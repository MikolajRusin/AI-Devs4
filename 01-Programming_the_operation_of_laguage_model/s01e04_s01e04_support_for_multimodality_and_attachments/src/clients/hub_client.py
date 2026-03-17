from ..utils.logger import logger

from pathlib import Path
from typing import Any
import httpx
import json


class AiDevsHubClient:
    def __init__(self, api_key: str, base_url: str, data_dir: str | Path):
        self.api_key = api_key
        self.base_url = base_url
        self.data_dir_path = Path(data_dir)
        self.downloads_dir_path = self.data_dir_path / 'downloaded_data'
        self.downloads_dir_path.mkdir(parents=True, exist_ok=True)

    @staticmethod
    async def _get(url: str) -> httpx.Response:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(url)
            response.raise_for_status()
        return response

    @staticmethod
    async def _post(url: str, payload: dict) -> httpx.Response:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(url, json=payload)
            logger.info(f'AiDevs Response {response.json()}')
            # response.raise_for_status()
        return response

    async def download_data(self, doc_name: str) -> str:
        url = f'{self.base_url}/dane/doc/{doc_name}'
        response = await self._get(url)

        dest_path = self.downloads_dir_path / doc_name
        if dest_path.suffix == '.md':
            dest_path.write_text(response.text, encoding='utf-8')
        else:
            dest_path.write_bytes(response.content)

        return str(dest_path)

    async def verify_answer(self, task_name: str, declaration: str) -> dict[str, Any]:
        url = 'https://hub.ag3nts.org/verify'
        payload = {
            'apikey': self.api_key,
            'task': task_name,
            'answer': {
                'declaration': declaration
            }
        }
        response = await self._post(url, payload)
        return response.json()