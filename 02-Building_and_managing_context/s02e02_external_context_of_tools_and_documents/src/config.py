from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict



class OpenAISettings(BaseModel):
    api_key: str
    responses_url: str


class OpenRouterSettings(BaseModel):
    api_key: str
    responses_url: str


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

    @property
    def openai(self) -> OpenAISettings:
        return OpenAISettings(
            api_key=self.OPENAI_API_KEY,
            responses_url="https://api.openai.com/v1/responses",
        )

    @property
    def openrouter(self) -> OpenRouterSettings:
        return OpenRouterSettings(
            api_key=self.OPENROUTER_API_KEY,
            responses_url="https://openrouter.ai/api/v1/responses",
        )

    @property
    def ai_devs_hub(self) -> AiDevsHubSettings:
        return AiDevsHubSettings(
            api_key=self.AI_DEVS_HUB_API_KEY,
            base_url=self.HUB_BASE_URL,
        )