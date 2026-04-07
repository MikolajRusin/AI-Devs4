import requests
from .config import OPENAI_API_KEY


def chat_responses(
    model: str,
    input: list[dict] | str,
    instructions: str,
    tools: list[dict] | None = None,
    response_format: dict | None = None,
    timeout: int = 8,
):
    print(f"[openai] model={model}")
    payload = {
        'model': model,
        'input': input,
        'instructions': instructions,
    }
    if tools is not None:
        payload['tools'] = tools
    if response_format is not None:
        payload['text'] = {
            'format': response_format
        }

    response = requests.post(
        url='https://api.openai.com/v1/responses',
        headers={
            'Authorization': f'Bearer {OPENAI_API_KEY}',
            'Content-Type': 'application/json'
        },
        json=payload,
        timeout=timeout,
    )
    print(f"[openai] status={response.status_code}")
    response.raise_for_status()
    return response.json()


def extract_response_text(response: dict) -> str:
    if response.get('output_text'):
        return response['output_text']

    output_parts: list[str] = []
    for item in response.get('output', []):
        for content in item.get('content', []):
            text_value = content.get('text')
            if text_value:
                output_parts.append(text_value)
    return ''.join(output_parts).strip()
