import requests
from typing import Any

from .config import OPENAI_API_KEY

def chat_responses(
    model: str,
    input: list[dict],
    instructions: str,
    tools: list[dict]
) -> dict[str, Any]:
    response = requests.post(
        'https://api.openai.com/v1/responses',
        headers={
            'Authorization': f'Bearer {OPENAI_API_KEY}',
            'Content-Type': 'application/json',
        },
        json={
            'model': model,
            'input': input,
            'instructions': instructions,
            'tools': tools,
        }
    )
    response.raise_for_status()
    return response.json()
