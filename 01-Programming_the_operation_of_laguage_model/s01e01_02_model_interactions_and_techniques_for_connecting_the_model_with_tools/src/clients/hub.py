from pathlib import Path
from typing import Any
import requests


class AiDevsHubClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip('/')

    @staticmethod
    def _fetch_data(url: str, method: str = 'GET', payload: dict = None) -> Any:
        if method == 'GET':
            response = requests.get(url, timeout=30)
        elif method == 'POST':
            response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        return response

    @staticmethod
    def _save_data(data, destination_path: str | Path) -> str:
        destination = Path(destination_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        return str(destination)

    def download_people_data(self, api_key: str, dest_dir: str | Path) -> str:
        url = f'{self.base_url}/data/{api_key}/people.csv'
        response = self._fetch_data(url, method='GET')
        dest_path = Path(dest_dir) / 'people.csv'
        dest_path = self._save_data(response.content, dest_path)
        return str(dest_path)

    def download_power_plant_data(self, api_key: str, dest_dir: str | Path) -> str:
        url = f'{self.base_url}/data/{api_key}/findhim_locations.json'
        response = self._fetch_data(url, method='GET')
        dest_path = Path(dest_dir) / 'findhim_locations.json'
        dest_path = self._save_data(response.content, dest_path)
        return str(dest_path)

    def get_person_locations(self, api_key: str, name: str, surname: str) -> list[dict[str, float]]:
        url = f'{self.base_url}/api/location'
        payload = {
            'apikey': api_key,
            'name': name,
            'surname': surname
        }
        response = self._fetch_data(url, method='POST', payload=payload)
        return response.json()

    def get_person_access_level(self, api_key: str, name: str, surname: str, birth_year: int):
        url = f'{self.base_url}/api/accesslevel'
        payload = {
            'apikey': api_key,
            'name': name,
            'surname': surname,
            'birthYear': birth_year
        }
        response = self._fetch_data(url, method='POST', payload=payload)
        return response.json()

    def verify_answer(self, api_key: str, task_name: str, answer: list[dict]) -> dict:
        response = requests.post(
            f'{self.base_url}/verify',
            json={
                'apikey': api_key,
                'task': task_name,
                'answer': answer,
            },
            timeout=30,
        )
        response.raise_for_status()
        return response.json()      
