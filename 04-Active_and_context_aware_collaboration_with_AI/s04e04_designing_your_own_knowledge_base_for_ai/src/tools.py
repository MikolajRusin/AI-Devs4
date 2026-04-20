from pathlib import Path

from .hub_client import HubClient
from .mcp_client import MCPFileSystemClient

TOOLS_DEFINITION = [
    {
        'type': 'function',
        'name': 'read_file',
        'description': 'Read the content of a file from the local workspace.',
        'parameters': {
            'type': 'object',
            'properties': {
                'path': {
                    'type': 'string',
                    'description': 'Path to the file relative to the workspace root, e.g. "workspace/notes/rozmowy.txt".',
                }
            },
            'required': ['path'],
        },
    },
    {
        'type': 'function',
        'name': 'list_directory',
        'description': 'List the contents of a directory in the local workspace.',
        'parameters': {
            'type': 'object',
            'properties': {
                'path': {
                    'type': 'string',
                    'description': 'Path to the directory relative to the workspace root, e.g. "workspace/notes".',
                }
            },
            'required': ['path'],
        },
    },
    {
        'type': 'function',
        'name': 'filesystem',
        'description': (
            'Interact with the remote virtual filesystem API. '
            'action="reset" — clears all remote files (call once before building). '
            'action="createDirectory" — creates a directory at path. '
            'action="createFile" — creates a file at path with given content. '
            'action="listFiles" — lists contents of a directory at path. '
            'action="batch" — sends multiple operations at once via operations list (preferred for bulk creation). '
            'action="done" — submits the filesystem for verification (call last). '
            'action="help" — returns available API actions.'
        ),
        'parameters': {
            'type': 'object',
            'properties': {
                'action': {
                    'type': 'string',
                    'enum': ['reset', 'help', 'createDirectory', 'createFile', 'listFiles', 'batch', 'done'],
                    'description': 'The operation to perform.',
                },
                'path': {
                    'type': 'string',
                    'description': 'File or directory path. Required for createDirectory, createFile, listFiles.',
                },
                'content': {
                    'type': 'string',
                    'description': 'File content. Required for createFile.',
                },
                'operations': {
                    'type': 'array',
                    'items': {'type': 'object'},
                    'description': 'List of operations for batch mode. Each item must have "action" and "path", and optionally "content".',
                },
            },
            'required': ['action'],
        },
    },
]


def make_handlers(mcp: MCPFileSystemClient, hub: HubClient, root: Path) -> dict:

    async def read_file(path: str) -> dict:
        return await mcp.call_tool('read_file', {'path': str(root / path)})

    async def list_directory(path: str) -> dict:
        return await mcp.call_tool('list_directory', {'path': str(root / path)})

    def filesystem(action: str, path: str | None = None, content: str | None = None, operations: list | None = None) -> dict:
        if action == 'reset':
            return hub.reset()
        if action == 'done':
            return hub.done()
        if action == 'help':
            return hub.help()
        if action == 'listFiles':
            return hub.list_dir(path=path)
        if action == 'createDirectory':
            return hub.create_dir(path=path)
        if action == 'createFile':
            return hub.create_file(path=path, content=content)
        if action == 'batch':
            return hub.batch(operations=operations)
        return {'status': 'error', 'error': f'Unknown action: {action}'}

    return {
        'read_file': read_file,
        'list_directory': list_directory,
        'filesystem': filesystem,
    }
