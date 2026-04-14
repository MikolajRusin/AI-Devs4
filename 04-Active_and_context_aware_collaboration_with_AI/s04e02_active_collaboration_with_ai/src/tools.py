"""
Agent tools for the windpower task.

Design
──────
Everything time-sensitive now runs in ONE async session (run_session).
The agent only needs to call two tools:

  1. run_windpower_session()
     Starts the 40-second window, fetches documentation + sensor data,
     calls the analysis subagent in a thread, signs all config points,
     submits the schedule, and calls done — all atomically.
     Returns {'suggested_configs', 'config', 'done'}.

  2. windpower_api(action, ...)
     Raw passthrough for help — outside the timer.  Optional first step.
"""

from dataclasses import dataclass
from typing import Any, Callable

from .api_client import run_session
from .analysis_agent import analyze_weather_subagent


@dataclass
class Tool:
    definition: dict
    handler: Callable[..., Any]


def find_tool(name: str, tools: list[Tool]) -> Callable | None:
    for t in tools:
        if t.definition.get('name') == name:
            return t.handler
    return None


def make_tools() -> list[Tool]:

    # ── 1. Full session: fetch → analyze → sign → submit → done ─────────────

    def tool_run_windpower_session() -> dict:
        print('[tool] run_windpower_session — starting...')
        result = run_session(analyze_weather_subagent)
        print(f'[tool] run_windpower_session → done={result.get("done")}')
        return result

    # ── Tool definitions ─────────────────────────────────────────────────────

    return [
        Tool(
            definition={
                'type': 'function',
                'name': 'run_windpower_session',
                'description': (
                    'Runs the complete windpower workflow in one atomic session: '
                    'fetches documentation and sensor data, analyses the forecast '
                    'via a dedicated subagent, signs every config point, submits '
                    'the schedule, and calls done — all within the 40-second window. '
                    'Returns {"suggested_configs": [...], "config": ..., "done": ...}. '
                    'The flag is in done.message. '
                    'If done.code is -805 or negative (window expired), call this tool again.'
                ),
                'parameters': {
                    'type': 'object',
                    'properties': {},
                    'required': [],
                },
            },
            handler=tool_run_windpower_session,
        ),
    ]
