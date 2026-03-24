from .openai_client import openai_responses
from .openrouter_client import openrouter_completions


def create_llm_client(
    provider: str,
    provider_url: str,
    api_key: str
):
    provider = provider.lower()

    def create_response(
        model: str,
        conversation: list[dict],
        instructions: str | None = None,
        response_format: dict | None = None,
        tools: list[dict] | None = None
    ):
        if provider == 'openrouter':
            return openrouter_completions(
                url=provider_url,
                api_key=api_key,
                model=model,
                conversation=conversation,
                response_format=response_format,
                tools=tools
            )

        if provider == 'openai':
            return openai_responses(
                url=provider_url,
                api_key=api_key,
                model=model,
                conversation=conversation,
                instructions=instructions,
                response_format=response_format,
                tools=tools
            )

        raise ValueError(f'Unsupported provider: {provider}')

    return create_response