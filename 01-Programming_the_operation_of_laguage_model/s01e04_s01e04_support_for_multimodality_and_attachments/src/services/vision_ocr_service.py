from ..utils.logger import logger
import httpx


def _build_image_url(base64_image: str, mime_type: str) -> str:
    return f'data:{mime_type};base64,{base64_image}'

async def run_document_ocr(
    base64_image: str,
    mime_type: str,
    mistral_api_key: str,
    mistral_ocr_endpoint: str,
    mistral_ocr_model: str
) -> dict[str, str]:
    logger.vision('Extracting text from image')
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(
            url=mistral_ocr_endpoint,
            headers={
                'Authorization': f'Bearer {mistral_api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'model': mistral_ocr_model,
                'document': {
                    'type': 'image_url',
                    'image_url': _build_image_url(base64_image, mime_type)
                }
            }
        )
        logger.info(f'Document OCR response status code: {response.status_code}')
        response.raise_for_status()

    data = response.json()
    return {
        'markdown': data['pages'][0]['markdown']
    }
