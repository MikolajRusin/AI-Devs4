from src.settings import Settings
from src.clients.hub_client import AiDevsHubClient
from src.mcp.filesystem_client import MCPFileSystemClient
from src.agents.declaration_agent import DeclarationAgent
from src.utils.logger import logger

import asyncio

async def main():
    logger.start('Start application')

    settings = Settings()
    hub_client = AiDevsHubClient(
        settings.ai_devs_hub_api_key, 
        settings.hub_base_url,
        settings.data_dir_path
    )
    mcp_filesystem_client = MCPFileSystemClient(settings.mcp_config_path)
    agent = DeclarationAgent(
        settings=settings,
        hub_client=hub_client,
        mcp_filesystem_client=mcp_filesystem_client
    )

    user_prompt = """
Solve task `sendit`.

Goal:
Prepare a correct transport declaration and successfully pass verification.

--------------------------------------------------
DOCUMENTATION
--------------------------------------------------

- Start from `index.md`.
- Recursively read ALL referenced files (including images).
- Use exact filenames only.
- Do not skip any potentially relevant file.

--------------------------------------------------
TASK DATA
--------------------------------------------------

- sender identifier: 450202122
- origin: Gdańsk
- destination: Żarnowiec
- weight: 2800 kg
- budget: 0 PP
- content: kasety z paliwem do reaktora
- special notes: none (do not add any)

--------------------------------------------------
REQUIREMENTS
--------------------------------------------------

- Match the declaration template EXACTLY (format, order, separators).
- Determine from documentation:
  - route code,
  - shipment category,
  - pricing/financing rule.
- Shipment must be free or financed by the System.
- Do NOT guess any value.
- Closed route is NOT a blocker.

--------------------------------------------------
EXECUTION RULES
--------------------------------------------------

- Retrieve ALL required files (batch when possible).
- Extract only explicitly confirmed data.
- Save the final declaration to a local file.
- Submit for task `sendit`.

If verification fails:
→ use error as a clue,
→ find violated rule in documentation,
→ fix and retry until success.

--------------------------------------------------
VALIDATION (MANDATORY)
--------------------------------------------------

Before submission, confirm:
- exact template match,
- all fields correct,
- valid route code,
- correct category,
- correct pricing/financing,
- compliance with all rules (including hidden ones),
- no forbidden or extra content.

--------------------------------------------------
COMPLETION CONDITION
--------------------------------------------------

Task is complete ONLY if:
- declaration is created,
- saved locally,
- submitted,
- verification response is received.

--------------------------------------------------
EXPECTED RESULT
--------------------------------------------------

Return the verification result (include flag if successful).
""".strip()
    result = await agent.run_agent(user_prompt)

    logger.info('End application')

if __name__ == '__main__':
    asyncio.run(main())



# -------------- 'gpt-5-mini' -------------------
#     user_prompt = """
# Solve task `sendit`.

# Your goal is to prepare a correct transport declaration for the conductor shipment system and submit it successfully.

# Documentation:
# - Start from `index.md`.
# - Read all relevant referenced files.
# - Some important files may be images and must be processed accordingly.
# - Use exact referenced filenames only.

# Task data:
# - sender identifier: 450202122
# - origin point: Gdańsk
# - destination point: Żarnowiec
# - weight: 2800 kg
# - budget: 0 PP
# - content description: kasety z paliwem do reaktora
# - special notes: do not add any

# Requirements:
# - The declaration must match the exact template from the documentation.
# - Formatting, separators, field order, and line structure must be preserved exactly.
# - Determine the correct route code from the documentation.
# - Determine the correct shipment category from the documentation.
# - Determine the correct pricing or financing rule from the documentation.
# - The shipment must be free or financed by the System.
# - Do not guess missing values.
# - The fact that the route is closed is not a reason to stop.
# - Save the final declaration to a local file before submission.
# - Submit the saved declaration for task `sendit`.
# - If verification returns an error, use it to identify what rule was violated, correct the declaration, and try again.

# Critical instruction:
# Before submitting anything, verify from the documentation all rules that may affect acceptance of the shipment, including:
# - declaration format,
# - route code,
# - shipment category,
# - pricing or financing rule,
# - route restrictions,
# - transport feasibility,
# - weight and capacity limits,
# - any rule that may cause rejection even if the format is correct.

# Mandatory completion condition:
# The task is not complete until all of the following have happened:
# - the final declaration text has been prepared,
# - the declaration has been written to a local file,
# - the saved declaration has been submitted,
# - a verification response has been received.

# Mandatory final checklist before submission:
# - confirm the exact declaration template,
# - confirm every field written in the declaration,
# - confirm the route code,
# - confirm the shipment category,
# - confirm the payment or financing rule,
# - confirm that the shipment is physically and operationally acceptable,
# - confirm that no hidden rejection rule from the documentation has been missed.

# Expected result:
# - a successful verification response for task `sendit`,
# - the final response should include the verification result, including the flag if successful.
# """.strip()
