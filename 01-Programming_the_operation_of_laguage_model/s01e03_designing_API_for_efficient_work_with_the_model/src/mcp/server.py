from src.utils.logging import setup_logging
from src.tools.handlers import check_package_status, redirect_package
from src.config.settings import Settings
from mcp.server.fastmcp import FastMCP

settings = Settings()
mcp_server_logger = setup_logging(
    level=settings.log_level,
    logger_name='MCP_SERVER',
    log_file=settings.log_file,
)
tool_logger = setup_logging(
    level=settings.log_level,
    logger_name='TOOL',
    log_file=settings.log_file,
)
mcp = FastMCP('package_tools')

mcp_server_logger.debug('Settings loaded')

@mcp.tool(name='check_package_status')
def check_package_status_tool(packageid: str) -> dict:
    mcp_server_logger.info('Called check_package_status tool')
    return check_package_status(
        packageid=packageid,
        base_hub_url=settings.hub_base_url,
        hub_api_key=settings.ai_devs_hub_api_key
    )

@mcp.tool(name='redirect_package')
def redirect_package_tool(packageid: str, destination: str, code: str) -> dict:
    mcp_server_logger.info('Called redirect_package tool')
    return redirect_package(
        packageid=packageid,
        destination=destination,
        code=code,
        base_hub_url=settings.hub_base_url,
        hub_api_key=settings.ai_devs_hub_api_key
    )

if __name__ == '__main__':
    mcp_server_logger.info('Starting server')
    mcp.run()