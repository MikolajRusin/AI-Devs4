from ..clients.llm_router import create_llm_response_client


class BoardVisionService:
    def __init__(self, provider: str, provider_url: str, api_key: str, model: str):
        self.model = model
        self.llm_client = create_llm_response_client(
            provider=provider,
            url=provider_url,
            api_key=api_key
        )

    