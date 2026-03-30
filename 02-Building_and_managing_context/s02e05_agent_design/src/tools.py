from dataclasses import dataclass
from typing import Literal, Any, Callable, Awaitable

from .vision_service import build_image_url, run_vision
from .filesystem_client import MCPFileSystemClient
from .hub_client import AiDevsHubClient
from .filesystem_service import (
    read_text_file, read_media_file, list_directory, directory_tree
)
from .config import ProviderBaseSettings
from .logger import logger


FileType = Literal['text', 'media']
async def read_file(
    file_path: str, 
    file_type: FileType, 
    filesystem_client: MCPFileSystemClient,
    vision_provider_config: ProviderBaseSettings,
    vision_model: str,
    vision_task: str | None = None
) -> dict[str, str]:
    logger.tool('read_file', {'file_path': file_path, 'file_type': file_type})

    if file_type == 'text':
        text_result = await read_text_file(file_path, filesystem_client)

        if not text_result['ok']:
            logger.error(
                'Text file read failed',
                f'path={file_path} result={text_result}'
            )
            return {
                'status': 'error',
                'path': file_path,
                'file_type': file_type,
                'error': 'Failed to read file.',
                'hint': 'Check if the file exists.'
            }
        else:
            content = text_result['content']

    elif file_type == 'media':
        if vision_task is None or not vision_task:
            logger.error(
                'vision_task can not be empty string or None',
                f'task={vision_task}'
            )
            return {
                'status': 'error',
                'path': file_path,
                'file_type': file_type,
                'error': 'vision_task can not be empty string or None',
                'hint': 'Write a vision_task that explains to the model what it needs to do.'
            }

        media_result = await read_media_file(file_path, filesystem_client)
        if not media_result['ok']:
            logger.error(
                'Media file read failed',
                f'path={file_path} result={media_result}'
            )
            return {
                'status': 'error',
                'path': file_path,
                'file_type': file_type,
                'error': 'Failed to read file.',
                'hint': 'Check if the file exists.'
            }
        else:
            media_content = media_result['content'][0]
            image_url = build_image_url(media_content['data'], media_content['mimeType'])
            content = await run_vision(
                image_url=image_url,
                query=vision_task,
                provider_config=vision_provider_config,
                model=vision_model
            )
            

    else:
        logger.error(
            'Incorrect file_type',
            f'The file_type passed by the agent is not supported, file_type: {file_type}'
        )
        return {
            'status': 'error',
            'path': file_path,
            'file_type': file_type,
            'error': 'Incorrect file_type.',
            'hint': 'Choose the correct file_type and rerun the tool.',
        }
    
    logger.success(f'File read successfully: {file_path}')
    return {
        'status': 'success',
        'path': file_path,
        'file_type': file_type,
        'content': content
    }

ManageMode = Literal['list_directory', 'directory_tree']
async def manage_files(path: str, mode: ManageMode, filesystem_client: MCPFileSystemClient) -> dict[str, Any]:
    logger.tool('manage_files', {'path': path, 'mode': mode})

    if mode == 'list_directory':
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

async def send_instructions(
    task: str,
    instructions: list[str],
    hub_client: AiDevsHubClient
) -> dict[str, Any]:
    logger.tool('send_instructions', {'task': task, 'instructions': instructions})
    result = await hub_client.send_instructions(task, instructions)
    logger.success('instructions sent to hub')
    return {
        'status': 'success',
        'result': result
    }

@dataclass
class Tool:
    definition: dict
    handler: Callable[..., Awaitable[dict[str, Any]]]

tools: list[Tool] = [
    Tool(
        definition={
            'type': 'function',
            'name': 'read_file',
            'description': 'Read a text or media file from the workspace. For media files, provide a vision_task describing what should be extracted from the image.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'file_path': {
                        'type': 'string',
                        'description': 'Absolute or workspace-relative path to the file that should be read.'
                    },
                    'file_type': {
                        'type': 'string',
                        'enum': ['text', 'media'],
                        'description': 'Set to text for plain files and media for images or other visual files.'
                    },
                    'vision_task': {
                        'type': 'string',
                        'description': 'Required only for media files. Describe exactly what should be extracted or identified from the image.'
                    }
                },
                'required': ['file_path', 'file_type']
            }
        },
        handler=read_file
    ),
    Tool(
        definition={
            'type': 'function',
            'name': 'manage_files',
            'description': 'Inspect the workspace structure. Use this to list files in a directory or get a recursive directory tree before choosing specific files to read.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'path': {
                        'type': 'string',
                        'description': 'Directory path to inspect. Use workspace-relative paths such as ., workspace, drone, or nested directories.'
                    },
                    'mode': {
                        'type': 'string',
                        'enum': ['list_directory', 'directory_tree'],
                        'description': 'Choose list_directory for one directory level or directory_tree for a recursive tree view.'
                    }
                },
                'required': ['path', 'mode']
            }
        },
        handler=manage_files
    ),
    Tool(
        definition={
            'type': 'function',
            'name': 'send_instructions',
            'description': 'Send a candidate list of drone instructions to the hub verify endpoint for the given task.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'task': {
                        'type': 'string',
                        'description': 'Task name expected by the hub, for this lesson usually drone.'
                    },
                    'instructions': {
                        'type': 'array',
                        'description': 'Ordered list of drone API instructions to send to the hub.',
                        'items': {
                            'type': 'string'
                        }
                    }
                },
                'required': ['task', 'instructions']
            }
        },
        handler=send_instructions
    )
]

def find_tool(tool_name: str) -> Callable[..., Awaitable[dict[str, Any]]] | None:
    for tool in tools:
        if tool.definition.get('name') == tool_name:
            return tool.handler
    return None
