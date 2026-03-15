from typing import Any
from ..utils.logging import get_logger

from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.types import CallToolResult
from mcp.client.stdio import stdio_client
import json


logger = get_logger('MCP_CLIENT')

class MCPClient:
    def __init__(self):
        self.session: ClientSession | None = None
        self.exit_stack = AsyncExitStack()
        self.stdio = None
        self.write = None

    async def connect_to_server(self, module_name: str):
        if self.session is not None:
            return

        server_params = StdioServerParameters(
            command='python',
            args=['-m', module_name],
            env=None
        )

        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(self.stdio, self.write)
        )

        logger.info('Connecting to the MCP server: %s', module_name)
        await self.session.initialize()
        
        response = await self.session.list_tools()
        logger.info('Connected to server with tools: %s', [tool.name for tool in response.tools])

    async def call_tool(self, tool_name: str, tool_args: dict[str, Any]):
        logger.info(f'Calling {tool_name} with args {tool_args}')
        results: CallToolResult = await self.session.call_tool(tool_name, tool_args)

        if results.isError:
            return {
                'ok': False,
                'error': 'Tool execution failed'
            }

        if results.structuredContent:
            return results.structuredContent

        if results.content:
            content = results.content[0]
            if content.type == 'text':
                logger.info(f'Results: {content.text}')
                return json.loads(content.text)
            
        return {
            'ok': False,
            'error': 'Empty tool result.'
        }

    async def cleanup(self):
        await self.exit_stack.aclose()
        self.exit_stack = AsyncExitStack()
        self.session = None
        self.stdio = None
        self.write = None
