from .config import AI_DEVS_HUB_API_KEY, AI_DEVS_HUB_BASE_URL, DEFAULT_WAIT_TIME, MAX_RETRIES
from .schemas import RequestsLimitations, RailwayApiResponse
from .logger import logger
import requests
import time


def _send_hub_request(action: str, arguments: dict) -> RailwayApiResponse:
    response = requests.post(
        url=f"{AI_DEVS_HUB_BASE_URL}/verify",
        json={
            'apikey': AI_DEVS_HUB_API_KEY,
            'task': 'railway',
            'answer': {
                'action': action,
                **arguments
            }
        },
        timeout=30
    )

    normalized_headers = {k.lower(): v for k, v in response.headers.items()}
    limitations = RequestsLimitations.model_validate(normalized_headers)

    try:
        body = response.json()
    except ValueError:
        body = None

    return RailwayApiResponse(
        status_code=response.status_code,
        body=body,
        limitations=limitations,
    )

def _get_wait_time(response: RailwayApiResponse) -> float | None:
    if response.status_code == 503:
        return float(response.limitations.retry_after or DEFAULT_WAIT_TIME)

    if response.limitations.x_rate_limit_remaining == 0:
        return float(response.limitations.retry_after or DEFAULT_WAIT_TIME)

    return None

def hub_response(action: str, arguments: dict, max_retries: int = MAX_RETRIES) -> RailwayApiResponse:
    response: RailwayApiResponse | None = None

    for attempt in range(max_retries):
        logger.info(f'Hub request attempt {attempt}/{max_retries} for action: {action}')
        response = _send_hub_request(action, arguments)
        logger.info(f'Hub response: {response.model_dump_json()}')

        wait_time = _get_wait_time(response)
        if wait_time:
            logger.warn(f'Hub request for action "{action}" requires waiting {wait_time} seconds before retry.')
            time.sleep(wait_time)
            logger.warn(f'Restarting request.')
            continue

        return response 
        
    logger.warn(f'Max retries reached for action: {action}')
    return response