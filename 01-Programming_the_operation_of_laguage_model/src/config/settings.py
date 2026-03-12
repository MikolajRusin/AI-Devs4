import os
from dataclasses import dataclass


@dataclass(frozen=True)
class PeopleFilterCriteria:
    gender: str
    city: str
    min_age: int
    max_age: int


@dataclass(frozen=True)
class Settings:
    ai_devs_hub_api_key: str
    openrouter_api_key: str
    openai_api_key: str
    hub_base_url: str
    openrouter_base_url: str = 'https://openrouter.ai/api/v1'
    people_task_name: str = 'people'

    @staticmethod
    def _require_env(name: str) -> str:
        value = os.getenv(name)
        if not value:
            raise RuntimeError(f'Missing required environment variable: {name}')
        return value

    @classmethod
    def from_env(cls) -> 'Settings':
        ai_devs_hub_api_key = cls._require_env('AI_DEVS_HUB_API_KEY')
        openrouter_api_key = cls._require_env('OPENROUTER_API_KEY')
        hub_base_url = cls._require_env('HUB_BASE_URL')
        openai_api_key = cls._require_env('OPENAI_API_KEY')
        return cls(
            ai_devs_hub_api_key=ai_devs_hub_api_key,
            openrouter_api_key=openrouter_api_key,
            openai_api_key=openai_api_key,
            hub_base_url=hub_base_url
        )
