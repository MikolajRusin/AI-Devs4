from src.config import AI_DEVS_HUB_API_KEY, AI_DEVS_HUB_BASE_URL
from src.hub_client import AiDevsHubClient
from src.oko_service import OkoService
from src.agent import run_agent


TASK = (
    'Edit the OKO operations center data using the available API. '
    'The system content may be in Polish — use values exactly as they appear in API responses. '
    'Perform the following changes:\n'
    '1. Find the report about the city of Skolwin and change its classification so it is about animals, not vehicles or people.\n'
    '2. Find the task related to Skolwin, mark it as done, and update its content to say that animals (e.g. beavers) were seen there.\n'
    '3. Add a new incident report about detected human movement near the city of Komarowo.\n'
    '4. When all changes are done, call oko_done to finish.'
    '5. Return the FLG: that you received in response.'
)


def main():
    client = AiDevsHubClient(
        api_key=AI_DEVS_HUB_API_KEY,
        base_url=AI_DEVS_HUB_BASE_URL,
    )
    service = OkoService(client)
    result = run_agent(TASK, service)
    print(f'\n[main] result={result}')


if __name__ == '__main__':
    main()