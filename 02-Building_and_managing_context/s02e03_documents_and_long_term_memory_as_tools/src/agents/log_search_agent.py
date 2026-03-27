import json
from typing import Any

from ..clients.hub_client import AiDevsHubClient
from ..mcp.filesystem_client import MCPFileSystemClient
from ..tools.handlers import fetch_logs, search_logs, manage_files, ManageMode
from ..tools.tools_definition import TOOLS_DEFINITION
from ..services.log_service import EventType
from ..logger import logger


class LogSearchAgent:
    SYSTEM_INSTRUCTIONS = """
You are LogSearchAgent, a narrow log-filtering worker.

MainAgent decides the strategy.
You only execute one narrow filtering step at a time.

Your task:
- inspect raw logs available in your filesystem scope,
- run exactly the filtering step requested by MainAgent,
- save the filtered result to a new file,
- return the file path and stop.

Severity behavior:
- if MainAgent asks for CRIT, filter only CRIT,
- if MainAgent asks for ERRO, filter only ERRO,
- if MainAgent asks for WARN, filter only WARN,
- if MainAgent asks for INFO, filter only INFO,
- never decide on your own to combine multiple severity levels.

Search behavior:
- if MainAgent gives no search phrase, do severity-only filtering,
- if MainAgent gives one search phrase, use only that one search phrase,
- do not invent or guess search phrases,
- do not broaden the request on your own,
- do not turn a narrow task into a broader exploration.

Tool behavior:
- before filtering, make sure the raw log file is available,
- if the raw log file is missing, fetch it first,
- if the raw log file already exists, do not fetch it again unless MainAgent explicitly asks for a refresh,
- do not inspect unnecessary directories,
- once you have enough filtered material, stop searching and save the file.

Required sequence:
1. Make sure the raw log file is available.
2. Run the requested narrow filter.
3. Create or reuse one folder for the current date inside your output area.
4. Save the filtered result to a file in that date folder using manage_files with mode='write_file'.
5. Return the path to that file and stop.

File rules:
- use paths relative to your filesystem roots,
- do not prefix paths with workspace/,
- write only to your own output area,
- do not write the final answer for the hub.
- use a date-based folder for your saved files,
- the folder name should be the current date in YYYY-MM-DD format,
- save multiple result files for the same day inside that same date folder,
- when using your own tools such as manage_files, use only local paths relative to your own output root,
- do not prefix your own write paths with agents/log_search_agent/,
- only in the final structured response should you convert those paths into MainAgent-readable paths,
- in the final response, return result_file_path and output_dir_path with the agents/log_search_agent/... prefix so MainAgent can read them directly.

Completion rule:
- your task is not complete until a result file exists,
- after writing the file, stop using tools,
- return the structured final response with the file path.

Your goal is to execute one narrow delegated filter step as efficiently as possible.
"""

    FINAL_RESPONSE_FORMAT = {
        'type': 'json_schema',
        'name': 'log_search_agent_result',
        'schema': {
            'type': 'object',
            'properties': {
                'status': {
                    'type': 'string',
                    'enum': ['done']
                },
                'searched_for': {
                    'type': 'string'
                },
                'summary': {
                    'type': 'string'
                },
                'remaining_gaps': {
                    'type': 'string'
                },
                'result_file_path': {
                    'type': 'string'
                },
                'output_dir_path': {
                    'type': 'string'
                }
            },
            'required': [
                'status',
                'searched_for',
                'summary',
                'remaining_gaps',
                'result_file_path',
                'output_dir_path'
            ],
            'additionalProperties': False
        },
        'strict': True
    }

    def __init__(self, hub_client: AiDevsHubClient, filesystem_client: MCPFileSystemClient, agent_client, model: str, max_iterations: int = 10):
        self.hub_client = hub_client
        self.mcp_filesystem_client = filesystem_client
        self.agent_client = agent_client
        self.model = model
        self.max_iterations = max_iterations

        self.tools_registry = {
            'fetch_logs': self._fetch_logs,
            'search_logs': self._search_logs,
            'manage_files': self._manage_files
        }
        logger.info(
            f'LogSearchAgent initialized. model={self.model} max_iterations={self.max_iterations} tools={list(self.tools_registry.keys())}'
        )

    async def _fetch_logs(self) -> dict[str, str]:
        results = await fetch_logs(
            hub_client=self.hub_client
        )
        return results

    async def _search_logs(
        self, 
        path: str, 
        event: list[EventType] | None = None,
        search: list[str] | None = None,
        first_n_per_group: int | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        results = await search_logs(
            path=path,
            event=event,
            search=search,
            first_n_per_group=first_n_per_group,
            limit=limit,
            filesystem_client=self.mcp_filesystem_client
        )
        return results

    async def _manage_files(
        self,
        path: str,
        mode: ManageMode,
        content: str | None = None
    ) -> dict[str, Any]:
        results = await manage_files(
            path=path,
            mode=mode,
            filesystem_client=self.mcp_filesystem_client,
            content=content
        )
        return results

    def _get_tools_definition(self):
        return [tool_definition for tool_definition in TOOLS_DEFINITION if tool_definition['name'] in self.tools_registry]

    async def _execute_tools(self, tool_calls: list[dict]) -> list[dict]:
        tool_calls_info = []
        for tool_call in tool_calls:
            tool_name = tool_call['name']
            tool_args = json.loads(tool_call['arguments'])
            logger.tool(tool_name, tool_args)
            
            tool_results = await self.tools_registry[tool_name](**tool_args)
            tool_calls_info.append(
                {
                    'type': 'function_call_output',
                    'call_id': tool_call['call_id'],
                    'output': json.dumps(tool_results, ensure_ascii=False)
                }
            )
        return tool_calls_info

    def _extract_output_message(self, output_items: list[dict]) -> dict | None:
        for item in output_items:
            if item.get('type') == 'message':
                return item
        return None

    async def _chat(self, conversation: list[dict]) -> dict[str, Any]:
        response = await self.agent_client(
            model=self.model,
            conversation=conversation,
            instructions=self.SYSTEM_INSTRUCTIONS,
            tools=self._get_tools_definition(),
            response_format=self.FINAL_RESPONSE_FORMAT
        )
        return response 

    async def run(self, task: str) -> str:
        logger.agent('LogSearchAgent started', {'task': task})

        await self.mcp_filesystem_client.connect_to_server()
        conversation = [
            {'role': 'user', 'content': task}
        ]

        try:
            for iteration in range(self.max_iterations):
                logger.agent_iteration(iteration + 1, self.max_iterations)
                response = await self._chat(conversation)

                if response.get('error'):
                    logger.error('Agent response error', json.dumps(response['error'], ensure_ascii=False))
                    return 'The error occured while processing the task'

                output_items = response.get('output', [])
                if not output_items:
                    logger.agent_empty_output()
                    return 'No response received'

                tool_calls = [item for item in output_items if item.get('type') == 'function_call']
                tool_reasoning = [item for item in output_items if item.get('type') == 'reasoning']
                logger.agent_tools(len(tool_calls))
                logger.agent_reasoning(len(tool_reasoning))
                conversation.extend(output_items)

                if tool_calls:
                    tool_results = await self._execute_tools(tool_calls)
                    conversation.extend(tool_results)
                    continue

                output_message = self._extract_output_message(output_items)
                if output_message:
                    message = output_message['content'][0]['text']
                    logger.response(f'LogSearchAgent | {message}')
                    logger.agent_finished()
                    return message

                logger.warn('Model returned no tool calls and no final message')
                return 'Model did not return a final answer.'

        finally:
            await self.mcp_filesystem_client.cleanup()
