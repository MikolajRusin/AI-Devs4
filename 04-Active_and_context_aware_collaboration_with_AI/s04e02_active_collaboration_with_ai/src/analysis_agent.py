"""
LLM-driven subagent for planning the wind turbine schedule.

Python handles only transport-oriented concerns here:
  - building the prompt payload,
  - normalizing/parsing the returned JSON,
  - retrying if the model returns malformed data,
  - validating/correcting the final schedule before submission.

Weather reasoning and schedule decisions are delegated to the subagent.
"""

import json

from .chat_api import chat_completions


ANALYSIS_MODEL = 'gpt-4.1'


_SYSTEM = """
You are a wind turbine scheduling subagent for the windpower task.

You receive:
- official turbine documentation,
- turbine status,
- power plant status,
- the full weather forecast.

Your task is to decide the schedule.

Rules you must follow:
- Protect the turbine during every dangerous storm.
- A dangerous storm means wind above the turbine safety limit from documentation.
- During dangerous storms, use pitchAngle 90 and turbineMode "idle".
- The turbine returns to normal roughly one hour after a storm, so if another later storm appears,
  you must schedule protection again for that later storm too.
- Find the FIRST forecast moment when the turbine can generate at least the missing power required by the plant.
- If powerDeficitKw is a range like "4-5", use the upper bound.
- Use only allowed pitch angles from documentation.
- Use only turbineMode values "idle" and "production".
- Include both the protection configs and the production config in one response.
- Use only timestamps that exist exactly in the forecast. Do not invent hours.
- Forecast entries are spaced every 2 hours, so your chosen startHour must match one of those exact entries.
- Timestamps come as "YYYY-MM-DD HH:MM:SS". Return:
  - startDate as "YYYY-MM-DD"
  - startHour as "HH:00:00"
- Minutes and seconds must stay zero.

Before answering, perform this self-check:
1. Every dangerous storm in the forecast has a protection config.
2. The production config is the earliest valid one.
3. Every returned timestamp exists exactly in the forecast input.
3. Output is valid JSON and contains only the requested fields.

Return JSON only, with no markdown and no explanation:
{
  "configs": [
    {
      "startDate": "YYYY-MM-DD",
      "startHour": "HH:00:00",
      "windMs": 0,
      "pitchAngle": 0,
      "turbineMode": "idle"
    }
  ]
}
"""


def _normalize_configs(configs: list[dict]) -> list[dict]:
    normalized: list[dict] = []
    seen: set[tuple[str, str, int, str]] = set()

    for item in configs:
        try:
            cfg = {
                'startDate': str(item['startDate']),
                'startHour': str(item['startHour']),
                'windMs': float(item['windMs']),
                'pitchAngle': int(item['pitchAngle']),
                'turbineMode': str(item['turbineMode']),
            }
        except (KeyError, TypeError, ValueError):
            continue

        if cfg['pitchAngle'] not in {0, 45, 90}:
            continue
        if cfg['turbineMode'] not in {'idle', 'production'}:
            continue

        key = (cfg['startDate'], cfg['startHour'], cfg['pitchAngle'], cfg['turbineMode'])
        if key in seen:
            continue
        seen.add(key)
        normalized.append(cfg)

    return sorted(normalized, key=lambda c: (c['startDate'], c['startHour'], c['turbineMode']))


def _filter_to_forecast_slots(configs: list[dict], weather: dict) -> list[dict]:
    valid_slots = {
        (ts.split(' ')[0], ts.split(' ')[1])
        for ts in (entry.get('timestamp', '') for entry in weather.get('forecast', []))
        if ' ' in ts
    }
    return [
        cfg for cfg in configs
        if (cfg['startDate'], cfg['startHour']) in valid_slots
    ]


def _build_payload(weather: dict, powerplant: dict, turbine: dict, documentation: dict) -> str:
    payload = {
        'task_goal': (
            'Protect the turbine during all dangerous storms and find the earliest '
            'moment when it can generate enough missing power for the plant.'
        ),
        'documentation': documentation,
        'turbine_status': turbine,
        'powerplant_status': powerplant,
        'weather': weather,
    }
    return json.dumps(payload, ensure_ascii=False)


def _entry_yield_percent(entry: dict) -> float | None:
    raw = str(entry.get('yieldPercent', '')).strip()
    if not raw:
        return None
    if '-' in raw:
        left, right = raw.split('-', 1)
        try:
            return (float(left) + float(right)) / 2
        except ValueError:
            return None
    try:
        return float(raw)
    except ValueError:
        return None


def _storm_cutoff(documentation: dict) -> float:
    safety = documentation.get('safety', {})
    for key in ('cutoffWindMs', 'stormCutoffMs', 'dangerousWindMs', 'maxOperationalWindMs'):
        if key in safety:
            return float(safety[key])
    for entry in documentation.get('windPowerYieldPercent', []):
        if _entry_yield_percent(entry) is None:
            if 'windMs' in entry:
                return float(entry['windMs'])
            wind_range = str(entry.get('windMsRange', '')).replace('+', '').strip()
            try:
                return float(wind_range)
            except ValueError:
                continue
    return 14.0


def _min_operational_wind(documentation: dict) -> float:
    safety = documentation.get('safety', {})
    if 'minOperationalWindMs' in safety:
        return float(safety['minOperationalWindMs'])
    return 4.0


def _calc_output_kw(wind_ms: float, documentation: dict) -> float:
    table = documentation.get('windPowerYieldPercent', [])
    rated = float(documentation.get('ratedPowerKw', 14))
    points: list[tuple[float, float]] = []

    for entry in table:
        pct = _entry_yield_percent(entry)
        if pct is None:
            continue

        if 'windMs' in entry:
            try:
                points.append((float(entry['windMs']), pct))
            except (TypeError, ValueError):
                continue
            continue

        raw_range = str(entry.get('windMsRange', '')).strip()
        if not raw_range:
            continue
        if raw_range.endswith('+'):
            try:
                points.append((float(raw_range[:-1]), pct))
            except ValueError:
                continue
            continue
        if '-' in raw_range:
            left, right = raw_range.split('-', 1)
            try:
                points.append((float(left), pct))
                points.append((float(right), pct))
            except ValueError:
                continue

    if not points:
        return 0.0

    points.sort()
    if wind_ms < points[0][0]:
        return 0.0
    if wind_ms >= points[-1][0]:
        return (points[-1][1] / 100) * rated

    for (left_w, left_pct), (right_w, right_pct) in zip(points, points[1:]):
        if left_w <= wind_ms <= right_w:
            if right_w == left_w:
                pct = max(left_pct, right_pct)
            else:
                ratio = (wind_ms - left_w) / (right_w - left_w)
                pct = left_pct + (right_pct - left_pct) * ratio
            return (pct / 100) * rated

    return 0.0


def _required_kw(powerplant: dict) -> float:
    raw = powerplant.get('powerDeficitKw')
    if raw is None:
        return 5.0
    text = str(raw)
    if '-' in text:
        try:
            return float(text.split('-')[-1])
        except ValueError:
            return 5.0
    try:
        value = float(text)
    except ValueError:
        return 5.0
    return value if value > 0 else 5.0


def _pitch_factors(documentation: dict) -> dict[int, float]:
    factors: dict[int, float] = {}
    for entry in documentation.get('pitchAngleYieldPercent', []):
        try:
            factors[int(entry['pitchAngleDeg'])] = float(entry['yieldPercent']) / 100.0
        except (KeyError, TypeError, ValueError):
            continue
    return factors or {0: 1.0, 45: 0.65, 90: 0.0}


def _split_ts(ts: str) -> tuple[str, str]:
    date, hour, *_ = ts.split(' ')
    return date, hour


def _storm_configs(weather: dict, documentation: dict) -> list[dict]:
    cutoff = _storm_cutoff(documentation)
    result: list[dict] = []
    for entry in weather.get('forecast', []):
        wind = float(entry.get('windMs', 0))
        if wind >= cutoff:
            start_date, start_hour = _split_ts(entry['timestamp'])
            result.append({
                'startDate': start_date,
                'startHour': start_hour,
                'windMs': wind,
                'pitchAngle': 90,
                'turbineMode': 'idle',
            })
    return result


def _first_production_config(weather: dict, powerplant: dict, documentation: dict) -> dict | None:
    required_kw = _required_kw(powerplant)
    min_wind = _min_operational_wind(documentation)
    cutoff = _storm_cutoff(documentation)
    pitch_factors = _pitch_factors(documentation)
    ordered_angles = sorted(pitch_factors, key=lambda angle: pitch_factors[angle], reverse=True)

    for entry in weather.get('forecast', []):
        wind = float(entry.get('windMs', 0))
        if wind >= cutoff or wind < min_wind:
            continue
        base_output = _calc_output_kw(wind, documentation)
        if base_output <= 0:
            continue
        for angle in ordered_angles:
            produced = round(base_output * pitch_factors[angle], 2)
            if produced >= required_kw:
                start_date, start_hour = _split_ts(entry['timestamp'])
                return {
                    'startDate': start_date,
                    'startHour': start_hour,
                    'windMs': wind,
                    'pitchAngle': angle,
                    'turbineMode': 'production',
                }
    return None


def _validated_schedule(
    proposed: list[dict],
    weather: dict,
    powerplant: dict,
    documentation: dict,
) -> list[dict]:
    by_slot: dict[tuple[str, str], dict] = {
        (cfg['startDate'], cfg['startHour']): cfg for cfg in proposed
    }

    for cfg in _storm_configs(weather, documentation):
        by_slot[(cfg['startDate'], cfg['startHour'])] = cfg

    production = _first_production_config(weather, powerplant, documentation)
    if production is not None:
        by_slot[(production['startDate'], production['startHour'])] = production

    return sorted(by_slot.values(), key=lambda c: (c['startDate'], c['startHour']))


def analyze_weather_subagent(
    weather: dict,
    powerplant: dict,
    turbine: dict,
    documentation: dict,
) -> list[dict]:
    if not weather.get('forecast') or 'powerDeficitKw' not in powerplant:
        print('[analysis_agent] missing critical input for subagent')
        return []

    user_prompt = _build_payload(weather, powerplant, turbine, documentation)

    for attempt in range(1, 4):
        print(f'[analysis_agent] subagent attempt {attempt}/3')
        raw = chat_completions(
            model=ANALYSIS_MODEL,
            system=_SYSTEM,
            user=user_prompt,
            response_format={'type': 'json_object'},
        )
        print(f'[analysis_agent] subagent raw: {raw[:600]}')

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            continue

        proposed = _filter_to_forecast_slots(
            _normalize_configs(parsed.get('configs', [])),
            weather,
        )
        configs = _validated_schedule(
            proposed=proposed,
            weather=weather,
            powerplant=powerplant,
            documentation=documentation,
        )
        if configs:
            print(f'[analysis_agent] proposed {len(proposed)} config(s), validated to {len(configs)}:')
            for cfg in configs:
                print(f'  {cfg}')
            return configs

    print('[analysis_agent] subagent failed to return usable configs')
    return []
