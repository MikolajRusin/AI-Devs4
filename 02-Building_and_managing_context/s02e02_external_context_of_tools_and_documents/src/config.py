import os
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


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

    ai_devs_hub_api_key: str
    openrouter_api_key: str
    openai_api_key: str
    mistral_api_key: str

    hub_base_url: str
    openrouter_base_url: str = 'https://openrouter.ai/api/v1'

    openai_responses_endpoint: str = 'https://api.openai.com/v1/responses'
    
    max_iterations: int = 25
    max_output_tokens: int = 800

    openrouter_responses_endpoint: str = 'https://openrouter.ai/api/v1/responses'

    current_board: BoardSettings = BoardSettings(
        x_min=236,
        y_min=97
    )
    solved_board: BoardSettings = BoardSettings(
        x_min=140,
        y_min=88
    )