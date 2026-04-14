import requests
from typing import Any

from .config import OPENAI_API_KEY


def chat_responses(
    model: str,
    input: list[dict],
    instructions: str,
    tools: list[dict],
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
        },
    )
    response.raise_for_status()
    return response.json()


def chat_completions(
    model: str,
    system: str,
    user: str,
    response_format: dict | None = None,
) -> str:
    """Single-turn chat completions call. Returns the assistant message text."""
    body: dict[str, Any] = {
        'model': model,
        'messages': [
            {'role': 'system', 'content': system},
            {'role': 'user', 'content': user},
        ],
    }
    if response_format:
        body['response_format'] = response_format

    response = requests.post(
        'https://api.openai.com/v1/chat/completions',
        headers={
            'Authorization': f'Bearer {OPENAI_API_KEY}',
            'Content-Type': 'application/json',
        },
        json=body,
    )
    response.raise_for_status()
    return response.json()['choices'][0]['message']['content']
