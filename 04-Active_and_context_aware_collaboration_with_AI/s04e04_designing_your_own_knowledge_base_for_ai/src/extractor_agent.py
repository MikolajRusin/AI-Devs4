from .json_agent import run_json_agent
from .mcp_client import MCPFileSystemClient
from .task_spec import TaskSpec


async def run_extractor(mcp: MCPFileSystemClient, root, spec: TaskSpec) -> dict:
    return await run_json_agent(
        agent_name='extractor',
        instructions=spec.extractor_instructions,
        prompt='Read the source note files and output the JSON structure described in your instructions.',
        mcp=mcp,
        root=root,
        postprocess=spec.normalize_extracted,
    )
