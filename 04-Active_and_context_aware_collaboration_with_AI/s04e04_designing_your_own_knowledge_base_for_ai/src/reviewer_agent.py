import json

from .json_agent import run_json_agent
from .mcp_client import MCPFileSystemClient
from .task_spec import TaskSpec


async def run_reviewer(mcp: MCPFileSystemClient, root, extracted: dict, spec: TaskSpec, feedback: dict | None = None) -> dict:
    prompt = (
        'Review this extracted JSON against the source notes and return the corrected JSON only:\n\n'
        + json.dumps(extracted, ensure_ascii=False, indent=2)
    )
    if feedback is not None:
        prompt += (
            '\n\nThe previous upload failed. Use this verifier feedback to correct the JSON, '
            'but still verify every change against the source notes:\n\n'
            + json.dumps(feedback, ensure_ascii=False, indent=2)
        )
    reviewed = await run_json_agent(
        agent_name='reviewer',
        instructions=spec.reviewer_instructions,
        prompt=prompt,
        mcp=mcp,
        root=root,
    )
    return spec.lock_reviewed(extracted, reviewed)
