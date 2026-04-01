import requests
from typing import Any

from .config import OPENAI_API_KEY


def chat_responses(model: str, input: list[dict[str, Any]], instructions: str, response_format: dict[str, Any]) -> dict[str, Any]:
    response = requests.post(
        url = 'https://api.openai.com/v1/responses',
        headers={
            'Authorization': f'Bearer {OPENAI_API_KEY}',
            'Content-Type': 'application/json'
        },
        json={
            'model': model,
            'input': input,
            'instructions': instructions,
            'text': {
                'format': response_format
            }
        }
    )
    response.raise_for_status()
    return response.json()