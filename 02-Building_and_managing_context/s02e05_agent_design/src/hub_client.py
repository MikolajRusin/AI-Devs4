import httpx
from typing import Any

from .logger import logger

class AiDevsHubClient:
    def __init__(self, api_key: str, base_url: str):
        self.api_key=api_key
        self.base_url=base_url

    async def _post(self, url: str, payload: dict[str, Any]) -> httpx.Response:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(url, json=payload)
        return response

    async def send_instructions(self, task: str, instructions: list[str]) -> dict:
        logger.api('AIDevsHub', 'Sending request with instructions')

        url = f'{self.base_url}/verify'
        payload = {
            'apikey': self.api_key,
            'task': task,
            'answer': {
                'instructions': instructions
            }
        }

        response = await self._post(url, payload)
        result = response.json()
        logger.success('Received response')
        logger.response(f'AIDevsHub response | {result}') 
        return result