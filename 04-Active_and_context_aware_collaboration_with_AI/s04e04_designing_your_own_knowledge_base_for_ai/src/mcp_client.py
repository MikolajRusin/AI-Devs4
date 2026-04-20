import json
from pathlib import Path
from contextlib import AsyncExitStack
from mcp.client.stdio import stdio_client
from mcp.types import CallToolResult
from mcp import ClientSession, StdioServerParameters


class MCPFileSystemClient:
    def __init__(self, mcp_config_path: str | Path, server_name: str):
        self.config = self._load_config(mcp_config_path, server_name)
        self.session: ClientSession | None = None
        self._exit_stack = AsyncExitStack()

    @staticmethod
    def _load_config(mcp_config_path: str | Path, server_name: str) -> dict:
        with open(mcp_config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        server = config['mcpServers'].get(server_name)
        if server is None:
            raise ValueError(f'MCP server "{server_name}" not found in {mcp_config_path}')
        return server

    async def connect(self) -> None:
        if self.session is not None:
            return
        params = StdioServerParameters(**self.config, env=None)
        stdio_transport = await self._exit_stack.enter_async_context(stdio_client(params))
        stdio, write = stdio_transport
        self.session = await self._exit_stack.enter_async_context(ClientSession(stdio, write))
        await self.session.initialize()
        print('[mcp] connected to filesystem server')

    async def call_tool(self, name: str, args: dict) -> dict:
        result: CallToolResult = await self.session.call_tool(name, args)
        if result.isError:
            return {'ok': False, 'error': result.content[0].text if result.content else 'unknown error'}
        if result.content:
            return {'ok': True, 'content': result.content[0].text}
        return {'ok': True, 'content': None}

    async def cleanup(self) -> None:
        await self._exit_stack.aclose()
        self.session = None
        print('[mcp] disconnected')
