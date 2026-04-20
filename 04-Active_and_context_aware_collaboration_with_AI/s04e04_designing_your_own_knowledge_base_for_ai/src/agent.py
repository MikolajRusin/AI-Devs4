import json

from .chat_api import chat_responses
from .config import AGENT_MODEL
from .hub_client import HubClient
from .mcp_client import MCPFileSystemClient
from .tools import TOOLS_DEFINITION, make_handlers

MAX_ITERATIONS = 50


def _extract_tool_calls(output: list[dict]) -> list[dict]:
    return [item for item in output if item.get('type') == 'function_call']


def _extract_final_message(output: list[dict]) -> str | None:
    for item in output:
        if item.get('type') == 'message':
            for content in item.get('content', []):
                text = content.get('text')
                if isinstance(text, str) and text:
                    return text
    return None


async def _execute_tools(tool_calls: list[dict], handlers: dict) -> list[dict]:
    results = []
    for call in tool_calls:
        name = call.get('name')
        raw_args = call.get('arguments', '{}')

        try:
            args = json.loads(raw_args)
        except json.JSONDecodeError:
            output = {'status': 'error', 'error': 'Invalid JSON arguments'}
            results.append({
                'type': 'function_call_output',
                'call_id': call['call_id'],
                'output': json.dumps(output),
            })
            continue

        print(f'[agent] → {name}({json.dumps(args, ensure_ascii=False)[:200]})')

        handler = handlers.get(name)
        if handler is None:
            output = {'status': 'error', 'error': f'Unknown tool: {name}'}
        else:
            try:
                result = handler(**args)
                output = await result if hasattr(result, '__await__') else result
            except Exception as exc:
                output = {'status': 'error', 'error': str(exc)}

        print(f'[agent] ← {name}: {json.dumps(output, ensure_ascii=False)[:500]}')
        results.append({
            'type': 'function_call_output',
            'call_id': call['call_id'],
            'output': json.dumps(output, ensure_ascii=False),
        })

    return results


def _extract_done_result(tool_outputs: list[dict]) -> str | None:
    for item in tool_outputs:
        if item.get('type') != 'function_call_output':
            continue
        try:
            output = json.loads(item.get('output', '{}'))
        except json.JSONDecodeError:
            continue
        if output.get('code') == 0:
            message = output.get('message')
            if isinstance(message, str) and message:
                return message
    return None


async def run_agent(instructions: str, user_message: str, mcp: MCPFileSystemClient, hub: HubClient, root) -> str:
    handlers = make_handlers(mcp=mcp, hub=hub, root=root)
    conversation = [{'role': 'user', 'content': user_message}]

    print(f'[agent] starting — model={AGENT_MODEL}, tools={len(TOOLS_DEFINITION)}')

    for iteration in range(MAX_ITERATIONS):
        print(f'\n[agent] iteration {iteration + 1}/{MAX_ITERATIONS}')
        response = await chat_responses(
            model=AGENT_MODEL,
            input=conversation,
            instructions=instructions,
            tools=TOOLS_DEFINITION,
        )

        output = response.get('output', [])
        conversation.extend(output)

        tool_calls = _extract_tool_calls(output)
        if tool_calls:
            tool_outputs = await _execute_tools(tool_calls, handlers)
            conversation.extend(tool_outputs)
            done_message = _extract_done_result(tool_outputs)
            if done_message:
                print(f'[agent] finished via tool result: {done_message}')
                return done_message
            continue

        message = _extract_final_message(output)
        if message:
            print(f'[agent] finished: {message}')
            return message

    return 'Agent reached max iterations without finishing.'
