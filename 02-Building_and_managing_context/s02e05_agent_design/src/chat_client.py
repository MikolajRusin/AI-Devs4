import httpx
from typing import Any
from .config import ProviderBaseSettings

async def chat_responses(
    provider_config: ProviderBaseSettings, 
    model: str, 
    input: list[dict[str, Any]], 
    instructions: str, 
    tools: list[dict] | None = None,
    response_format: dict | None = None
) -> dict[str, Any]:
    payload = {
        'model': model,
        'instructions': instructions,
        'input': input,
    }
    if tools is not None:
        payload['tools'] = tools
    if response_format is not None:
        payload['text'] = {
            'format': response_format
        }
    
    async with httpx.AsyncClient(timeout=50) as client:
        response = await client.post(
            url=provider_config.url,
            headers={
                'Authorization': f'Bearer {provider_config.api_key}',
                'Content-Type': 'application/json'
            },
            json=payload
        )
    response.raise_for_status()
    return response.json()
