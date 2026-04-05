from dotenv import load_dotenv
import os

load_dotenv()
AI_DEVS_HUB_API_KEY  = os.getenv('AI_DEVS_HUB_API_KEY')
AI_DEVS_HUB_BASE_URL = os.getenv('HUB_BASE_URL')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')

MAX_ITERATIONS = 50
# MODEL = 'anthropic/claude-sonnet-4-6'
MODEL = 'gpt-5-mini-2025-08-07'
AGENT_INSTRUCTIONS = '''
You control a robot on a board using only the `send_command` tool.

Rules:
- Think briefly and act quickly.
- Send exactly one command per tool call.
- Use only: `start`, `left`, `right`, `wait`, `reset`.
- Avoid repeating loops that do not improve the state.
- When the goal is reached and the API returns `FLG:`, stop and return only that final flag.
- Keep responses extremely short.
'''
