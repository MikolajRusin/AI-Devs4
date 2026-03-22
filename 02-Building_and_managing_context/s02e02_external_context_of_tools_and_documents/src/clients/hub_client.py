import json
from pathlib import Path

import requests


class AiDevsHubClient:
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self.download_dir_path = Path(__file__).parents[2] / 'data' / 'raw_img'
        self.download_dir_path.mkdir(parents=True, exist_ok=True)

    def download_board_image(self, final_board: bool = False) -> str:
        if final_board:
            file_name = 'solved_electricity.png'
            url = f'{self.base_url}/i/{file_name}'
        else:
            file_name = 'electricity.png'
            url = f'{self.base_url}/data/{self.api_key}/{file_name}'
            
        response = requests.get(url)
        response.raise_for_status()

        dest_path = self.download_dir_path / file_name
        dest_path.write_bytes(response.content)
        return str(dest_path)