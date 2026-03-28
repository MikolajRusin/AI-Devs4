import json
from typing import Any

from .tools import tools, find_tool
from .chat_client import chat_responses
from .hub_client import AiDevsHubClient
from .config import Settings
from .logger import logger



async def _execute_tools(tool_calls: list[dict], hub_client: AiDevsHubClient) -> list[dict]:
    tool_calls_info = []
    for tool_call in tool_calls:
        tool_name = tool_call.get('name')
        tool_args = json.loads(tool_call.get('arguments'))
        logger.info(f'Model called tool -> Tool Name: {tool_name}, Arguments: {tool_args}')
        
        tool = find_tool(tool_name)
        tool_results = await tool(hub_client=hub_client, **tool_args)
        tool_calls_info.append(
            {
                'type': 'function_call_output',
                'call_id': tool_call['call_id'],
                'output': json.dumps(tool_results, ensure_ascii=False)
            }
        )
    return tool_calls_info

def _extract_output_message(output_items: list[dict[str, Any]]) -> dict[str, Any] | None:
    for item in output_items:
        if item.get('type') == 'message':
            return item
    return None

async def run_agent(settings: Settings, hub_client: AiDevsHubClient, task: str, instructions: str) -> dict:
    logger.agent('LogSearchAgent started', {'tools': [tool.definition.get('name') for tool in tools]})
    logger.query(task)

    conversation = [
        {'role': 'user', 'content': task}
    ]

    agent_tools = [tool.definition for tool in tools]
    for iteration in range(settings.max_iterations):
        logger.info(f'Starting agent iteration {iteration + 1}/{settings.max_iterations}')

        chat_response = await chat_responses(
            provider_config=settings.openrouter,
            model=settings.agent_model,
            input=conversation,
            instructions=instructions,
            tools=agent_tools
        )

        if chat_response.get('error'):
            logger.error('Response agent error', json.dumps(chat_response['error']))
            return 'The error occured while processing the request'

        output_items = chat_response.get('output', '')
        if not output_items:
            logger.warn('Returned empty output')
            return 'No response received'      

        tool_calls = [item for item in output_items if item.get('type') == 'function_call']
        tool_reasoning = [item for item in output_items if item.get('type') == 'reasoning']
        logger.info(f'Detected {len(tool_calls)} tool call(s) and {len(tool_reasoning)} reasoning(s) in current iteration')
        conversation.extend(output_items)

        if tool_calls:
            logger.start('Agent Executing tools...')
            tool_results = await _execute_tools(tool_calls, hub_client)
            conversation.extend(tool_results)
            logger.success('Tools executed')
            continue
        else:
            output_message = _extract_output_message(output_items)
            if not output_message:
                logger.warn('No output message found in model response')
                return 'No output message received from the model.'
            
            message = output_message['content'][0]['text']
            logger.response(message)
            return message

    logger.error(
        'Agent stalled',
        'Model returned no tool calls and no final message.'
    )
    logger.info(f"Response status: {chat_response.get('status')}")
    logger.info(f"Response incomplete details: {chat_response.get('incomplete_details')}")
    logger.info(
        f"Response output item types: {[item.get('type') for item in chat_response.get('output', [])]}"
    )
    return 'Model did not return a final answer.'