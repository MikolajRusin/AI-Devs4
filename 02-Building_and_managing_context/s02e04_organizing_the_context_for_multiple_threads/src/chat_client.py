import httpx
from typing import Any
from .config import ProviderBaseSettings

async def chat_responses(provider_config: ProviderBaseSettings, model: str, input: dict[str, str], instructions: str, tools: list[dict]) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=50) as client:
        response = await client.post(
            url=provider_config.url,
            headers={
                'Authorization': f'Bearer {provider_config.api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'model': model,
                'instructions': instructions,
                'input': input,
                'tools': tools
            }
        )
    return response.json()