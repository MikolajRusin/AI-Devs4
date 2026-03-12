from pathlib import Path
import json

from ..clients.hub import AiDevsHubClient
from ..clients.llm_router import make_llm_response_fn
from ..config.settings import Settings
from ..resources.job_tags import id2job_tag
from ..tools.handlers import (
    download_people_data, filter_people, tag_jobs, get_job_tags,
    filter_people_by_job_tag_id, download_power_plant_locations,
    identify_power_plant_suspect, get_access_level, send_message
)
from ..tools.tools_definition import tools


class FindHimAgent:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.hub_client = AiDevsHubClient(base_url=settings.hub_base_url)
        self.data_path = Path(__file__).resolve().parents[1] / 'data'
        self.create_agent_response = make_llm_response_fn(
            provider='openai',
            openai_api_key=settings.openai_api_key,
        )
        self.get_openrouter_llm_response = make_llm_response_fn(
            provider='openrouter',
            openrouter_api_key=settings.openrouter_api_key,
            openrouter_base_url=settings.openrouter_base_url,
        )
        self.get_openai_llm_response = make_llm_response_fn(
            provider='openai',
            openai_api_key=settings.openai_api_key,
        )

        self.tool_registry = {
            'download_people_data': self._download_people_data,
            'filter_people': self._filter_people,
            'tag_jobs': self._tag_jobs,
            'get_job_tags': self._get_job_tags,
            'filter_people_by_job_tag_id': self._filter_people_by_job_tag_id,
            'download_power_plant_locations': self._download_power_plant_locations,
            'identify_power_plant_suspect': self._identify_power_plant_suspect,
            'get_access_level': self._get_access_level,
            'send_message': self._send_message
        }

    @staticmethod
    def _log_message(role: str, content: str) -> None:
        print(f'\n{role}: {content}')

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
            get_llm_response=self.get_openai_llm_response,
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

    def _download_power_plant_locations(self) -> dict:
        return download_power_plant_locations(
            hub_client=self.hub_client,
            hub_api_key=self.settings.ai_devs_hub_api_key,
            get_llm_response=self.get_openai_llm_response,
            dest_dir=self.data_path
        )

    def _identify_power_plant_suspect(self, power_plant_data_path: str, filtered_people_path: str) -> dict:
        return identify_power_plant_suspect(
            power_plant_data_path=power_plant_data_path,
            filtered_people_path=filtered_people_path,
            hub_client=self.hub_client,
            hub_api_key=self.settings.ai_devs_hub_api_key
        )

    def _get_access_level(self, name: str, surname: str, birth_year: int) -> dict:
        return get_access_level(
            name=name,
            surname=surname,
            birth_year=birth_year,
            hub_client=self.hub_client,
            hub_api_key=self.settings.ai_devs_hub_api_key
        )

    def _send_message(self, name: str, surname: str, access_level: int, power_plant_code: str, message_header: str) -> dict:
        return send_message(
            name=name,
            surname=surname,
            access_level=access_level,
            power_plant_code=power_plant_code,
            message_header=message_header,
            hub_client=self.hub_client,
            hub_api_key=self.settings.ai_devs_hub_api_key
        )

    def run(self, user_prompt: str) -> str:
        messages = [
            {
                'role': 'system',
                'content': (
                    'You are a tool-using agent. '
                    'Your job is to complete the investigation by calling available tools whenever a tool can perform the next step. '
                    'Treat file paths returned by tools as valid inputs for other tools. '
                    'Do not ask the user for confirmation or file access if a suitable tool already exists. '
                    'Do not claim that you cannot read files when a tool accepts a file path. '
                    'Do not invent file paths or arguments. Use only values returned by tools or explicitly given by the user. '
                    'Do not stop at intermediate results such as filtered people lists or job tags if later tools are still relevant to the task. '
                    'Before each tool call, write a short assistant message that states what you have found so far and what you will do next. '
                    'Keep these progress messages brief and concrete. '
                    'When you identify the suspect, obtain the access level and send the final message with the suspect data. '
                    'If more work can be done with tools, continue calling tools instead of answering in natural language. '
                    'Only return a final natural-language response when no further tool call is needed.'
                ),
            },
            {
                'role': 'user',
                'content': user_prompt,
            },
        ]
        self._log_message('USER', messages[-1]['content'])

<<<<<<< HEAD
        for step in range(1, 11):
=======
        for _ in range(12):
>>>>>>> s01e02-techniques-for-connecting-the-model-with-tools
            response = self.create_agent_response(
                model='gpt-5-mini',
                messages=messages,
                response_format=None,
                tools=tools,
            )

            message = response['choices'][0]['message']
            if message.get('content'):
                self._log_message('AGENT', message['content'])
            tool_calls = message.get('tool_calls', [])

            if not tool_calls:
                final_content = message.get('content', '')
                return final_content
            
            messages.append(message)

            for tool_call in tool_calls:
                tool_name = tool_call['function']['name']
                tool_args = json.loads(tool_call['function']['arguments'])

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
