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

    hub_base_url: str
    openai_responses_endpoint: str = 'https://api.openai.com/v1/responses'
    openrouter_responses_endpoint: str = 'https://openrouter.ai/api/v1/responses'

    model: str = 'gpt-5-mini'
    max_iterations: int = 5
    max_output_tokens: int = 800

    sessions_dir: str = 'sessions'
    mcp_server_module_name: str = 'src.mcp.server'
    log_file: str = 'logs/app.log'
    log_level: str = 'INFO'
