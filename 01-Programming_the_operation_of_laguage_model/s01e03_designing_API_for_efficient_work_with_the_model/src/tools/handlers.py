import requests

from ..utils.logging import get_logger


logger = get_logger('TOOLS')


def check_package_status(
    packageid: str,
    base_hub_url: str,
    hub_api_key: str
) -> dict:
    check_package_url = f'{base_hub_url}/api/packages'
    logger.info('Checking package status for packageid=%s', packageid)
    response = requests.post(
        url=check_package_url,
        json={
            'apikey': hub_api_key,
            'action': 'check',
            'packageid': packageid
        }
    )
    logger.info('Package check response status code: %s', response.status_code)
    return response.json()

def redirect_package(
    packageid: str,
    destination: str,
    code: str,
    base_hub_url: str,
    hub_api_key: str
) -> dict:
    check_package_url = f'{base_hub_url}/api/packages'
    logger.info(
        'Redirecting package packageid=%s to destination=%s',
        packageid,
        destination,
    )
    response = requests.post(
        url=check_package_url,
        json={
            'apikey': hub_api_key,
            'action': 'redirect',
            'packageid': packageid,
            'destination': destination,
            'code': code
        }
    )
    logger.info('Package redirect response status code: %s', response.status_code)
    return response.json()
