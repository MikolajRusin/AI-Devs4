import requests

from .config import AI_DEVS_HUB_API_KEY, AI_DEVS_HUB_BASE_URL

TASK = 'foodwarehouse'


class HubClient:
    def __init__(self):
        self._url = f'{AI_DEVS_HUB_BASE_URL}/verify'
        self._key = AI_DEVS_HUB_API_KEY

    def _call(self, **answer_kwargs) -> dict:
        payload = {
            'apikey': self._key,
            'task': TASK,
            'answer': answer_kwargs,
        }
        resp = requests.post(self._url, json=payload, timeout=30)
        try:
            return resp.json()
        except Exception:
            return {'status': 'error', 'error': resp.text}

    def query_database(self, query: str) -> dict:
        return self._call(tool='database', query=query)

    def generate_signature(self, login: str, birthday: str, destination: int) -> dict:
        return self._call(
            tool='signatureGenerator',
            action='generate',
            login=login,
            birthday=birthday,
            destination=destination,
        )

    def create_order(self, title: str, creator_id: int, destination: int, signature: str) -> dict:
        return self._call(
            tool='orders',
            action='create',
            title=title,
            creatorID=creator_id,
            destination=destination,
            signature=signature,
        )

    def append_items(self, order_id: str, items: dict) -> dict:
        return self._call(tool='orders', action='append', id=order_id, items=items)

    def get_orders(self) -> dict:
        return self._call(tool='orders', action='get')

    def done(self) -> dict:
        return self._call(tool='done')

    def reset(self) -> dict:
        return self._call(tool='reset')
