import json

from .chat_api import chat_responses
from .config import AGENT_MODEL
from .tools import Tool, find_tool, make_tools

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


def _execute_tools(tool_calls: list[dict], tools: list[Tool]) -> list[dict]:
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
        handler = find_tool(name, tools)
        if handler is None:
            output = {'status': 'error', 'error': f'Unknown tool: {name}'}
        else:
            try:
                output = handler(**args)
            except Exception as exc:
                output = {'status': 'error', 'error': str(exc)}

        print(f'[agent] ← {name}: {json.dumps(output, ensure_ascii=False)[:500]}')
        results.append({
            'type': 'function_call_output',
            'call_id': call['call_id'],
            'output': json.dumps(output, ensure_ascii=False),
        })

    return results


def run_agent(instructions: str, user_message: str) -> str:
    tools = make_tools()
    tool_definitions = [t.definition for t in tools]
    conversation = [{'role': 'user', 'content': user_message}]

    print(f'[agent] starting — model={AGENT_MODEL}')

    for iteration in range(MAX_ITERATIONS):
        print(f'\n[agent] iteration {iteration + 1}/{MAX_ITERATIONS}')
        response = chat_responses(
            model=AGENT_MODEL,
            input=conversation,
            instructions=instructions,
            tools=tool_definitions,
        )

        output = response.get('output', [])
        conversation.extend(output)

        tool_calls = _extract_tool_calls(output)
        if tool_calls:
            conversation.extend(_execute_tools(tool_calls, tools))
            continue

        message = _extract_final_message(output)
        if message:
            print(f'[agent] finished: {message}')
            return message

    return 'Agent reached max iterations without finishing.'
