from ..utils.logger import logger

from pathlib import Path
from typing import Any
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.types import CallToolResult
from mcp.client.stdio import stdio_client
import json


class MCPFileSystemClient:
    def __init__(self, config_path: str | Path):
        with open(config_path, 'r', encoding='utf-8') as file: 
            self.config = json.load(file)

        self.session: ClientSession | None = None
        self.exit_stack = AsyncExitStack()
        self.stdio = None
        self.write = None

    async def connect_to_server(self) -> None:
        logger.mcp_filesystem(f'Connecting with file-system server')

        if self.session is not None:
            return

        filesystem_config = self.config['mcpServers'].get('filesystem')
        if filesystem_config is None:
            logger.error('Not found MCP config', 'Missing "filesystem" config section')
            raise ValueError('Missing "filesystem" config section')

        server_params = StdioServerParameters(
            **filesystem_config,
            env=None
        )

        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(self.stdio, self.write)
        )

        await self.session.initialize()
        logger.success('MCP server connected')

    async def call_tool(self, tool_name: str, tool_args: dict[str, Any]):
        logger.tool(tool_name, tool_args)

        if self.session is None:
            logger.error(
                'MCP tool call failed',
                'MCP session is not initialized'
            )
            raise RuntimeError('MCP session is not initialized')

        result: CallToolResult = await self.session.call_tool(tool_name, tool_args)

        if result.isError:
            logger.tool_result(
                tool_name,
                success=False,
                output=result.content[0].text
            )
            return {
                'ok': False,
                'error': 'Tool execution failed'
            }

        if result.structuredContent:
            content = result.structuredContent
            logger.info('Returned structured content')
            logger.tool_result(
                tool_name,
                success=True,
                output=json.dumps(content, ensure_ascii=False)
            )
            return content

        if result.content:
            content = result.content[0]
            if content.type == 'text':
                logger.tool_result(
                    tool_name,
                    success=True,
                    output=content.text
                )
                return content.text
        
        logger.tool_result(
            tool_name,
            success=True,
            output='No structured or text content returned',
        )
        return {
            'ok': True,
            'content': None
        }

    async def cleanup(self) -> None:
        logger.mcp_filesystem(f'Disconnecting with file-system server')
        await self.exit_stack.aclose()
        self.exit_stack = AsyncExitStack()
        self.session = None
        self.stdio = None
        self.write = None
        logger.success('MCP server disconnected')