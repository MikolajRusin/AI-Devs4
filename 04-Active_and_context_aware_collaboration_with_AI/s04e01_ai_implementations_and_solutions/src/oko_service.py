from .hub_client import AiDevsHubClient


class OkoService:
    def __init__(self, client: AiDevsHubClient):
        self.client = client

    def execute(self, action: str, **kwargs) -> dict:
        return self.client.oko_action(action, **kwargs)

    def done(self) -> dict:
        return self.client.oko_done()
