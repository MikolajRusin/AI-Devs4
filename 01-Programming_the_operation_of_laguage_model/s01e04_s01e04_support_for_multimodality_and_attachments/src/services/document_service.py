from ..clients.hub_client import AiDevsHubClient
from typing import Any


async def download_document(doc_name: str, hub_client: AiDevsHubClient) -> str:
    return await hub_client.download_data(doc_name)

async def send_answer(task_name: str, declaration: str, hub_client: AiDevsHubClient) -> dict[str, Any]:
    return await hub_client.verify_answer(task_name, declaration)
