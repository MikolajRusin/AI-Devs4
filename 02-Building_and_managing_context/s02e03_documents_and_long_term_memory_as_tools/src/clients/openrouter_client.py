import httpx

from ..logger import logger


async def openrouter_completions(
    url: str,
    api_key: str,
    model: str,
    conversation: list[dict],
    response_format: dict | None = None,
    tools: list[dict] | None = None
) -> dict:
    payload = {
        'model': model,
        'messages': conversation
    }
    if response_format is not None:
        payload['response_format'] = response_format
    if tools is not None:
        payload['tools'] = tools

    logger.start(
        f'OpenRouter completions request model={model} messages={len(conversation)} tools={0 if tools is None else len(tools)}'
    )
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            url=url,
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            json=payload,
            timeout=60
        )
    response.raise_for_status()
    logger.success(f'OpenRouter completions request completed status={response.status_code}')
    return response.json()
