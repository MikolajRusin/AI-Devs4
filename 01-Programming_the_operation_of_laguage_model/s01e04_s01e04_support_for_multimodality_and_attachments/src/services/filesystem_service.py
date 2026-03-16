from ..mcp.filesystem_client import MCPFileSystemClient

async def read_text_file(file_path: str, filesystem_client: MCPFileSystemClient) -> str:
    result = await filesystem_client.call_tool(
        tool_name='read_text_file', 
        tool_args={'path': file_path}
    )
    return result['content']

async def read_media_file(file_path: str, filesystem_client: MCPFileSystemClient) -> dict[str, str]:
    result = await filesystem_client.call_tool(
        tool_name='read_media_file', 
        tool_args={'path': file_path}
    )
    return result['content'][0]