"""
Agent tools for the Domatowo rescue mission.

4 tools total — grouped by purpose so the model picks behaviour via params:

  get_info      — read-only queries (map, objects, logs, expenses, symbol search)
  create_unit   — spawn a transporter (with scouts aboard) or a lone scout
  unit_action   — move / inspect / dismount an existing unit
  call_helicopter — final evacuation call (only works after a scout confirms a human)
"""

from dataclasses import dataclass
from typing import Any, Callable

from .hub_client import HubClient

_client = HubClient()


@dataclass
class Tool:
    definition: dict
    handler: Callable[..., Any]


def find_tool(name: str, tools: list[Tool]) -> Callable | None:
    for t in tools:
        if t.definition["name"] == name:
            return t.handler
    return None


def make_tools() -> list[Tool]:

    # ── 1. get_info ──────────────────────────────────────────────────────────

    def tool_get_info(type: str, symbol: str | None = None, symbols: list[str] | None = None) -> dict:
        if type == "map":
            return _client.get_map(symbols=symbols)
        if type == "symbol":
            return _client.search_symbol(symbol=symbol)
        if type == "objects":
            return _client.get_objects()
        if type == "logs":
            return _client.get_logs()
        if type == "expenses":
            return _client.get_expenses()
        return {"error": f"Unknown type: {type}"}

    # ── 2. create_unit ───────────────────────────────────────────────────────

    def tool_create_unit(type: str, passengers: int | None = None) -> dict:
        return _client.create_unit(type=type, passengers=passengers)

    # ── 3. unit_action ───────────────────────────────────────────────────────

    def tool_unit_action(action: str, object_hash: str, where: str | None = None, passengers: int | None = None) -> dict:
        if action == "move":
            return _client.move(object_hash=object_hash, where=where)
        if action == "inspect":
            return _client.inspect(object_hash=object_hash)
        if action == "dismount":
            return _client.dismount(object_hash=object_hash, passengers=passengers)
        return {"error": f"Unknown action: {action}"}

    # ── 4. call_helicopter ───────────────────────────────────────────────────

    def tool_call_helicopter(destination: str) -> dict:
        return _client.call_helicopter(destination=destination)

    # ── 5. reset ─────────────────────────────────────────────────────────────

    def tool_reset() -> dict:
        return _client.reset()

    # ── Definitions ──────────────────────────────────────────────────────────

    return [
        Tool(
            definition={
                "type": "function",
                "name": "get_info",
                "description": (
                    "Read-only queries against the game state. "
                    "type='map' returns the full 11x11 grid (pass 'symbols' list to filter). "
                    "type='symbol' returns all coordinates matching a 2-char symbol (requires 'symbol' param, e.g. 'B3'). "
                    "type='objects' returns all units with their hash, type and position. "
                    "type='logs' returns all inspect log entries. "
                    "type='expenses' returns the action-point spending history."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "enum": ["map", "symbol", "objects", "logs", "expenses"],
                            "description": "Which information to retrieve.",
                        },
                        "symbol": {
                            "type": "string",
                            "description": "2-char symbol to search for. Required when type='symbol' (e.g. 'B3').",
                        },
                        "symbols": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional filter for type='map'. Only tiles matching these symbols are returned.",
                        },
                    },
                    "required": ["type"],
                },
            },
            handler=tool_get_info,
        ),
        Tool(
            definition={
                "type": "function",
                "name": "create_unit",
                "description": (
                    "Spawn a new unit at the next free slot on row 6 (A6→D6). "
                    "type='transporter' creates a vehicle that moves cheaply on roads (1 pt/field) "
                    "and can carry scouts — requires 'passengers' (1-4). "
                    "type='scout' creates a lone scout that can walk any tile (7 pt/field)."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "enum": ["transporter", "scout"],
                            "description": "Unit type to create.",
                        },
                        "passengers": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 4,
                            "description": "Number of scouts aboard. Required when type='transporter'.",
                        },
                    },
                    "required": ["type"],
                },
            },
            handler=tool_create_unit,
        ),
        Tool(
            definition={
                "type": "function",
                "name": "unit_action",
                "description": (
                    "Perform an action on an existing unit identified by its hash. "
                    "action='move': move the unit to a destination coordinate (e.g. 'F1'). "
                    "  Transporters follow roads only; scouts take the shortest orthogonal path. "
                    "action='inspect': scout checks its current tile for the partisan (costs 1 pt). "
                    "action='dismount': drop scouts from a transporter onto surrounding tiles (free). "
                    "  Requires 'passengers' — how many scouts to unload."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["move", "inspect", "dismount"],
                            "description": "Action to perform.",
                        },
                        "object_hash": {
                            "type": "string",
                            "description": "Hash identifier of the unit (from get_info type='objects').",
                        },
                        "where": {
                            "type": "string",
                            "description": "Target coordinate for action='move', e.g. 'F1', 'D9'.",
                        },
                        "passengers": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 4,
                            "description": "Number of scouts to unload. Required for action='dismount'.",
                        },
                    },
                    "required": ["action", "object_hash"],
                },
            },
            handler=tool_unit_action,
        ),
        Tool(
            definition={
                "type": "function",
                "name": "call_helicopter",
                "description": (
                    "Call the evacuation helicopter to the given coordinate. "
                    "Only works after at least one scout has confirmed a human via inspect. "
                    "Pass the exact coordinate where the partisan was found."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "destination": {
                            "type": "string",
                            "description": "Coordinate where the partisan was found, e.g. 'F1'.",
                        },
                    },
                    "required": ["destination"],
                },
            },
            handler=tool_call_helicopter,
        ),
        Tool(
            definition={
                "type": "function",
                "name": "reset",
                "description": (
                    "Resets the board to a fresh state: clears all units, restores 300 action points, "
                    "and re-randomises the partisan position. Call this once at the very start of the mission."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
            handler=tool_reset,
        ),
    ]
