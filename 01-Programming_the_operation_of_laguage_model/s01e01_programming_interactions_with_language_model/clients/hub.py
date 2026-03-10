from pathlib import Path
import requests


class AiDevsHubClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip('/')

    def download_people_data(self, api_key: str, destination: Path) -> Path:
        url = f'{self.base_url}/data/{api_key}/people.csv'
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(response.content)
        return destination

    def verify_people_answer(self, api_key: str, task_name: str, answer: list[dict]) -> dict:
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
