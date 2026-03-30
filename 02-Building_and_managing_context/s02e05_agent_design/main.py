import asyncio
from pathlib import Path

from src.agent import run_agent
from src.config import Settings
from src.filesystem_client import MCPFileSystemClient
from src.hub_client import AiDevsHubClient


SYSTEM_INSTRUCTIONS = """
You are an autonomous agent solving the drone task.

Work iteratively and use tools whenever you need external information.
Read the drone documentation and the map from the workspace before sending instructions.
When reading an image, provide a precise vision_task describing exactly what must be extracted.
Do not invent API commands. Base drone instructions only on the documentation and feedback from the hub.
If the hub returns an error, use that feedback to correct the next attempt.
Do not get stuck on a single interpretation of the target if repeated feedback suggests that your current assumption is wrong.
Treat narrative hints and non-obvious clues as potentially relevant, but verify them through the map, documentation, and hub feedback rather than guessing.
When an obvious interpretation repeatedly fails, step back, reassess what the real strike point should be, and try a better-supported hypothesis.
""".strip()


TASK = """
Solve the drone task.

You have a local workspace with the relevant files stored in the `data` folder.

The map is a top-down image divided into a visible grid of sectors.
On the map you can see the power plant complex and nearby infrastructure related to water.
Your goal is to destroy the dam that holds back the water near the power plant, not the main power plant building itself.
Find the exact sector containing that dam and use it in the instructions.
The most obvious interpretation may be wrong, so do not assume the first plausible location is automatically correct.
If repeated hub feedback suggests that your target sector is wrong, revisit the map and consider whether a clue or hint points to a more specific or less literal location.
The target power plant identifier is `PWR6132PL` and this object code must be used in the drone instructions.

Your job:
1. Read the drone documentation.
2. Analyze the map carefully, count the grid sectors correctly, and identify the most defensible target sector based on visual evidence and hints.
3. Send valid instructions to the hub.
4. If the hub returns an error, correct the instructions and try again.
5. If the same interpretation keeps failing, reassess your assumptions instead of repeating the same plan.

Important:
If the hub response contains `{FLG:...}`, return it as the final answer and stop.

Use the task name `drone` when sending instructions.
""".strip()



async def async_main() -> None:
    settings = Settings()
    hub_client = AiDevsHubClient(
        api_key=settings.ai_devs_hub.api_key,
        base_url=settings.ai_devs_hub.base_url,
    )
    filesystem_client = MCPFileSystemClient(
        mcp_config_path=Path(__file__).resolve().parent / '.mcp.json',
        server_name='filesystem_main',
    )

    await filesystem_client.connect_to_server()
    try:
        result = await run_agent(
            settings=settings,
            hub_client=hub_client,
            filesystem_client=filesystem_client,
            task=TASK,
            instructions=SYSTEM_INSTRUCTIONS,
        )
        print(result)
    finally:
        await filesystem_client.cleanup()


def main() -> None:
    asyncio.run(async_main())


if __name__ == '__main__':
    main()
