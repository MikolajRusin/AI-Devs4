from .chat_client import chat_responses


SYSTEM_INSTRUCTIONS = """
You are a precise visual analysis assistant.

Analyze the provided image carefully and answer only on the basis of visible evidence.
Pay close attention to spatial layout, relative position, counting, boundaries, labels, and small visual details.
Do not guess when the image is ambiguous. If something is uncertain, say so briefly and stay grounded in what is actually visible.
Return results in the exact format requested by the task or response schema.
""".strip()


def _build_conversation(query: str, image_url: str) -> list[dict]:
    return [
        {
            'role': 'user',
            'content': [
                {'type': 'input_text', 'text': query},
                {'type': 'input_image', 'image_url': image_url}
            ]
        }
    ]


def build_image_url(image_base64: str, mime_type: str) -> str:
    return f"data:{mime_type};base64,{image_base64}"


def extract_response_text(response: dict) -> str:
    output_text = response.get('output_text')
    if isinstance(output_text, str) and output_text:
        return output_text

    for item in response.get('output', []):
        for content in item.get('content', []):
            text = content.get('text')
            if isinstance(text, str) and text:
                return text
    return ''


async def run_vision(
    image_url: str,
    query: str,
    provider_config,
    model: str,
    response_format: str | None = None,
) -> str:
    responses = await chat_responses(
        provider_config,
        model=model,
        input=_build_conversation(query, image_url),
        instructions=SYSTEM_INSTRUCTIONS,
        response_format=response_format,
    )
    text = extract_response_text(response=responses)
    return text
