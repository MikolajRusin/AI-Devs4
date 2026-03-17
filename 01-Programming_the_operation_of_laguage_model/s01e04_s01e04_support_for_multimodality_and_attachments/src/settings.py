from pydantic_settings import BaseSettings, SettingsConfigDict

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
    # declaration_agent_model: str = 'gpt-4o-mini-2024-07-18'
    declaration_agent_model: str = 'gpt-5-mini'
    
    max_iterations: int = 25
    max_output_tokens: int = 800

    mistral_ocr_endpoint: str = 'https://api.mistral.ai/v1/ocr'
    mistral_ocr_model: str = 'mistral-ocr-latest'

    openrouter_responses_endpoint: str = 'https://openrouter.ai/api/v1/responses'

    data_dir_path: str = '/home/mikolaj/Desktop/Projects/Courses/AI_Devs4/01-Programming_the_operation_of_laguage_model/s01e04_s01e04_support_for_multimodality_and_attachments/data'
    mcp_config_path: str = '/home/mikolaj/Desktop/Projects/Courses/AI_Devs4/01-Programming_the_operation_of_laguage_model/s01e04_s01e04_support_for_multimodality_and_attachments/mcp.json'