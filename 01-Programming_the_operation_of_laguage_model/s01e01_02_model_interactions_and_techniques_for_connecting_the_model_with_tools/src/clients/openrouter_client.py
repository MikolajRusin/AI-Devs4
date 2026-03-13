import requests


def create_openrouter_response(
    api_key: str,
    base_url: str,
    model: str,
    messages: list[dict],
    response_format: dict | None = None,
    tools: list[dict] | None = None,
    tool_choice: str | dict | None = None
) -> dict:
    payload = {
        'model': model,
        'messages': messages,
    }
    if response_format is not None:
        payload['response_format'] = response_format
    if tools is not None:
        payload['tools'] = tools
    if tool_choice is not None:
        payload['tool_choice'] = tool_choice

    response = requests.post(
        f"{base_url.rstrip('/')}/chat/completions",
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        },
        json=payload,
        timeout=60,
    )
    response.raise_for_status()

    return response.json()
