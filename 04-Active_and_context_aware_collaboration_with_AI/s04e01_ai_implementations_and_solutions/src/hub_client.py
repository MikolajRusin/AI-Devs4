import requests


class AiDevsHubClient:
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url

    def oko_action(self, action: str, **kwargs) -> dict:
        url = f'{self.base_url}/verify'
        response = requests.post(
            url,
            json={
                'apikey': self.api_key,
                'task': 'okoeditor',
                'answer': {
                    'action': action,
                    **kwargs
                }
            }
        )
        response.raise_for_status()
        return response.json()

    def oko_done(self) -> dict:
        return self.oko_action('done')
