import json
from typing import Any

from .tools import tools, find_tool
from .chat_client import chat_responses
from .hub_client import AiDevsHubClient
from .config import Settings, ProviderBaseSettings
from .filesystem_client import MCPFileSystemClient
from .logger import logger


async def _execute_tools(
    tool_calls: list[dict], 
    hub_client: AiDevsHubClient, 
    filesystem_client: MCPFileSystemClient,
    vision_provider_config: ProviderBaseSettings,
    vision_model: str,
) -> list[dict]:
    tool_calls_info = []
    for tool_call in tool_calls:
        tool_name = tool_call.get('name')
        raw_arguments = tool_call.get('arguments', '{}')

        try:
            tool_args = json.loads(raw_arguments)
        except json.JSONDecodeError:
            tool_args = {}
            tool_results = {
                'status': 'error',
                'error': 'Tool arguments are not valid JSON.',
                'raw_arguments': raw_arguments,
            }
            tool_calls_info.append(
                {
                    'type': 'function_call_output',
                    'call_id': tool_call['call_id'],
                    'output': json.dumps(tool_results, ensure_ascii=False)
                }
            )
            continue

        logger.info(f'Model called tool -> Tool Name: {tool_name}, Arguments: {tool_args}')
        tool = find_tool(tool_name)
        if tool is None:
            tool_results = {
                'status': 'error',
                'error': f'Unknown tool: {tool_name}'
            }
        elif tool_name == 'read_file':
            tool_results = await tool(
                filesystem_client=filesystem_client, 
                vision_provider_config=vision_provider_config, 
                vision_model=vision_model,
                **tool_args
            )
        elif tool_name == 'manage_files':
            tool_results = await tool(
                filesystem_client=filesystem_client,
                **tool_args
            )
        elif tool_name == 'send_instructions':
            tool_results = await tool(hub_client=hub_client, **tool_args)
        else:
            tool_results = {
                'status': 'error',
                'error': f'Tool dispatch is not configured for: {tool_name}'
            }

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


def _extract_message_text(message_item: dict[str, Any]) -> str | None:
    for content in message_item.get('content', []):
        text = content.get('text')
        if isinstance(text, str) and text:
            return text
    return None

async def run_agent(
    settings: Settings, 
    hub_client: AiDevsHubClient, 
    filesystem_client: MCPFileSystemClient,
    task: str, 
    instructions: str
) -> dict:
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
            tool_results = await _execute_tools(tool_calls, hub_client, filesystem_client, vision_provider_config=settings.openai, vision_model=settings.vision_model)
            conversation.extend(tool_results)
            logger.success('Tools executed')
            continue
        else:
            output_message = _extract_output_message(output_items)
            if not output_message:
                logger.warn('No output message found in model response')
                return 'No output message received from the model.'
            
            message = _extract_message_text(output_message)
            if not message:
                logger.warn('No text found in output message content')
                return 'No text output received from the model.'
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
