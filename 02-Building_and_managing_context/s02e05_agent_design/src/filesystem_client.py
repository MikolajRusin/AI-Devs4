import json
from pathlib import Path
from contextlib import AsyncExitStack
from mcp.client.stdio import stdio_client
from mcp.types import CallToolResult
from mcp import ClientSession, StdioServerParameters
from .logger import logger


class MCPFileSystemClient:
    def __init__(self, mcp_config_path: str | Path, server_name: str):
        self.config = self._get_config(mcp_config_path, server_name)
        self.allowed_roots = self._extract_allowed_roots(self.config)
        self.session: ClientSession | None = None
        self.exist_stack = AsyncExitStack()
        self.stdio = None
        self.write = None

    @staticmethod
    def _get_config(mcp_config_path: str | Path, server_name: str) -> dict:
        try:
            with open(mcp_config_path, 'r', encoding='utf-8') as file:
                config = json.load(file)
        except FileNotFoundError as e:
            logger.error('Not found MCP file.', 'The mcp configuration file was not found')
            raise
        except json.JSONDecodeError:
            logger.error(
                'Invalid MCP file',
                f'The mcp configuration file is not a valid JSON: {mcp_config_path}'
            )
            raise

        filesystem_config = config['mcpServers'].get(server_name)
        if filesystem_config is None:
            logger.error('Not found MCP config', f'Missing "{server_name}" config section')
            raise ValueError(f'Missing "{server_name}" config section')    

        return filesystem_config

    @staticmethod
    def _extract_allowed_roots(config: dict) -> list[Path]:
        roots = []
        for arg in config.get('args', []):
            if isinstance(arg, str) and arg.startswith('/'):
                roots.append(Path(arg))
        
        roots.sort()
        return roots

    def _normalize_path(self, path_value: str) -> str:
        path = Path(path_value)

        if not self.allowed_roots:
            return path_value

        default_root = self.allowed_roots[0]

        if path_value in {'', '.'}:
            return str(default_root)

        if path_value == 'workspace':
            return str(default_root)

        return str(default_root / path)

    async def connect_to_server(self) -> None:
        logger.start('Connecting to the MCP FileSystem Server')

        if self.session is not None:
            logger.warn('MCP Client is already connected to the MCP FileSystem Server')
            return

        server_params = StdioServerParameters(
            **self.config,
            env=None
        )

        stdio_transport = await self.exist_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exist_stack.enter_async_context(
            ClientSession(self.stdio, self.write)
        )
        
        await self.session.initialize()
        logger.success('Connected to the MCP FileSystem Server')

    async def call_tool(self, tool_name: str, tool_args: dict) -> dict:
        logger.start('MCP FileSystem Server executing the tool')
        normalized_args = dict(tool_args)
        if 'path' in normalized_args and isinstance(normalized_args['path'], str):
            normalized_args['path'] = self._normalize_path(normalized_args['path'])
        logger.tool(tool_name, normalized_args)

        if self.session is None:
            logger.error(
                'MCP tool call failed',
                'MCP session is not initialized'
            )
            raise RuntimeError('MCP session is not initialized')

        result: CallToolResult = await self.session.call_tool(tool_name, normalized_args)

        if result.isError:
            logger.error('Tool Executing Error', 'Error during executing tool')
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
            logger.info('MCP FileSystem Server returned structured content')
            logger.tool_result(
                tool_name,
                success=True,
                output=json.dumps(content, ensure_ascii=False)
            )
            return {
                'ok': True,
                'content': content['content']
            }

        if result.content:
            content = result.content[0]
            if content.type == 'text':
                logger.info('MCP FileSystem Server returned not structured content')
                logger.tool_result(
                    tool_name,
                    success=True,
                    output=content.text
                )
                return {
                    'ok': True,
                    'content': content.text
                }
        
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
        logger.stop('Disconnecting from the MCP FileSystem Server')
        await self.exist_stack.aclose()
        self.exist_stack = AsyncExitStack()
        self.session = None
        self.stdio = None
        self.write = None
        logger.success('MCP server disconnected')
