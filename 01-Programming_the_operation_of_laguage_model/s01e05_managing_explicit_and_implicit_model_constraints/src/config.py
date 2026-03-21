from .schemas import AgentDecision
from dotenv import load_dotenv
import os

load_dotenv()
OPENAI_API_KEY  = os.getenv('OPENAI_API_KEY')
# CHAT_MODEL      = 'gpt-4.1-nano-2025-04-14' (The model gave up after displaying the message try again in a moment, Selected only one action)
# CHAT_MODEL      = 'gpt-5.4-nano-2026-03-17' (Selected only one action low price)
# CHAT_MODEL      = 'gpt-4.1-mini-2025-04-14' (Selected few actions Higher price)
# CHAT_MODEL      = 'gpt-5-mini' (Selected few actions Higher price)
CHAT_MODEL      = 'gpt-4o-mini-2024-07-18' # (Selected few actions low price)
MAX_ITERATIONS  = 10
RESPONSE_FORMAT = {
    'format': {
        'type': 'json_schema',
        'name': 'agent_decision',
        'schema': AgentDecision.model_json_schema(),
        'strict': True,
    }
}
INSTRUCTIONS = """
You are deciding the next API step or steps.

Rules:
- Always begin by requesting the `help` action, unless the conversation already contains the API documentation returned by `help`.
- Never invent action names, argument names, argument values, or action order.
- Use only actions and parameters explicitly described in the API documentation already present in the conversation.
- Carefully analyze the latest API response before choosing the next step.
- If the latest API response contains an error, use that error to correct the next action.
- If the API response contains a flag in the format {FLG:...}, stop making API calls and return a final answer.
- You may return more than one action in `actions` when the correct next sequence is already fully determined by the API documentation or by the latest API response.
- Return multiple actions only when no additional API response is needed between them to determine the next step.
- If any uncertainty remains, return only one next action.
- Preserve the correct execution order in the `actions` list.
- If no API call is needed, set `should_call_api` to false and provide `final_answer`.
- If an API call is needed, set `should_call_api` to true and provide one or more actions.
- Return only data that matches the required response schema.
- If an action does not require arguments, return an empty arguments list.
"""


AI_DEVS_HUB_API_KEY  = os.getenv('AI_DEVS_HUB_API_KEY')
AI_DEVS_HUB_BASE_URL = os.getenv('HUB_BASE_URL')
MAX_RETRIES = 5
DEFAULT_WAIT_TIME = 1