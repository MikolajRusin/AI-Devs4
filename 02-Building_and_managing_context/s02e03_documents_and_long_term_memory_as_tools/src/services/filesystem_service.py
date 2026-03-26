from ..mcp.filesystem_client import MCPFileSystemClient
from typing import Any
import json


async def read_text_file(file_path: str, filesystem_client: MCPFileSystemClient) -> dict[str, Any]:
    result = await filesystem_client.call_tool(
        tool_name='read_text_file', 
        tool_args={'path': file_path}
    )
    return result

async def write_file(file_path: str, content: str, filesystem_client: MCPFileSystemClient) -> dict[str, Any]:
    result = await filesystem_client.call_tool(
        tool_name='write_file',
        tool_args={
            'path': file_path,
            'content': content
        }
    )
    return result

async def create_directory(dir_path: str, filesystem_client: MCPFileSystemClient) -> dict[str, Any]:
    result = await filesystem_client.call_tool(
        tool_name='create_directory', 
        tool_args={'path': dir_path}
    )
    return result

async def list_directory(dir_path: str, filesystem_client: MCPFileSystemClient) -> dict[str, Any]:
    result = await filesystem_client.call_tool(
        tool_name='list_directory', 
        tool_args={'path': dir_path}
    )
    return result

async def directory_tree(dir_path: str, filesystem_client: MCPFileSystemClient) -> dict[str, Any]:
    result = await filesystem_client.call_tool(
        tool_name='directory_tree', 
        tool_args={'path': dir_path}
    )
    return {
        'ok': result['ok'],
        'content': json.loads(result['content'])
    }