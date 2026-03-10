import json
import requests

from ..prompts.tag_jobs import build_tag_jobs_prompt


class JobTagger:
    def __init__(
        self,
        api_key: str,
        base_url: str,
        id_to_tag: dict[int, dict[str, str]],
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.id_to_tag = id_to_tag

    def tag_jobs(self, id_to_job_description: dict[int, str]) -> dict[str, list[str]]:
        prompt_data = build_tag_jobs_prompt(id_to_job_description, self.id_to_tag)
        response = requests.post(
            f'{self.base_url}/chat/completions',
            headers={
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
            },
            json={
                'model': prompt_data['metadata']['model_config']['model'],
                'messages': [
                    {'role': 'system', 'content': prompt_data['system_message']},
                    {'role': 'user', 'content': prompt_data['user_message']},
                ],
                'response_format': prompt_data['metadata']['response_format'],
            },
            timeout=60,
        )
        response.raise_for_status()

        payload = response.json()
        content = payload['choices'][0]['message']['content']
        parsed = json.loads(content)
        return parsed['tagged_jobs']
