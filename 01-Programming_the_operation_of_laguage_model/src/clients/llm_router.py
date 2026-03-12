from collections.abc import Callable

from .openai_client import create_openai_response
from .openrouter_client import create_openrouter_response

LlmResponseFn = Callable[
    [str, list[dict], dict | None, list[dict] | None, str | dict | None],
    dict
]


def make_llm_response_fn(
    provider: str,
    openrouter_api_key: str | None = None,
    openai_api_key: str | None = None,
    openrouter_base_url: str | None = None,
) -> LlmResponseFn:
    provider = provider.lower()

    def get_llm_response(
        model: str, 
        messages: list[dict], 
        response_format: dict | None,
        tools: list[dict] | None = None,
        tool_choice: str | dict | None = None
    ) -> dict:
        if provider == 'openrouter':
            response = create_openrouter_response(
                api_key=openrouter_api_key,
                base_url=openrouter_base_url,
                model=model,
                messages=messages,
                response_format=response_format,
                tools=tools,
                tool_choice=tool_choice
            )
        elif provider == 'openai':
            response = create_openai_response(
                api_key=openai_api_key,
                model=model,
                messages=messages,
                response_format=response_format,
                tools=tools,
                tool_choice=tool_choice
            )
        else:
            raise ValueError(f'Unsupported provider: {provider}')
        return response

    return get_llm_response
