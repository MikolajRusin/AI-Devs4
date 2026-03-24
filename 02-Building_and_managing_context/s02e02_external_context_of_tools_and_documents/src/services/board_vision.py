def _build_conversation(system_prompt: str, query: str, image_url: str) -> list[dict]:
    return [
        {
            'role': 'system',
            'content': [
                {'type': 'text', 'text': system_prompt}
            ]
        },
        {
            'role': 'user',
            'content': [
                {'type': 'text', 'text': query},
                {'type': 'image_url', 'image_url': {'url': image_url}}
            ]
        }
    ]

def build_image_url(image_base64: str, mime_type: str) -> str:
    return f'data:{mime_type};base64,{image_base64}'

def run_vision(
    image_url: str,
    query: str, 
    system_prompt: str, 
    llm_response_client,
    model: str,
    response_format: str | None = None
) -> dict:
    responses = llm_response_client(
        model=model,
        conversation=_build_conversation(system_prompt, query, image_url),
        response_format=response_format
    )
    return responses