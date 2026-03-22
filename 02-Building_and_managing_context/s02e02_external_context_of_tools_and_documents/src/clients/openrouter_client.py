import requests


def openrouter_responses(
    url: str,
    api_key: str,
    model: str,
    messages: list[dict],
    response_format: dict | None = None,
    tools: list[dict] | None = None
) -> dict:
    payload = {
        'model': model,
        'messages': messages
    }
    if response_format is not None:
        payload['response_format'] = response_format
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