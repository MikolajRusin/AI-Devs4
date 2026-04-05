import json
import time
import requests
from pathlib import Path

from utils.config import (
    AI_DEVS_HUB_API_KEY, AI_DEVS_HUB_BASE_URL, 
    OPENAI_API_KEY, OPENROUTER_API_KEY,
    MAX_ITERATIONS, MODEL, AGENT_INSTRUCTIONS
)


TEMPLATE_PATH = Path(__file__).parent / 'classify_note_fragment_prompt_template.md'
TOOLS_DEFINITION = [
    {
        'type': 'function',
        'name': 'send_command',
        'description': 'Send command to the robot.',
        'parameters': {
            'type': 'object',
            'properties': {
                'command': {
                    'type': 'string',
                    'description': 'The command for the robot.'
                }
            },
            'required': ['command'],
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

def send_command(command: str):
    response = requests.post(
        url=f'{AI_DEVS_HUB_BASE_URL}/verify',
        json={
            'apikey': AI_DEVS_HUB_API_KEY,
            'task': 'reactor',
            'answer': {
                'command': command
            }
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
        if tool_name == 'send_command':
            tool_results = send_command(**tool_args)
            # print_section('TOOL RESULT', tool_results)
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
            return 'No response received'

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

Your task is to give commands to the robot so that it moves from point P to point G.

<description>
The game is played on a **board** consisting of 7 columns and 5 rows. The *board* contains the following points:
- *P* -> Actual robot position.
- *G* -> The final position the robot must reach.
- *B* -> Reactor blocks.
- *.* -> These are empty fields the robot can move through.

The reactor blocks *B* can only move up or down. When it reaches its highest point, it begins to go back down, and when it reaches its lowest point, it goes back up. Their position and direction are provided in the **blocks** section. One reactor block consists of 2 points *B* (top_row and bottorm_row).
</description>

<sections>
- **board** -> The visual position of each point on the board.
- **player** -> The actual position of point *P* (robot).
- **goal** -> The final position the point *P* (robot) must reach.
- **blocks** -> The list of current positions of the reactor blocks *B* and their directions.
</sections>

<commands>
- `start` -> Start the task.
- `reset` -> Reset the board.
- `left` -> Robot to the left.
- `right` -> Robot to the right.
- `wait` -> Stay in the same position and wait the turn. 
</commands>

<task>
Move the robot to the final point **G** and do not let the reactor blocks end up in the same place as the robot. The blocks only move when you give them a command. If you want the board state to change without moving the robot, send the `wait` command.
If you manage to reach the final point, you will get the flag FLG: that you need to return in the message.
</task>
'''



    final_result = run_agent(user_message)
    print_section('RESULT', final_result)

if __name__ == '__main__':
    main()


#     user_message = '''
# Please solve this task.

# Your task is to give commands to the robot so that it moves from point P to point G.

# <description>
# The game is played on a **board** consisting of 7 columns and 5 rows. The *board* contains the following points:
# - *P* -> Actual robot position.
# - *G* -> The final position the robot must reach.
# - *B* -> Reactor blocks.
# - *.* -> These are empty fields the robot can move through.

# The reactor blocks *B* can only move up or down. When it reaches its highest point, it begins to go back down, and when it reaches its lowest point, it goes back up. Their position and direction are provided in the **blocks** section. One reactor block consists of 2 points *B* (top_row and bottorm_row).
# </description>

# <sections>
# - **board** -> The visual position of each point on the board.
# - **player** -> The actual position of point *P* (robot).
# - **goal** -> The final position the point *P* (robot) must reach.
# - **blocks** -> The list of current positions of the reactor blocks *B* and their directions.
# </sections>

# <commands>
# - `start` -> Start the task.
# - `reset` -> Reset the board.
# - `left` -> Robot to the left.
# - `right` -> Robot to the right.
# - `wait` -> Stay in the same position and wait the turn. 
# </commands>

# <task>
# Move the robot to the final point **G** and do not touch the reactor blocks. The blocks only move when you give them a command. If you want the board state to change without moving the robot, send the `wait` command.
# If you manage to reach the final point, you will get the flag FLG: that you need to return in the message.
# </task>
# '''