from src.config import Settings
from src.clients.hub_client import AiDevsHubClient
from src.agents.electricity_agent import ElectricityAgent

def main():
    settings = Settings()
    hub_client = AiDevsHubClient(
        **settings.ai_devs_hub.model_dump()
    )
    electricity_agent = ElectricityAgent(
        settings=settings,
        hub_client=hub_client
    )

    user_message = """
Solve task `electricity`.

Your goal is to transform the current 3x3 board into the solved board by rotating tiles clockwise.

Important task rules:
- The current board and the solved board may differ on multiple cells.
- Rotate only the current board.
- Each rotation rotates exactly one tile by 90 degrees clockwise.
- Use the minimum reasonable number of rotations.
- If a full-board read is uncertain for any cell, inspect that specific tile before rotating it.
- Re-check the board when needed after rotations.

Completion condition:
- Finish only when the board is solved and the final response from the hub confirms success.

Return only the final flag.
    """
    electricity_agent.run_agent(user_message)

if __name__ == '__main__':
    main()
