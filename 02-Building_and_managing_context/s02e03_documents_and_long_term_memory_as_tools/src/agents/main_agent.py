import json
from typing import Any

from .log_search_agent import LogSearchAgent
from ..clients.hub_client import AiDevsHubClient
from ..mcp.filesystem_client import MCPFileSystemClient
from ..tools.handlers import read_file, manage_files, ManageMode, count_tokens, send_logs
from ..tools.tools_definition import TOOLS_DEFINITION
from ..logger import logger


class MainAgent:
    SYSTEM_INSTRUCTIONS = """
You are MainAgent, the orchestrator for the failure task.

Your job is to build the final condensed failure log efficiently and iteratively.

You must use this severity escalation order:
1. CRIT
2. ERRO
3. WARN
4. INFO

Never start by filtering multiple severity levels at once.
Always begin with CRIT only.
If the current result is insufficient, move only one step further in the severity order.

Your workflow:
1. Delegate one narrow filtering task to log_search_agent.
2. The delegated task should normally contain only one severity level.
3. Only include a search phrase when it comes from verification feedback or already confirmed evidence.
4. Wait for the subagent to return a saved result file path.
5. Read the returned file.
6. Merge useful lines into your own aggregated result file.
7. Count tokens for the aggregated result.
8. Send the aggregated result to the hub for verification.
9. Read the feedback.
10. Only then decide the next delegated task.

Delegation rules:
- do not inspect raw logs directly,
- do not ask the subagent for CRIT, ERRO, WARN, and INFO together,
- do not invent or guess search phrases on your own,
- if you do not yet have specific clues from the system, delegate severity-only searches,
- if verification feedback mentions a subsystem, product, symptom, or component, then use that as the next narrow search clue,
- when the subagent returns result_file_path, use that exact path,
- do not rewrite, shorten, or guess a different path than the one returned by the subagent,
- after each delegated run, verification is the default next step, not another immediate delegation.

Aggregation rules:
- maintain your own growing aggregated result file,
- append useful lines from each delegated result file,
- use the aggregated file as the working draft for the final answer,
- keep the final output concise and within token budget.

File rules:
- use paths relative to your available filesystem roots,
- subagent files are saved in the agents area available to you,
- you must read the files created by the subagent from the agents area,
- you may use manage_files to inspect directories and files in the agents area before reading them,
- you must create and maintain your own aggregated file in the results area,
- after each delegated run, add the useful log lines from the subagent file into your own aggregated results file,
- do not expect the subagent to write into your results file for you,
- save the final condensed log file in your results area,
- when ready, send it to the hub using the send_logs tool.

Final answer rules:
- after using send_logs, inspect the hub response carefully,
- if the hub response contains a flag, return that flag as your final answer,
- if the hub response contains feedback instead of a flag, use that feedback for the next iteration,
- do not stop after send_logs unless you have either a flag or a clear verification response to act on.

Your goal is to reach the correct final answer with minimal broad exploration.
"""

    def __init__(self, hub_client: AiDevsHubClient, filesystem_client: MCPFileSystemClient, agent_client, model: str, log_search_agent: LogSearchAgent, max_iterations: int = 10):
        self.hub_client = hub_client
        self.mcp_filesystem_client = filesystem_client
        self.agent_client = agent_client
        self.model = model
        self.max_iterations = max_iterations

        self.log_search_agent = log_search_agent
        self.subagents_registry = {
            'log_search_agent': self.log_search_agent
        }
        self.tools_registry = {
            'read_file': self._read_file,
            'manage_files': self._manage_files,
            'count_tokens': self._count_tokens,
            'send_logs': self._send_logs,
            'delegate_to_agent': self._delegate_agent
        }
        logger.info(
            f'MainAgent initialized. model={self.model} max_iterations={self.max_iterations} tools={list(self.tools_registry.keys())}'
        )

    async def _read_file(self, path: str) -> dict[str, str]:
        results = await read_file(
            file_path=path,
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

    async def _count_tokens(self, logs_path: str, ) -> dict[str, Any]:
        results = await count_tokens(
            logs_path=logs_path,
            filesystem_client=self.mcp_filesystem_client,
            model=self.model
        )
        return results

    async def _send_logs(self, logs_path: str):
        results = await send_logs(
            logs_path=logs_path,
            filesystem_client=self.mcp_filesystem_client,
            hub_client=self.hub_client
        )
        return results

    async def _delegate_agent(self, agent_name: str, task: str) -> str:
        logger.agent(f'Delegating to {agent_name}', {'task': task})
        subagent = self.subagents_registry[agent_name]
        result = await subagent.run(task)
        logger.agent(f'{agent_name} finished', {'result': result[:300]})
        return result

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
            tools=self._get_tools_definition()
        )
        return response 

    async def run(self, task: str) -> str:
        logger.agent('MainAgent started', {'task': task})

        await self.mcp_filesystem_client.connect_to_server()
        conversation = [
            {'role': 'user', 'content': task}
        ]

        try:
            for iteration in range(self.max_iterations):
                logger.agent_iteration(iteration + 1, self.max_iterations)
                response = await self._chat(conversation)

                if response.get('error'):
                    logger.error('MainAgent response error', json.dumps(response['error'], ensure_ascii=False))
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
                    logger.response(f'MainAgent | {message}')
                    logger.agent_finished()
                    return message

                logger.warn('Model returned no tool calls and no final message')
                return 'Model did not return a final answer.'

        finally:
            await self.mcp_filesystem_client.cleanup()
