import asyncio
from typing import Any, Awaitable, Callable
from dataclasses import dataclass

from .hub_client import AiDevsHubClient
from .zmail_service import get_inbox, search_inbox, get_thread, get_messages
from .logger import logger


async def zmail__get_inbox(hub_client: AiDevsHubClient, page: int = 1) -> dict[str, Any]:
    logger.tool('zmail__get_inbox', {'page': page})
    result = await get_inbox(hub_client=hub_client, page=page)
    logger.success(f'zmail__get_inbox successfully.')
    return result

async def zmail__search_inbox(hub_client: AiDevsHubClient, query: str, page: int = 1) -> dict[str, Any]:
    logger.tool('zmail__search_inbox', {'query': query, 'page': page})
    result = await search_inbox(hub_client=hub_client, query=query, page=page)
    logger.success(f'zmail__search_inbox successfully.')
    return result

async def zmail__get_thread(hub_client: AiDevsHubClient, thread_id: int) -> dict[str, Any]:
    logger.tool('zmail__get_thread', {'thread_id': thread_id})
    result = await get_thread(hub_client=hub_client, thread_id=thread_id)
    logger.success(f'zmail__get_thread successfully.')
    return result

async def zmail__get_messages(hub_client: AiDevsHubClient, row_ids: list[int]) -> dict[str, Any]:
    logger.tool('zmail__get_messages', {'row_ids': row_ids})
    result = await get_messages(hub_client=hub_client, row_ids=row_ids)
    logger.success(f'zmail__get_messages successfully.')
    return result

async def hub__send_data(hub_client: AiDevsHubClient, password: str, date: str, confirmation_code: str) -> dict:
    logger.tool('hub__send_data', {'password': password, 'date': date, 'confirmation_code': confirmation_code})
    result = await hub_client.send_data(password=password, date=date, confirmation_code=confirmation_code)
    logger.success(f'hub__send_data successfully.')
    return result


async def wait_a_moment(hub_client: AiDevsHubClient, seconds: int) -> dict[str, Any]:
    del hub_client
    logger.tool('wait_a_moment', {'seconds': seconds})
    await asyncio.sleep(seconds)
    logger.success('wait_a_moment successfully.')
    return {'status': 'ok', 'waited_seconds': seconds}

@dataclass
class Tool:
    definition: dict
    handler: Callable[..., Awaitable[dict[str, Any]]]

tools: list[Tool] = [
    Tool(
        definition={
            'type': 'function',
            'name': 'zmail__get_inbox',
            'description': 'Load one page of inbox results from zmail.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'page': {
                        'type': 'integer',
                        'description': 'Inbox page number to load. Start with 1 and increase only when you need older messages.'
                    }
                },
                'required': ['page']
            }
        },
        handler=zmail__get_inbox
    ),
    Tool(
        definition={
            'type': 'function',
            'name': 'zmail__search_inbox',
            'description': 'Search inbox messages with Gmail-like query syntax. Supports plain words, quoted phrases, from:, to:, subject:, OR, AND.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'query': {
                        'type': 'string',
                        'description': 'Search query using Gmail-like operators, for example: from:gmail.com, subject:"security ticket", password, "confirmation code", OR, AND.'
                    },
                    'page': {
                        'type': 'integer',
                        'description': 'Search results page number. Start with 1 and request later pages only if needed.'
                    }
                },
                'required': ['query', 'page']
            }
        },
        handler=zmail__search_inbox
    ),
    Tool(
        definition={
            'type': 'function',
            'name': 'zmail__get_thread',
            'description': 'Load all message metadata from a specific thread. Use this after finding an interesting thread ID in inbox or search results.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'thread_id': {
                        'type': 'integer',
                        'description': 'Thread identifier returned by inbox or search results.'
                    }
                },
                'required': ['thread_id']
            }
        },
        handler=zmail__get_thread
    ),
    Tool(
        definition={
            'type': 'function',
            'name': 'zmail__get_messages',
            'description': 'Fetch the full content of one or more messages by row ID. Always use this before extracting facts from an email.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'row_ids': {
                        'type': 'array',
                        'description': 'List of message row IDs to fetch in full.',
                        'items': {
                            'type': 'integer',
                            'description': 'Message row ID returned by inbox, search, or thread results.'
                        }
                    }
                },
                'required': ['row_ids']
            }
        },
        handler=zmail__get_messages
    ),
    Tool(
        definition={
            'type': 'function',
            'name': 'hub__send_data',
            'description': 'Send the found answer to the hub. Use this only when you have a concrete candidate for all three fields and want feedback about which values are correct or still wrong.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'password': {
                        'type': 'string',
                        'description': 'Password for the employee system found in the mailbox. Send the exact value from the email without paraphrasing or reformatting.'
                    },
                    'date': {
                        'type': 'string',
                        'description': 'Planned attack date in exact YYYY-MM-DD format, for example 2026-02-28.'
                    },
                    'confirmation_code': {
                        'type': 'string',
                        'description': 'Security ticket confirmation code. It must start with SEC- and have exactly 36 characters in total.'
                    },
                },
                'required': ['password', 'date', 'confirmation_code']
            }
        },
        handler=hub__send_data
    ),
    Tool(
        definition={
            'type': 'function',
            'name': 'wait_a_moment',
            'description': 'Pause briefly before checking the mailbox again. Use this only after meaningful search attempts, when a relevant new message may arrive soon.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'seconds': {
                        'type': 'integer',
                        'description': 'Number of seconds to wait before continuing. Keep this short.'
                    }
                },
                'required': ['seconds']
            }
        },
        handler=wait_a_moment
    )
]

def find_tool(tool_name: str) -> Callable[..., Awaitable[dict[str, Any]]] | None:
    for tool in tools:
        if tool.definition.get('name') == tool_name:
            return tool.handler
    return None
