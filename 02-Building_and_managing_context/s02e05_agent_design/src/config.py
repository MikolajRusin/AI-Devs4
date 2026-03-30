from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class ProviderBaseSettings(BaseModel):
    api_key: str
    url: str

class OpenAISettings(ProviderBaseSettings):
    provider: str = 'OpenAI'


class OpenRouterSettings(ProviderBaseSettings):
    provider: str = 'OpenRouter'


class AiDevsHubSettings(BaseModel):
    api_key: str
    base_url: str


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )

    OPENAI_API_KEY: str
    OPENROUTER_API_KEY: str
    AI_DEVS_HUB_API_KEY: str
    HUB_BASE_URL: str

    agent_model: str = 'google/gemini-3.1-flash-lite-preview'
    max_iterations: int = 50
    max_output_tokens: int = 800

    vision_model: str = 'gpt-5.4'
    
    workspace_dir_path: str = str(Path(__file__).resolve().parent.parent / 'workspace')

    @property
    def openai(self) -> OpenAISettings:
        return OpenAISettings(
            api_key=self.OPENAI_API_KEY,
            url='https://api.openai.com/v1/responses'
        )

    @property
    def openrouter(self) -> OpenRouterSettings:
        return OpenRouterSettings(
            api_key=self.OPENROUTER_API_KEY,
            url='https://openrouter.ai/api/v1/responses'
        )

    @property
    def ai_devs_hub(self) -> AiDevsHubSettings:
        return AiDevsHubSettings(
            api_key=self.AI_DEVS_HUB_API_KEY,
            base_url=self.HUB_BASE_URL
        )