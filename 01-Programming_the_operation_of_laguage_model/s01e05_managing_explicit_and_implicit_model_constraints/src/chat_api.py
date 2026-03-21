from .config import OPENAI_API_KEY
from typing import Any
import requests


def chat_responses(model: str, input: list[dict[str, Any]], instructions: str, response_format: dict[str, Any] | None = None) -> dict:
    response = requests.post(
        url='https://api.openai.com/v1/responses',
        headers={
            'Authorization': f'Bearer {OPENAI_API_KEY}',
            'Content-Type': 'application/json'
        },
        json={
            'model': model,
            'instructions': instructions,
            'input': input,
            'text': response_format
        }
    )
    return response.json()