"""
HubClient — thin wrapper around the Domatowo API.
Each method maps 1:1 to an API action and returns the raw response dict.
"""

import requests
from .config import AI_DEVS_HUB_API_KEY, AI_DEVS_HUB_BASE_URL

TASK = "domatowo"


class HubClient:
    def __init__(self):
        self._url = f"{AI_DEVS_HUB_BASE_URL}/verify"
        self._key = AI_DEVS_HUB_API_KEY

    def _call(self, action: str, **kwargs) -> dict:
        payload = {
            "apikey": self._key,
            "task": TASK,
            "answer": {"action": action, **kwargs},
        }
        resp = requests.post(self._url, json=payload, timeout=30)
        if not resp.ok:
            try:
                return {"status": "error", "error": resp.json()}
            except Exception:
                return {"status": "error", "error": resp.text}
        return resp.json()

    # ── Info (free) ──────────────────────────────────────────────

    def get_map(self, symbols: list[str] | None = None) -> dict:
        kwargs = {}
        if symbols:
            kwargs["symbols"] = symbols
        return self._call("getMap", **kwargs)

    def search_symbol(self, symbol: str) -> dict:
        return self._call("searchSymbol", symbol=symbol)

    def get_objects(self) -> dict:
        return self._call("getObjects")

    def get_logs(self) -> dict:
        return self._call("getLogs")

    def get_expenses(self) -> dict:
        return self._call("expenses")

    def get_action_cost(self) -> dict:
        return self._call("actionCost")

    # ── Unit management ──────────────────────────────────────────

    def create_unit(self, type: str, passengers: int | None = None) -> dict:
        """Create a unit. type='transporter' requires passengers (1-4). type='scout' is standalone."""
        kwargs: dict = {"type": type}
        if passengers is not None:
            kwargs["passengers"] = passengers
        return self._call("create", **kwargs)

    def move(self, object_hash: str, where: str) -> dict:
        return self._call("move", object=object_hash, where=where)

    def dismount(self, object_hash: str, passengers: int) -> dict:
        return self._call("dismount", object=object_hash, passengers=passengers)

    def inspect(self, object_hash: str) -> dict:
        return self._call("inspect", object=object_hash)

    # ── Finale ───────────────────────────────────────────────────

    def call_helicopter(self, destination: str) -> dict:
        return self._call("callHelicopter", destination=destination)

    def reset(self) -> dict:
        return self._call("reset")
