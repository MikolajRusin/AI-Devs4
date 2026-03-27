from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict



class OpenAISettings(BaseModel):
    api_key: str
    responses_url: str
    provider: str = 'OpenAI'


class OpenRouterSettings(BaseModel):
    api_key: str
    completions_url: str
    provider: str = 'OpenRouter'


class AiDevsHubSettings(BaseModel):
    api_key: str
    base_url: str


class BoardSettings(BaseModel):
    x_min: int
    y_min: int
    width: int = 290
    height: int = 290


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

    agent_model: str = 'gpt-5-mini'
    max_iterations: int = 25
    max_output_tokens: int = 800

    current_board: BoardSettings = BoardSettings(
        x_min=236,
        y_min=97,
    )
    solved_board: BoardSettings = BoardSettings(
        x_min=140,
        y_min=88,
    )
    
    workspace_dir_path: str = '/home/mikolaj/Desktop/Projects/Courses/AI_Devs4/02-Building_and_managing_context/s02e03_documents_and_long_term_memory_as_tools/workspace'

    @property
    def openai(self) -> OpenAISettings:
        return OpenAISettings(
            api_key=self.OPENAI_API_KEY,
            responses_url='https://api.openai.com/v1/responses',
        )

    @property
    def openrouter(self) -> OpenRouterSettings:
        return OpenRouterSettings(
            api_key=self.OPENROUTER_API_KEY,
            completions_url='https://openrouter.ai/api/v1/chat/completions',
        )

    @property
    def ai_devs_hub(self) -> AiDevsHubSettings:
        return AiDevsHubSettings(
            api_key=self.AI_DEVS_HUB_API_KEY,
            base_url=self.HUB_BASE_URL,
        )