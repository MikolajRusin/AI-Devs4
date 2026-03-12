from openai import OpenAI


def create_openai_response(
    api_key: str,
    model: str,
    messages: list[dict],
    response_format: dict | None = None,
    tools: list[dict] | None = None,
    tool_choice: str | dict | None = None,
) -> dict:
    client = OpenAI(api_key=api_key)

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

    response = client.chat.completions.create(**payload)
    return response.model_dump()
