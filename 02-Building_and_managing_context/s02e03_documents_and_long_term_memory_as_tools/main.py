import asyncio
from pathlib import Path

from src.agents.main_agent import MainAgent
from src.agents.log_search_agent import LogSearchAgent
from src.clients.hub_client import AiDevsHubClient
from src.clients.llm_router import create_llm_client
from src.mcp.filesystem_client import MCPFileSystemClient
from src.config import Settings
from src.logger import logger

APP_ROOT = Path(__file__).parent
WORKSPACE_DIR_PATH = APP_ROOT / 'workspace'

LOGS_DIR_PATH = WORKSPACE_DIR_PATH / 'logs'
LOGS_DIR_PATH.mkdir(parents=True, exist_ok=True)

AGENTS_DIR_PATH = WORKSPACE_DIR_PATH / 'agents'
LOG_SEARCH_AGENT_DIR_PATH = AGENTS_DIR_PATH / 'log_search_agent'
LOG_SEARCH_AGENT_DIR_PATH.mkdir(parents=True, exist_ok=True)

RESULTS_DIR_PATH = WORKSPACE_DIR_PATH / 'results'
RESULTS_DIR_PATH.mkdir(parents=True, exist_ok=True)

async def main():
    logger.start('Initializing application')
    settings = Settings()
    logger.info(f'Workspace directory: {WORKSPACE_DIR_PATH}')
    hub_client = AiDevsHubClient(
        api_key=settings.ai_devs_hub.api_key,
        base_url=settings.ai_devs_hub.base_url,
        workspace_dir_path=WORKSPACE_DIR_PATH
    )

    main_fs_client = MCPFileSystemClient(
        mcp_config_path=str(APP_ROOT / '.mcp.json'),
        server_name='filesystem_main'
    )
    logs_fs_client = MCPFileSystemClient(
        mcp_config_path=str(APP_ROOT / '.mcp.json'),
        server_name='filesystem_logs'
    )

    openai_client = create_llm_client(
        provider=settings.openai.provider,
        api_key=settings.openai.api_key,
        provider_url=settings.openai.responses_url
    )
    logger.info('Clients initialized successfully')

    log_search_agent = LogSearchAgent(
        hub_client=hub_client,
        filesystem_client=logs_fs_client,
        agent_client=openai_client,
        model=settings.agent_model,
        max_iterations=10
    )
    main_agent = MainAgent(
        hub_client=hub_client,
        filesystem_client=main_fs_client,
        agent_client=openai_client,
        model=settings.agent_model,
        log_search_agent=log_search_agent,
        max_iterations=50
    )
    logger.success('Agents initialized successfully')

    user_message = """
Solve the failure task.

We need to prepare a condensed version of the system logs from the power plant failure day.
The final result must contain only events relevant to failure analysis, especially around:
- power and electrical systems,
- cooling systems,
- water pumps and coolant flow,
- software, control systems, interlocks, trips, and shutdown-related behavior,
- other important plant subsystems directly related to the outage.

Important requirements:
- the final condensed logs must fit within 1500 tokens,
- keep multiline format,
- one event per line,
- preserve timestamp, severity level, and subsystem identifier,
- you may shorten or paraphrase messages as long as key technical information remains intact.

Do not start from broad or low-value exploration.
Begin with the most critical failure-related evidence that is most likely to explain the outage.
"""

    results = await main_agent.run(user_message)
    logger.response(f'Main result | {results}')

if __name__ == '__main__':
    asyncio.run(main())
