from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='../../.env',
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
    openrouter_responses_endpoint: str = 'https://openrouter.ai/api/v1/responses'
    mistral_ocr_endpoint: str = 'https://api.mistral.ai/v1/ocr'