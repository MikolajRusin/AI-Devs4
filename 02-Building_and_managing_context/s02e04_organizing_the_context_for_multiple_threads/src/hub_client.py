import httpx
from typing import Literal, Any

from .logger import logger

ActionType = Literal['getInbox', 'getThread', 'getMessages', 'search']

class AiDevsHubClient:
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url

    async def _post(self, url: str, payload: dict[str, Any]) -> httpx.Response:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(url, json=payload)
            # response.raise_for_status()
        return response
    
    async def zmail_api(
        self, 
        action: str, 
        page: int = 1,  
        thread_id: int | None = None, 
        row_ids: list[int] | None = None, 
        query: str | None = None
    ) -> dict:
        logger.api('ZMAIL', f'Sending request with action: {action}')

        url = f'{self.base_url}/api/zmail'
        payload = {
            'apikey': self.api_key
        }

        per_page = 5
        if action == 'getInbox':
            payload['action'] = 'getInbox'
            payload['page'] = page
            payload['perPage'] = per_page

        elif action == 'getThread':
            payload['action'] = 'getThread'
            payload['threadID'] = thread_id

        elif action == 'getMessages':
            payload['action'] = 'getMessages'
            payload['ids'] = row_ids

        elif action == 'search':
            payload['action'] = 'search'
            payload['query'] = query
            payload['page'] = page
            payload['perPage'] = per_page

        response = await self._post(url, payload)
        result = response.json()
        logger.success('Received response')
        logger.response(f'Zmail response | {result}')        
        return result

    async def send_data(self, password: str, date: str, confirmation_code: str) -> dict:
        logger.api('AIDevsHub', f'Sending request with action')

        url = f'{self.base_url}/verify'
        payload = {
            'apikey': self.api_key,
            'task': 'mailbox',
            'answer': {
                'password': password,
                'date': date,
                'confirmation_code': confirmation_code
            }
        }

        response = await self._post(url, payload)
        result = response.json()
        logger.success('Received response')
        logger.response(f'AIDevsHub response | {result}') 
        return result