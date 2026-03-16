from ..clients.hub_client import AiDevsHubClient

async def download_document(doc_name: str, hub_client: AiDevsHubClient) -> str:
    return await hub_client.download_data(doc_name)
