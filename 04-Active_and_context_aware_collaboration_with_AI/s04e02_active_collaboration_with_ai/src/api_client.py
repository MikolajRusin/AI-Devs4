"""
Async helpers for the windpower API.
All public functions return plain dicts so tool handlers can return them directly.

Key design
──────────
Everything that counts against the 40-second service window now happens inside
ONE asyncio.run() call — `run_session`.  The LLM analysis step is dispatched
to a thread executor so the event loop stays alive during the HTTP polling.

           ┌─────────────────────────── one asyncio.run ──────────────────────────────┐
  start → docs → queue sensors → collect sensors → [LLM analysis in thread] →
  queue unlock codes → collect codes → submit config → done
           └──────────────────────────────────────────────────────────────────────────┘
"""

import asyncio
import json
import httpx
from concurrent.futures import ThreadPoolExecutor
from typing import Callable

from .config import AI_DEVS_HUB_API_KEY, VERIFY_URL, TASK


# ──────────────────────────────────────────────────────────────
# Low-level async helpers
# ──────────────────────────────────────────────────────────────

async def _call(client: httpx.AsyncClient, action: str, **kwargs) -> dict:
    payload = {
        'apikey': AI_DEVS_HUB_API_KEY,
        'task': TASK,
        'answer': {'action': action, **kwargs},
    }
    resp = await client.post(VERIFY_URL, json=payload)
    return resp.json()


async def _collect_n(
    client: httpx.AsyncClient,
    n: int,
    timeout: float,
    expected_source: str | None = None,
) -> list[dict]:
    """Poll getResult until n matching results are available."""
    results: list[dict] = []
    deadline = asyncio.get_event_loop().time() + timeout
    while len(results) < n:
        if asyncio.get_event_loop().time() > deadline:
            print(f'[api] collect_n timeout — got {len(results)}/{n}')
            break
        r = await _call(client, 'getResult')
        source = r.get('sourceFunction')
        if source and (expected_source is None or source == expected_source):
            results.append(r)
            print(f'  [queue] {source} ({len(results)}/{n})')
        else:
            await asyncio.sleep(0.25)
    return results


async def _collect_sources(
    client: httpx.AsyncClient,
    required_sources: set[str],
    timeout: float,
) -> dict[str, dict]:
    """Collect queued results until all required sources are present or time runs out."""
    results: dict[str, dict] = {}
    deadline = asyncio.get_event_loop().time() + timeout
    while asyncio.get_event_loop().time() <= deadline:
        r = await _call(client, 'getResult')
        source = r.get('sourceFunction')
        if source:
            results[source] = r
            print(f'  [queue] {source} ({len(results)}/{len(required_sources)})')
            if required_sources.issubset(results.keys()):
                break
            continue
        await asyncio.sleep(0.25)

    if not required_sources.issubset(results.keys()):
        missing = sorted(required_sources - set(results.keys()))
        print(f'[api] collect_sources timeout — missing: {missing}')
    return results


# ──────────────────────────────────────────────────────────────
# Public helpers used by tools
# ──────────────────────────────────────────────────────────────

def sync_api_call(action: str, **kwargs) -> dict:
    """One-shot synchronous API call (outside the service window)."""
    async def _run():
        async with httpx.AsyncClient(timeout=30) as client:
            return await _call(client, action, **kwargs)
    return asyncio.run(_run())


def run_session(analysis_fn: Callable[[dict, dict, dict, dict], list[dict]]) -> dict:
    """
    Execute the entire windpower workflow inside a single 40-second session:

      1. start  — open service window
      2. get documentation  — direct response
      3. get weather / turbinecheck / powerplantcheck  — queued, parallel
      4. collect sensor results (up to 25 s)
      5. run analysis_fn(weather, powerplant, turbine, docs) in a thread
         so the event loop keeps polling if needed
      6. queue unlockCodeGenerator for every config (parallel)
      7. collect unlock codes (up to 10 s)
      8. submit config
      9. done

    Returns {'suggested_configs': [...], 'config': ..., 'done': ...}
    """
    async def _run():
        async with httpx.AsyncClient(timeout=60) as client:
            # ── 1 & 2: open session + fetch docs ──────────────────────────────
            session = await _call(client, 'start')
            print(f'[session] started: {session}')
            docs = await _call(client, 'get', param='documentation')
            print(f'[session] docs: ratedPowerKw={docs.get("ratedPowerKw")}')

            # ── 3: queue sensor calls in parallel ─────────────────────────────
            await asyncio.gather(
                _call(client, 'get', param='weather'),
                _call(client, 'get', param='turbinecheck'),
                _call(client, 'get', param='powerplantcheck'),
            )

            # ── 4: collect sensor results ──────────────────────────────────────
            sensor = await _collect_sources(
                client,
                required_sources={'weather', 'powerplantcheck'},
                timeout=37,
            )
            weather = sensor.get('weather', {})
            powerplant = sensor.get('powerplantcheck', {})
            turbine = sensor.get('turbinecheck', {})

            if not weather.get('forecast'):
                print('[session] WARNING: weather forecast missing — session may be stale')
            if 'powerDeficitKw' not in powerplant:
                print('[session] WARNING: powerplant data missing — session may be stale')

            # ── 5: LLM analysis in thread (keeps event loop alive) ─────────────
            loop = asyncio.get_event_loop()
            executor = ThreadPoolExecutor(max_workers=1)
            configs: list[dict] = await loop.run_in_executor(
                executor, analysis_fn, weather, powerplant, turbine, docs
            )
            print(f'[session] analysis returned {len(configs)} config(s)')

            if not configs:
                return {
                    'suggested_configs': [],
                    'config': {'code': -1, 'message': 'No configs from analysis'},
                    'done': {'code': -1, 'message': 'No configs from analysis'},
                }

            # ── 6: queue unlock codes in parallel ─────────────────────────────
            await asyncio.gather(*[
                _call(
                    client, 'unlockCodeGenerator',
                    startDate=c['startDate'],
                    startHour=c['startHour'],
                    windMs=c['windMs'],
                    pitchAngle=c['pitchAngle'],
                )
                for c in configs
            ])

            # ── 7: collect unlock codes ────────────────────────────────────────
            unlock_raw = await _collect_n(
                client,
                len(configs),
                timeout=15,
                expected_source='unlockCodeGenerator',
            )
            for r in unlock_raw:
                print(f'  [sign raw] {json.dumps(r, ensure_ascii=False)}')

            code_by_date_hour: dict[tuple, str] = {}
            code_by_wind_pitch: dict[tuple, str] = {}
            for r in unlock_raw:
                code = r.get('unlockCode', '')
                sp = r.get('signedParams', {})
                date = sp.get('startDate', r.get('startDate', ''))
                hour = sp.get('startHour', r.get('startHour', ''))
                wind = sp.get('windMs', r.get('windMs'))
                pitch = sp.get('pitchAngle', r.get('pitchAngle'))
                if date and hour:
                    code_by_date_hour[(date, hour)] = code
                if wind is not None and pitch is not None:
                    code_by_wind_pitch[(str(wind), str(pitch))] = code

            signed: list[dict] = []
            for i, c in enumerate(configs):
                unlock_code = (
                    code_by_date_hour.get((c['startDate'], c['startHour']), '')
                    or code_by_wind_pitch.get((str(float(c['windMs'])), str(float(c['pitchAngle']))), '')
                    or (unlock_raw[i].get('unlockCode', '') if i < len(unlock_raw) else '')
                )
                signed.append({**c, 'unlockCode': unlock_code})
                print(f'  [signed] {c["startDate"]} {c["startHour"]} → {unlock_code}')

            # ── 8: submit config ───────────────────────────────────────────────
            batch = {
                f"{c['startDate']} {c['startHour']}": {
                    'pitchAngle': c['pitchAngle'],
                    'turbineMode': c['turbineMode'],
                    'unlockCode': c['unlockCode'],
                }
                for c in signed
            }
            print(f'[session] submitting {len(batch)} config points')
            config_resp = await _call(client, 'config', configs=batch)
            print(f'  config response: {config_resp}')

            # ── 9: done ────────────────────────────────────────────────────────
            done_resp = await _call(client, 'done')
            print(f'  done response: {done_resp}')

            return {
                'suggested_configs': configs,
                'config': config_resp,
                'done': done_resp,
            }

    return asyncio.run(_run())
