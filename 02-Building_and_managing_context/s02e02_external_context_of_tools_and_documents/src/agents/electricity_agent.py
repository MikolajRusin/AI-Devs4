import json
from typing import Literal, Any

from ..clients.hub_client import AiDevsHubClient
from ..clients.llm_router import create_llm_client
from ..tools.handlers import load_board, load_one_tile, rotate_one_tile
from ..tools.tools_definition import TOOLS_DEFINITION
from ..config import Settings
from ..utils.logger import logger


class ElectricityAgent:
    SYSTEM_INSTRUCTIONS = """
You are solving a 3x3 tile-rotation puzzle.

Work from evidence, not assumptions.

Strategy:
- First inspect the current board and the solved board.
- Group independent tool calls in the same iteration whenever possible.
- If several tiles need additional inspection, request all of them in the same iteration instead of one by one.
- Use separate iterations only when the next step depends on the result of the current one.
- Compare matching cells and find only the tiles that differ.
- For each differing tile, determine the minimum number of clockwise rotations needed.
- If any tile is uncertain or inconsistent, inspect that single tile before rotating it.
- Do not rotate blindly.
- Re-check the board after rotations whenever there is uncertainty.

Decision policy:
- Prefer the smallest reasonable number of clockwise rotations.
- Use detailed tile inspection for ambiguous cells.
- Batch full-board reads together, and batch multiple tile inspections together when they are independent.
- Apply rotations only when the target orientation is supported by observed exits.
- If one tile requires multiple clockwise rotations, you may call the same rotation tool multiple times for that tile within a single iteration.

Completion:
- Continue until the board is solved or until more evidence is needed.
- When solved, return only the final success result or flag.
    """

    def __init__(self, settings: Settings, hub_client: AiDevsHubClient):
        self.settings = settings
        self.hub_client = hub_client
        self.agent_client = create_llm_client(
            provider='OpenAI',
            provider_url=self.settings.openai.responses_url,
            api_key=self.settings.openai.api_key
        )
        self.vision_client = create_llm_client(
            provider='OpenRouter',
            provider_url=self.settings.openrouter.completions_url,
            api_key=self.settings.openrouter.api_key
        )

        self.tools_registry = {
            'load_board': self._load_board, 
            'load_one_tile': self._load_one_tile, 
            'rotate_one_tile': self._rotate_one_tile
        }

    def _load_board(self, board_type: Literal['current', 'solved']) -> dict[str, Any]:
        if board_type == 'current':
            board_settings = self.settings.current_board
        else:
            board_settings = self.settings.solved_board
        return load_board(
            board_type=board_type,
            hub_client=self.hub_client,
            board_settings=board_settings,
            llm_client=self.vision_client
        )

    def _load_one_tile(self, board_type: Literal['current', 'solved'], row: int, column: int) -> dict[str, Any]:
        if board_type == 'current':
            board_settings = self.settings.current_board
        else:
            board_settings = self.settings.solved_board
        return load_one_tile(
            board_type=board_type,
            row=row,
            column=column,
            hub_client=self.hub_client,
            board_settings=board_settings,
            llm_client=self.vision_client
        )

    def _rotate_one_tile(self, row: int, column: int) -> dict[str, Any]:
        return rotate_one_tile(
            row=row,
            column=column,
            hub_client=self.hub_client
        )

    def _execute_tools(self, tool_calls: list[dict]) -> list[dict]:
        tool_calls_info = []
        for tool_call in tool_calls:
            tool_name = tool_call['name']
            tool_args = json.loads(tool_call['arguments'])
            logger.tool(tool_name, tool_args)

            tool_results = self.tools_registry[tool_name](**tool_args)
            logger.tool_result(tool_name, True, json.dumps(tool_results, ensure_ascii=False))
            tool_calls_info.append(
                {
                    'type': 'function_call_output',
                    'call_id': tool_call['call_id'],
                    'output': json.dumps(tool_results, ensure_ascii=False)
                }
            )
        return tool_calls_info

    @staticmethod
    def _extract_output_message(output_items: list[dict[str, Any]]) -> dict[str, Any]:
        for item in output_items:
            if item.get('type') == 'message':
                return item
        return None

    def chat_responses(self, conversation: str) -> dict[str, Any]:
        response = self.agent_client(
            model=self.settings.agent_model,
            conversation=conversation,
            instructions=self.SYSTEM_INSTRUCTIONS,
            tools=TOOLS_DEFINITION
        )
        return response

    def run_agent(self, user_message: str):
        logger.start('Electricity agent started')
        logger.query(user_message)
        conversation = [
            {'role': 'user', 'content': user_message}
        ]

        for iteration in range(self.settings.max_iterations):
            logger.agent_iteration(iteration + 1, self.settings.max_iterations)
            response = self.chat_responses(conversation)

            if response.get('error'):
                logger.error('Agent response error', json.dumps(response['error'], ensure_ascii=False))
                return 'The error occured while processing the request'

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
                tool_results = self._execute_tools(tool_calls)
                conversation.extend(tool_results)
                continue

            output_message = self._extract_output_message(output_items)
            if output_message:
                message = output_message['content'][0]['text']
                logger.response(message)
                logger.agent_finished()
                return message

            logger.warn('Model returned no tool calls and no final message')
            return 'Model did not return a final answer.'
