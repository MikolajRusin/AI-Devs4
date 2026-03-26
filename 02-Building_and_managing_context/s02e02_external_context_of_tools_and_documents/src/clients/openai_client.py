import requests


def openai_responses(
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
    
    response = requests.post(
        url=url,
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        },
        json=payload,
        timeout=60
    )
    response.raise_for_status()
    return response.json()