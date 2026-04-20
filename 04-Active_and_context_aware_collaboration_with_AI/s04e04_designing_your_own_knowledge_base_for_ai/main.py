import asyncio
import json
from pathlib import Path

from src.extractor_agent import run_extractor
from src.filesystem_task import FILESYSTEM_SPEC
from src.hub_client import HubClient
from src.mcp_client import MCPFileSystemClient
from src.reviewer_agent import run_reviewer

APP_ROOT = Path(__file__).parent

async def main():
    spec = FILESYSTEM_SPEC
    mcp = MCPFileSystemClient(
        mcp_config_path=str(APP_ROOT / '.mcp.json'),
        server_name='filesystem',
    )
    hub = HubClient(task_name=spec.name)

    await mcp.connect()
    try:
        print('\n=== PHASE 1: EXTRACTION ===')
        extracted = await run_extractor(mcp=mcp, root=APP_ROOT, spec=spec)
        print(f'[main] extracted: {json.dumps(extracted, ensure_ascii=False, indent=2)}')

        reviewed = extracted
        print('\n=== PHASE 2: BUILD 1 ===')
        result = spec.build(data=reviewed, hub=hub)
        if result.get('code') == 0:
            print(f'\n=== RESULT ===\n{result}')
            return

        for attempt in range(spec.max_review_attempts):
            print(f'\n=== PHASE 3: REVIEW {attempt + 1} ===')
            feedback = result.get('error') if isinstance(result, dict) else result
            reviewed = await run_reviewer(
                mcp=mcp,
                root=APP_ROOT,
                extracted=reviewed,
                spec=spec,
                feedback=feedback,
            )
            print(f'[main] reviewed: {json.dumps(reviewed, ensure_ascii=False, indent=2)}')

            print(f'\n=== PHASE 4: BUILD {attempt + 2} ===')
            result = spec.build(data=reviewed, hub=hub)
            if result.get('code') == 0:
                break

        print(f'\n=== RESULT ===\n{result}')
    finally:
        await mcp.cleanup()


if __name__ == '__main__':
    asyncio.run(main())
