import json
from collections.abc import Callable

from .chat_api import chat_responses
from .config import AGENT_MODEL
from .mcp_client import MCPFileSystemClient

MAX_ITERATIONS = 20

READ_FILE_TOOL = [
    {
        'type': 'function',
        'name': 'read_file',
        'description': 'Read a file from the local workspace.',
        'parameters': {
            'type': 'object',
            'properties': {
                'path': {'type': 'string', 'description': 'Path relative to workspace root.'},
            },
            'required': ['path'],
        },
    },
]


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


async def run_json_agent(
    *,
    agent_name: str,
    instructions: str,
    prompt: str,
    mcp: MCPFileSystemClient,
    root,
    postprocess: Callable[[dict], dict] | None = None,
) -> dict:
    async def read_file(path: str) -> dict:
        return await mcp.call_tool('read_file', {'path': str(root / path)})

    handlers = {'read_file': read_file}
    conversation = [{'role': 'user', 'content': prompt}]

    print(f'[{agent_name}] starting')

    for iteration in range(MAX_ITERATIONS):
        print(f'[{agent_name}] iteration {iteration + 1}')
        response = await chat_responses(
            model=AGENT_MODEL,
            input=conversation,
            instructions=instructions,
            tools=READ_FILE_TOOL,
        )

        output = response.get('output', [])
        conversation.extend(output)

        tool_calls = _extract_tool_calls(output)
        if tool_calls:
            results = []
            for call in tool_calls:
                name = call.get('name')
                args = json.loads(call.get('arguments', '{}'))
                print(f'[{agent_name}] -> {name}({json.dumps(args, ensure_ascii=False)[:200]})')
                handler = handlers.get(name)
                try:
                    result = handler(**args)
                    result = await result if hasattr(result, '__await__') else result
                except Exception as exc:
                    result = {'status': 'error', 'error': str(exc)}
                print(f'[{agent_name}] <- {name}: {json.dumps(result, ensure_ascii=False)[:300]}')
                results.append({
                    'type': 'function_call_output',
                    'call_id': call['call_id'],
                    'output': json.dumps(result, ensure_ascii=False),
                })
            conversation.extend(results)
            continue

        message = _extract_final_message(output)
        if message:
            print(f'[{agent_name}] done, parsing JSON')
            start = message.find('{')
            end = message.rfind('}') + 1
            parsed = json.loads(message[start:end])
            return postprocess(parsed) if postprocess else parsed

    raise RuntimeError(f'{agent_name} reached max iterations without finishing.')
