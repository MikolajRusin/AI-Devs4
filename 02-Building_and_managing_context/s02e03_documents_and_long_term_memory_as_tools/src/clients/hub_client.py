import httpx
from pathlib import Path

from ..logger import logger


class AiDevsHubClient:
    def __init__(self, api_key: str, base_url: str, workspace_dir_path: str):
        self.api_key = api_key
        self.base_url = base_url
        self.workspace_dir_path = Path(workspace_dir_path)

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
            # response.raise_for_status()
        return response

    async def download_logs(self) -> str:
        logger.start('Downloading failure logs from hub')
        url = f'{self.base_url}/data/{self.api_key}/failure.log'
        response = await self._get(url)

        logs_dir = self.workspace_dir_path / 'logs'
        logs_dir.mkdir(parents=True, exist_ok=True)
        dest_path = logs_dir / 'failure.log'

        dest_path.write_text(response.text)
        logger.success(f'Failure logs downloaded to {dest_path}')
        return str(dest_path)

    async def send_logs(self, logs: str) -> dict:
        logger.start(f'Sending condensed logs to hub lines={len(logs.splitlines())}')
        url = f'{self.base_url}/verify'
        payload = {
            'apikey': self.api_key,
            'task': 'failure',
            'answer': {
                'logs': logs
            }
        }
        response = await self._post(
            url=url,
            payload=payload
        )
        result = response.json()
        logger.success('Condensed logs sent to hub successfully')
        logger.response(f'Hub response | {result}')
        return result
