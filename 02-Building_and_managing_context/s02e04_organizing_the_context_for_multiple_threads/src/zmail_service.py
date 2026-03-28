from typing import Any

from .hub_client import AiDevsHubClient
from .logger import logger


async def get_inbox(hub_client: AiDevsHubClient, page: int = 1) -> dict[str, Any]:
    logger.service('get_inbox', {'page': page})
    result = await hub_client.zmail_api(action='getInbox', page=page)
    logger.success(f'get_inbox successfully.')
    return result

async def search_inbox(hub_client: AiDevsHubClient, query: str, page: int = 1) -> dict[str, Any]:
    logger.service('search_inbox', {'query': query, 'page': page})
    result = await hub_client.zmail_api(action='search', page=page, query=query)  
    logger.success(f'search_inbox successfully.')
    return result 

async def get_thread(hub_client: AiDevsHubClient, thread_id: int) -> dict[str, Any]:
    logger.service('get_thread', {'thread_id': thread_id})
    result = await hub_client.zmail_api(action='getThread', thread_id=thread_id)
    logger.success(f'get_thread successfully.')
    return result 

async def get_messages(hub_client: AiDevsHubClient, row_ids: list[int]) -> dict[str, Any]:
    logger.service('get_messages', {'row_ids': row_ids})
    result = await hub_client.zmail_api(action='getMessages', row_ids=row_ids)
    logger.success(f'get_messages successfully.')
    return result 