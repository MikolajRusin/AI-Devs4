from .openai_client import openai_responses
from .openrouter_client import openrouter_responses


def create_llm_response_client(
    provider: str,
    url: str,
    api_key: str
):
    def create_response(
        model: str,
        messages: list[dict],
        response_format: dict | None = None,
        tools: list[dict] | None = None
    ):
        if provider == 'openrouter':
            return openrouter_responses(
                url=url,
                api_key=api_key,
                model=model,
                messages=messages,
                response_format=response_format,
                tools=tools
            )

        if provider == 'openai':
            return openai_responses(
                url=url,
                api_key=api_key,
                model=model,
                messages=messages,
                response_format=response_format,
                tools=tools
            )

        raise ValueError(f'Unsupported provider: {provider}')

    return create_response