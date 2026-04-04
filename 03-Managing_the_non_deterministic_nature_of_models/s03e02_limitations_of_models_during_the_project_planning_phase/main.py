import re
import json
import time
import requests
import frontmatter
from pathlib import Path
from jinja2 import Template

from utils.config import (
    AI_DEVS_HUB_API_KEY, AI_DEVS_HUB_BASE_URL, 
    OPENAI_API_KEY, OPENROUTER_API_KEY,
    MAX_ITERATIONS, MODEL, AGENT_INSTRUCTIONS
)


TEMPLATE_PATH = Path(__file__).parent / 'classify_note_fragment_prompt_template.md'
TOOLS_DEFINITION = [
    {
        'type': 'function',
        'name': 'run_vm_command',
        'description': 'Executes a shell command inside the remote virtual machine and returns the result.',
        'parameters': {
            'type': 'object',
            'properties': {
                'cmd': {
                    'type': 'string',
                    'description': 'The shell command to execute inside the virtual machine.'
                }
            },
            'required': ['cmd'],
            'additionalProperties': False
        }
    },
    {
        'type': 'function',
        'name': 'send_password',
        'description': 'Sends the final confirmation password for the firmware task to the verification endpoint.',
        'parameters': {
            'type': 'object',
            'properties': {
                'password': {
                    'type': 'string',
                    'description': 'The confirmation password returned by the firmware after a successful start.'
                }
            },
            'required': ['password'],
            'additionalProperties': False
        }
    },
    {
        'type': 'function',
        'name': 'wait_a_moment',
        'description': 'Pauses execution for a given number of seconds and returns confirmation after waiting.',
        'parameters': {
            'type': 'object',
            'properties': {
                'seconds': {
                    'type': 'integer',
                    'description': 'Number of seconds to wait before continuing.'
                }
            },
            'required': ['seconds'],
            'additionalProperties': False
        }
    }
]

def print_section(title: str, content: str | dict):
    print(f'\n=== {title} ===')
    if isinstance(content, dict):
        print(json.dumps(content, ensure_ascii=False, indent=2))
    else:
        print(content)

def wait_a_moment(seconds: int):
    time.sleep(seconds)
    return {'status': 'ok', 'waited_seconds': seconds}

def send_password(password: str):
    response = requests.post(
        url=f'{AI_DEVS_HUB_BASE_URL}/verify',
        json={
            'apikey': AI_DEVS_HUB_API_KEY,
            'task': 'firmware',
            'answer': {
                'confirmation': password
            }
        }
    )
    return response.json()

def run_vm_command(cmd: str):
    response = requests.post(
        url=f'{AI_DEVS_HUB_BASE_URL}/api/shell',
        json={
            'apikey': AI_DEVS_HUB_API_KEY,
            'cmd': cmd
        }
    )
    return response.json()

def chat_responses(model: str, input: list[dict], instructions: str, tools: list[dict]):
    response = requests.post(
        # url='https://openrouter.ai/api/v1/responses',
        url = 'https://api.openai.com/v1/responses',
        headers={
            # 'Authorization': f'Bearer {OPENROUTER_API_KEY}',
            'Authorization': f'Bearer {OPENAI_API_KEY}',
            'Content-Type': 'application/json'
        },
        json={
            'model': model,
            'input': input,
            'instructions': instructions,
            'tools': tools
        }
    )
    response.raise_for_status()
    return response.json()

def execute_tools(tool_calls: list[dict]):
    tool_calls_info = []
    for tool_call in tool_calls:
        tool_name = tool_call.get('name')
        tool_args = json.loads(tool_call.get('arguments', '{}'))

        print_section('TOOL CALL', f'{tool_name}({tool_args})')
        if tool_name == 'run_vm_command':
            tool_results = run_vm_command(**tool_args)
            print_section('TOOL RESULT', tool_results)
        elif tool_name == 'send_password':
            tool_results = send_password(**tool_args)
            print_section('TOOL RESULT', tool_results)
        elif tool_name == 'wait_a_moment':
            tool_results = wait_a_moment(**tool_args)
            print_section('TOOL RESULT', tool_results)
        else:
            raise ValueError(f'Model provided wrong tool name: {tool_name}')

        tool_calls_info.append(
            {
                'type': 'function_call_output',
                'call_id': tool_call['call_id'],
                'output': json.dumps(tool_results, ensure_ascii=False)
            }
        )
    return tool_calls_info

def extract_output_message(output_items: list[dict]):
    for item in output_items:
        if item.get('type') == 'message':
            return item
    return None

def extract_message_text(output_message: dict):
    for content in output_message.get('content', {}):
        text = content.get('text')
        if isinstance(text, str) and text:
            return text
    return None

def run_agent(task: str):
    conversation = [
        {'role': 'user', 'content': task}
    ]

    for iteration in range(MAX_ITERATIONS):
        print_section('ITERATION', str(iteration + 1))
        chat_response = chat_responses(
            model=MODEL,
            input = conversation,
            instructions=AGENT_INSTRUCTIONS,
            tools=TOOLS_DEFINITION
        )

        if chat_response.get('error'):
            return 'The error occured while processing the request'

        output_items = chat_response.get('output', [])
        if not output_items:
            return 'Nor response received'

        tool_calls = [item for item in output_items if item.get('type') == 'function_call']
        conversation.extend(output_items)

        if tool_calls:
            tool_results = execute_tools(tool_calls)
            conversation.extend(tool_results)
            continue
        else:
            output_message = extract_output_message(output_items)
            if not output_message:
                return 'No output message was received from the model'

            message = extract_message_text(output_message)
            if not message:
                return 'No text output was received from the model'

            print_section('FINAL ANSWER', message)
            return message

    return 'Model did not return a final answer.'

def main():
    user_message = '''
Please solve this task.

You can execute commands on the virtual machine using the provided shell function. Your objective is to make the cooling system firmware start correctly, find the required password, send it, and finish the task.

The firmware is located at:
`/opt/firmware/cooler/cooler.bin`

You need to determine why it does not work, find the application password, and adjust the configuration if necessary, especially `settings.ini`, so the program can run properly.

Required workflow:
- Start with the `help` command and use only supported commands.
- First inspect only the files and directories directly related to the firmware in `/opt/firmware/cooler`.
- Read all relevant text files that may contain configuration, hints, logs, metadata, lock information, or documentation before trying passwords.
- Pay special attention to files like `settings.ini`, `.gitignore`, logs, lock files, and other text files located in or near the firmware directory.
- Do not guess passwords early.
- Only try a password when you have evidence from the inspected files that it may be correct.
- If configuration looks incorrect, fix it carefully and then run the firmware again.
- As soon as you find the correct password, call `send_password`.
- After calling `send_password`, stop immediately.

Important rules:
- Some typical Linux commands may not work, so do not assume standard Linux behavior.
- Don't use any flags, e.g. ls -la. It does not work on this system.
- Never access, inspect, list, read, or search inside `/etc`, `/root`, or `/proc`.
- Never read binary files directly.
- In particular, never use `cat` on `cooler.bin` or on any other `.bin` file.
- If you find a `.gitignore` file, read it first and treat all listed paths as forbidden.
- Work only in safe, relevant locations related to this firmware task.
- Do not explore unrelated parts of the filesystem.
- Do not repeat the same command unless the previous result gives a concrete reason.
- Avoid destructive commands and unnecessary changes.

When `send_password` returns the final value, return only that final value and nothing else.
'''



    final_result = run_agent(user_message)
    print_section('RESULT', final_result)

if __name__ == '__main__':
    main()