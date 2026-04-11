import json

from .chat_api import chat_responses
from .config import AGENT_MODEL
from .tools import make_tools, find_tool
from .oko_service import OkoService


MAX_ITERATIONS = 40

INSTRUCTIONS = (
    'You are an agent that edits data in the OKO operations center via its API. '
    'Before doing anything else, follow these preparation steps in order: '
    '1. Call oko_execute with action="help" to learn all available commands and their exact parameters. '
    '2. Use oko_scrape to browse all available pages and read their content — '
    '   some pages may contain rules, conventions, or context that you must understand before making any changes. '
    'The system content (titles, descriptions, city names, page names) may be in Polish — '
    'search and match values as they appear, do not translate them. '
    'When you need a record ID, use oko_scrape with only a path to get the list. '
    'If you need the full content of a specific record, call oko_scrape again with the path and the ID. '
    'When making updates, send only the fields that need to change — do not rewrite or repeat existing content. '
    'When every required change is done, call oko_done to verify and finish.'
)


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


def _execute_tools(tool_calls: list[dict], tools) -> list[dict]:
    results = []
    for call in tool_calls:
        tool_name = call.get('name')
        raw_args = call.get('arguments', '{}')

        try:
            args = json.loads(raw_args)
        except json.JSONDecodeError:
            output = {'status': 'error', 'error': 'Invalid JSON arguments.'}
            results.append({
                'type': 'function_call_output',
                'call_id': call['call_id'],
                'output': json.dumps(output)
            })
            continue

        print(f'[tool] {tool_name} args={args}')
        handler = find_tool(tool_name, tools)

        if handler is None:
            output = {'status': 'error', 'error': f'Unknown tool: {tool_name}'}
        else:
            try:
                if tool_name == 'oko_execute':
                    action = args.get('action')
                    extra = {k: v for k, v in args.items() if k != 'action'}
                    output = handler(action=action, **extra)
                elif tool_name == 'oko_scrape':
                    output = handler(**args)
                else:
                    output = handler()
            except Exception as exc:
                output = {'status': 'error', 'error': str(exc)}

        print(f'[tool] {tool_name} result={output}')
        results.append({
            'type': 'function_call_output',
            'call_id': call['call_id'],
            'output': json.dumps(output, ensure_ascii=False)
        })
    return results


def run_agent(task: str, service: OkoService) -> str:
    tools = make_tools(service)
    tool_definitions = [t.definition for t in tools]

    conversation = [{'role': 'user', 'content': task}]
    print(f'[agent] starting task={task}')

    for iteration in range(MAX_ITERATIONS):
        print(f'[agent] iteration {iteration + 1}/{MAX_ITERATIONS}')

        response = chat_responses(
            model=AGENT_MODEL,
            input=conversation,
            instructions=INSTRUCTIONS,
            tools=tool_definitions,
        )

        output = response.get('output', [])
        conversation.extend(output)

        tool_calls = _extract_tool_calls(output)
        if tool_calls:
            tool_results = _execute_tools(tool_calls, tools)
            conversation.extend(tool_results)
            continue

        message = _extract_final_message(output)
        if message:
            print(f'[agent] done message={message}')
            return message

    return 'Agent reached max iterations without finishing.'
