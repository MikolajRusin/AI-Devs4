import httpx


def _build_image_url(base64_image: str, mime_type: str) -> str:
    return f'data:{mime_type};base64,{base64_image}'

async def run_document_ocr(base64_image: str, mime_type: str, mistral_api_key: str, mistral_url: str):
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(
            url=mistral_url,
            headers={
                'Authorization': f'Bearer {mistral_api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'mistral-ocr-latest',
                'document': {
                    'type': 'image_url',
                    'image_url': _build_image_url(base64_image, mime_type)
                }
            }
        )
    return response['pages'][0]['markdown']