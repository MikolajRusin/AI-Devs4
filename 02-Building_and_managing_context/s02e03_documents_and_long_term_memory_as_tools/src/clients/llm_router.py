from .openai_client import openai_responses
from .openrouter_client import openrouter_completions
from ..logger import logger


def create_llm_client(
    provider: str,
    provider_url: str,
    api_key: str
):
    provider = provider.lower()
    logger.info(f'Creating LLM client for provider={provider}')

    async def create_response(
        model: str,
        conversation: list[dict],
        instructions: str | None = None,
        response_format: dict | None = None,
        tools: list[dict] | None = None
    ):
        logger.agent(
            'Dispatching LLM request',
            {
                'provider': provider,
                'model': model,
                'conversation_items': len(conversation),
                'tools': 0 if tools is None else len(tools)
            }
        )
        if provider == 'openrouter':
            return await openrouter_completions(
                url=provider_url,
                api_key=api_key,
                model=model,
                conversation=conversation,
                response_format=response_format,
                tools=tools
            )

        if provider == 'openai':
            return await openai_responses(
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
