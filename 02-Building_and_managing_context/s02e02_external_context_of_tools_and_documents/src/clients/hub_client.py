import requests
from typing import Literal
from pathlib import Path


class AiDevsHubClient:
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self.download_dir_path = Path(__file__).parents[2] / 'data' / 'raw_img'
        self.download_dir_path.mkdir(parents=True, exist_ok=True)

    def download_board_image(self, board: Literal['current', 'solved'] = 'current') -> str:
        if board == 'current':
            file_name = 'electricity.png'
            url = f'{self.base_url}/data/{self.api_key}/{file_name}'
        else:
            file_name = 'solved_electricity.png'
            url = f'{self.base_url}/i/{file_name}'
            
        response = requests.get(url)
        response.raise_for_status()

        dest_path = self.download_dir_path / file_name
        dest_path.write_bytes(response.content)
        return str(dest_path)

    def rotate_cable(self, cable_code: str) -> dict:
        url = f'{self.base_url}/verify'
        response = requests.post(
            url,
            json={
                'apikey': self.api_key,
                'task': 'electricity',
                'answer': {
                    'rotate': cable_code
                }
            }
        )
        response.raise_for_status()
        return response.json()

    def reset_board(self) -> dict:
        url = f'{self.base_url}/data/{self.api_key}/electricity.png?reset=1'
        response = requests.get(
            url,
            params={'reset': '1'}
        )
        return response