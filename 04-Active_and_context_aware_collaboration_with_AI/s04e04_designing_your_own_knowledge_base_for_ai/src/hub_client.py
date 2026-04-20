"""HubClient — wrapper around the /verify/ task API."""

import requests
from .config import AI_DEVS_HUB_API_KEY, AI_DEVS_HUB_BASE_URL


class HubClient:
    def __init__(self, task_name: str = "filesystem"):
        self._url = f"{AI_DEVS_HUB_BASE_URL}/verify"
        self._key = AI_DEVS_HUB_API_KEY
        self._task_name = task_name

    def _call(self, action: str, **kwargs) -> dict:
        payload = {
            "apikey": self._key,
            "task": self._task_name,
            "answer": {"action": action, **kwargs},
        }
        resp = requests.post(self._url, json=payload, timeout=30)
        if not resp.ok:
            try:
                return {"status": "error", "error": resp.json()}
            except Exception:
                return {"status": "error", "error": resp.text}
        return resp.json()

    def help(self) -> dict:
        return self._call("help")

    def reset(self) -> dict:
        return self._call("reset")

    def done(self) -> dict:
        return self._call("done")

    def list_dir(self, path: str) -> dict:
        return self._call("listFiles", path=path)

    def create_dir(self, path: str) -> dict:
        return self._call("createDirectory", path=path)

    def create_file(self, path: str, content: str) -> dict:
        return self._call("createFile", path=path, content=content)

    def delete_file(self, path: str) -> dict:
        return self._call("deleteFile", path=path)

    def batch(self, operations: list[dict]) -> dict:
        """Send multiple filesystem operations in a single request."""
        payload = {
            "apikey": self._key,
            "task": self._task_name,
            "answer": operations,
        }
        resp = requests.post(self._url, json=payload, timeout=60)
        if not resp.ok:
            try:
                return {"status": "error", "error": resp.json()}
            except Exception:
                return {"status": "error", "error": resp.text}
        return resp.json()
