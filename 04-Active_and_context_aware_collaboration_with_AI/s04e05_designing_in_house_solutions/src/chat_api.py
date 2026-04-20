import asyncio
from typing import Any

import requests

from .config import OPENAI_API_KEY


async def chat_responses(
    model: str,
    input: list[dict],
    instructions: str,
    tools: list[dict],
) -> dict[str, Any]:
    def _post() -> dict[str, Any]:
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
            timeout=60,
        )
        response.raise_for_status()
        return response.json()

    return await asyncio.to_thread(_post)
