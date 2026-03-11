from pathlib import Path
import json

from ..clients.hub import AiDevsHubClient
from ..clients.openrouter_client import create_chat_completion
from ..config.settings import Settings
from ..resources.job_tags import id2job_tag
from ..tools.handlers import (
    download_people_data, filter_people, tag_jobs, get_job_tags,
    filter_people_by_job_tag_id
)
from ..tools.tools_definition import tools


class FindHimAgent:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.hub_client = AiDevsHubClient(base_url=settings.hub_base_url)
        self.data_path = Path(__file__).resolve().parents[1] / 'data'

        self.tool_registry = {
            'download_people_data': self._download_people_data,
            'filter_people': self._filter_people,
            'tag_jobs': self._tag_jobs,
            'get_job_tags': self._get_job_tags,
            'filter_people_by_job_tag_id': self._filter_people_by_job_tag_id
        }

    @staticmethod
    def _log(label: str, payload) -> None:
        print(f'\n=== {label} ===')
        if isinstance(payload, str):
            print(payload)
            return
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))

    @staticmethod
    def _latest_message(messages: list[dict]) -> dict:
        return messages[-1]

    def _download_people_data(self) -> dict:
        return download_people_data(
            hub_client=self.hub_client,
            hub_api_key=self.settings.ai_devs_hub_api_key,
            dest_dir=self.data_path
        )

    def _filter_people(self, people_data_path: str, gender: str, city: str, lower_age_bound: int, upper_age_bound: int) -> dict:
        return filter_people(
            people_data_path=people_data_path,
            gender=gender,
            city=city,
            lower_age_bound=lower_age_bound,
            upper_age_bound=upper_age_bound
        )

    def _tag_jobs(self, filtered_people_path: str) -> dict:
        return tag_jobs(
            filtered_people_path=filtered_people_path,
            openrouter_api_key=self.settings.openrouter_api_key,
            openrouter_base_url=self.settings.openrouter_base_url,
            id_to_tag=id2job_tag,
            batch_size=10
        )

    def _get_job_tags(self) -> dict:
        return get_job_tags()

    def _filter_people_by_job_tag_id(self, filtered_people_path: str, tagged_jobs_path: str, tag_id: int) -> dict:
        return filter_people_by_job_tag_id(
            filtered_people_path=filtered_people_path,
            tagged_jobs_path=tagged_jobs_path,
            tag_id=tag_id
        )

    def run(self) -> str:
        messages = [
            {
                'role': 'system',
                'content': (
                    'You are a tool-using agent. '
                    'Your job is to solve the request by calling available tools whenever a tool can perform the next step. '
                    'Treat file paths returned by tools as valid inputs for other tools. '
                    'Do not ask the user for confirmation or file access if a suitable tool already exists. '
                    'Do not claim that you cannot read files when a tool accepts a file path. '
                    'Do not invent file paths or arguments. Use only values returned by tools or explicitly given by the user. '
                    'If more work can be done with tools, continue calling tools instead of answering in natural language. '
                    'Only return a final natural-language response when no further tool call is needed.'
                ),
            },
            {
                'role': 'user',
                'content': (
                    'Find men from Grudziądz aged 20 to 40 in the people dataset and tag their jobs.'
                ),
            },
        ]

        for step in range(1, 11):
            self._log(f'STEP {step} MESSAGE_TO_MODEL', self._latest_message(messages))
            response = create_chat_completion(
                api_key=self.settings.openrouter_api_key,
                base_url=self.settings.openrouter_base_url,
                model='openai/gpt-5-mini',
                messages=messages,
                tools=tools,
            )

            message = response['choices'][0]['message']
            self._log(f'STEP {step} MODEL_RESPONSE', message)
            tool_calls = message.get('tool_calls', [])

            if not tool_calls:
                final_content = message.get('content', '')
                return final_content
            
            messages.append(message)

            for tool_call in tool_calls:
                tool_name = tool_call['function']['name']
                tool_args = json.loads(tool_call['function']['arguments'])
                self._log(f'STEP {step} TOOL_CALL', tool_name)

                tool_handler = self.tool_registry[tool_name]
                tool_result = tool_handler(**tool_args)

                messages.append(
                    {
                        'role': 'tool',
                        'tool_call_id': tool_call['id'],
                        'name': tool_name,
                        'content': json.dumps(tool_result),
                    }
                )

        raise RuntimeError('Agent exceeded max iterations')
