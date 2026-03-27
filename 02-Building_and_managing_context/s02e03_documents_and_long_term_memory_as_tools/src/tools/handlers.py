from typing import Literal, Any
from pathlib import Path

from ..mcp.filesystem_client import MCPFileSystemClient
from ..clients.hub_client import AiDevsHubClient
from ..services.filesystem_service import (
    read_text_file,
    write_file,
    create_directory,
    list_directory,
    directory_tree,
)
from ..services.log_service import (
    download_logs,
    parse_logs,
    filter_by_event,
    filter_by_search,
    take_first_n_per_group,
    logs2text,
    number_of_tokens,
    EventType
)
from ..logger import logger


async def read_file(
    file_path: str, 
    filesystem_client: MCPFileSystemClient, 
) -> dict[str, str]:
    logger.tool('read_file', {'file_path': file_path})

    text_result = await read_text_file(file_path, filesystem_client)
    if not text_result['ok']:
        logger.error(
            'Text file read failed',
            f'path={file_path} result={text_result}'
        )
        return {
            'status': 'error',
            'path': file_path,
            'error': 'Failed to read file.',
            'hint': 'Check if the file exists.'
        }

    
    logger.success(f'File read successfully: {file_path}')
    return {
        'status': 'success',
        'path': file_path,
        'content': text_result['content']
    }

ManageMode = Literal['write_file', 'create_directory', 'list_directory', 'directory_tree']
async def manage_files(path: str, mode: ManageMode, content: str | None, filesystem_client: MCPFileSystemClient) -> dict[str, Any]:
    logger.tool('manage_files', {'path': path, 'mode': mode})

    if path in {'workspace', './workspace'}:
        logger.warn('The agent requested the workspace root directly; redirecting to the default allowed root for this filesystem client')

    if mode == 'write_file':
        if content is None:
            logger.error(
                'Content is empty',
                f'path={path} content={content}'
            )
            return {
                'status': 'error',
                'path': path,
                'mode': mode,
                'content': content,
                'error': 'Content is empty.',
                'hint': 'Provide the content to be saved to the file.',
            }
        parent_dir = Path(path).parent
        if str(parent_dir) not in {'', '.'}:
            dir_result = await create_directory(dir_path=str(parent_dir), filesystem_client=filesystem_client)
            if not dir_result['ok']:
                logger.error(
                    'Create parent directory failed',
                    f'path={path} parent_dir={parent_dir} result={dir_result}'
                )
                return {
                    'status': 'error',
                    'path': path,
                    'mode': mode,
                    'error': 'Failed to create parent directory for file.'
                }
        result = await write_file(file_path=path, content=content, filesystem_client=filesystem_client)

    elif mode == 'create_directory':
        target_path = Path(path)
        current_path = Path()
        result = {'ok': True, 'content': None}

        for part in target_path.parts:
            current_path = current_path / part
            result = await create_directory(dir_path=str(current_path), filesystem_client=filesystem_client)
            if not result['ok']:
                break

    elif mode == 'list_directory':
        result = await list_directory(dir_path=path, filesystem_client=filesystem_client)

    elif mode == 'directory_tree':
        result = await directory_tree(dir_path=path, filesystem_client=filesystem_client)

    else:
        logger.error(
            'Incorrect mode',
            f'The mode passed by the agent is not supported, mode: {mode}'
        )
        return {
            'status': 'error',
            'path': path,
            'mode': mode,
            'error': 'Incorrect mode.',
            'hint': 'Choose the correct mode and rerun the tool.',
        }

    if not result['ok']:
        logger.error(
            'Manage file failed',
            f'path={path} result={result} mode={mode}'
        )
        return {
            'status': 'error',
            'path': path,
            'mode': mode,
            'error': 'Failed to manage file.'
        }

    return {
        'status': 'success',
        'path': path,
        'mode': mode,
        'content': result['content']
    }

async def fetch_logs(hub_client: AiDevsHubClient) -> dict[str, str]:
    logs_path = await download_logs(hub_client)
    return {
        'status': 'success',
        'path': logs_path
    }

async def search_logs(
    path: str,
    filesystem_client: MCPFileSystemClient,
    event: list[EventType] | None = None,
    search: list[str] | None = None,
    first_n_per_group: int | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    logger.tool(
        'search_logs',
        {
            'path': path,
            'event': event,
            'search': search,
            'first_n_per_group': first_n_per_group,
            'limit': limit,
        }
    )

    if event is not None and 'INFO' in event and len(event) > 2:
        logger.warn('Broad search requested with INFO included early; this may reduce signal quality')
    if search is not None and len(search) > 4:
        logger.warn('Broad keyword search requested; prefer smaller iterative search batches')

    text_result = await read_text_file(path, filesystem_client)
    if not text_result['ok']:
        logger.error(
            'Log file read failed',
            f'path={path} result={text_result}'
        )
        return {
            'status': 'error',
            'path': path,
            'error': 'Failed to read log file.',
            'hint': 'Check if the log file exists.',
        }

    logs = parse_logs(text_result['content'])

    if event:
        logs = filter_by_event(logs, event)

    if search:
        logs = filter_by_search(logs, search)

    if first_n_per_group:
        logs = take_first_n_per_group(logs, first_n_per_group)

    effective_limit = 50 if limit is None else min(limit, 50)
    logs = logs[:effective_limit]

    logger.success(f'Log search completed: path={path} matches={len(logs)}')
    return {
        'status': 'success',
        'path': path,
        'number_of_logs': len(logs),
        'logs': logs2text(logs),
    }

async def count_tokens(logs_path: str, filesystem_client: MCPFileSystemClient, model: str) -> dict[str, str]:
    text_result = await read_text_file(logs_path, filesystem_client)
    if not text_result['ok']:
        logger.error(
            'Log file read failed',
            f'path={logs_path} result={text_result}'
        )
        return {
            'status': 'error',
            'path': logs_path,
            'error': 'Failed to read log file.',
            'hint': 'Check if the log file exists.',
        }

    logs = text_result['content']
    n_tokens = number_of_tokens(logs, model)
    return {
        'status': 'success',
        'path': logs_path,
        'number_of_logs': len(logs.splitlines()),
        'number_of_tokens': n_tokens
    }

async def send_logs(
    logs_path: str,
    filesystem_client: MCPFileSystemClient,
    hub_client: AiDevsHubClient
) -> dict[str, Any]:
    text_result = await read_text_file(logs_path, filesystem_client)
    if not text_result['ok']:
        logger.error(
            'Log file read failed',
            f'path={logs_path} result={text_result}'
        )
        return {
            'status': 'error',
            'path': logs_path,
            'error': 'Failed to read log file.',
            'hint': 'Check if the log file exists.',
        }

    logs = text_result['content']

    logger.tool('send_logs', {'lines': len(logs.splitlines())})
    result = await hub_client.send_logs(logs)
    logger.success('Logs sent to hub')
    return {
        'status': 'success',
        'result': result
    }
