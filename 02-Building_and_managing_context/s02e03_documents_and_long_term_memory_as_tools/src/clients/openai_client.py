import httpx

from ..logger import logger


async def openai_responses(
    url: str,
    api_key: str,
    model: str,
    conversation: list[dict],
    instructions: str | None = None,
    response_format: dict | None = None,
    tools: list[dict] | None = None
) -> dict:
    payload = {
        'model': model,
        'input': conversation
    }
    if instructions is not None:
        payload['instructions'] = instructions
    if response_format is not None:
        payload['text'] = {
            'format': response_format
        }
    if tools is not None:
        payload['tools'] = tools

    logger.start(
        f'OpenAI responses request model={model} input_items={len(conversation)} tools={0 if tools is None else len(tools)}'
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
    if response.status_code >= 400:
        logger.error('OpenAI responses request failed', response.text)
    response.raise_for_status()
    logger.success(f'OpenAI responses request completed status={response.status_code}')
    return response.json()
