from ..settings import Settings
from ..clients.hub_client import AiDevsHubClient
from ..mcp.filesystem_client import MCPFileSystemClient
from ..tools.handlers import (
    download_documents, read_file, manage_files, send_declaration,
    FileType, ManageMode
)
from ..tools.tools_definition import TOOLS_DEFINITION
from ..utils.logger import logger

from typing import Any
from pathlib import Path
import httpx
import json


class DeclarationAgent:
    SYSTEM_INSTRUCTIONS = """
You are a document-driven task agent solving strict, verification-based challenges.

You do NOT have full documentation. You must request files by EXACT filenames and recursively gather all required data.

--------------------------------------------------
RULES
--------------------------------------------------

- Retrieved files are the ONLY source of truth.
- NEVER invent values, formats, filenames, rules, or structure.
- If not explicitly confirmed → UNKNOWN.
- Do not guess — retrieve more data.

FILES & TOOLS:
- Use ALL available tools efficiently.
- If multiple files are needed → request ALL of them (not one-by-one unless required).
- Always use exact filenames (no guessing or modifying).
- Follow all file references (including images).

--------------------------------------------------
WORKFLOW
--------------------------------------------------

1. DISCOVER → find rules, fields, constraints, referenced files.
2. EXTRACT → collect ONLY explicitly confirmed values.
3. BUILD → reproduce template EXACTLY (format, order, spacing).
4. VALIDATE → check format, fields, rules, constraints, no extras.
5. RETRY → fix errors using verification feedback until success.

--------------------------------------------------
OUTPUT
--------------------------------------------------

- File request → ONLY filename(s).
- Final answer → ONLY final document.
- No explanations.

--------------------------------------------------
GOAL
--------------------------------------------------

Finish ONLY when output is correct and accepted. Never stop early.
""".strip()

    def __init__(self, settings: Settings, hub_client: AiDevsHubClient, mcp_filesystem_client: MCPFileSystemClient):
        self.settings = settings
        self.hub_client = hub_client
        self.mcp_filesystem_client = mcp_filesystem_client

        self.tools_registry = {
            'download_documents': self._download_documents,
            'read_file'         : self._read_file,
            'manage_files'      : self._manage_files,
            'send_declaration'  : self._send_declaration,
        }

    def _resolve_data_path(self, path: str) -> str:
        raw_path = Path(path)

        if raw_path.is_absolute():
            return str(raw_path)

        parts = raw_path.parts
        if parts and parts[0] == 'data':
            raw_path = Path(*parts[1:])

        return str((Path(self.settings.data_dir_path) / raw_path).resolve())


    async def _download_documents(self, document_names: list[str]) -> dict[str, str]:
        result = await download_documents(
            document_names=document_names,
            hub_client=self.hub_client
        )
        return result

    async def _read_file(self, file_path: str, file_type: FileType) -> dict[str, str]:
        result = await read_file(
            file_path=self._resolve_data_path(file_path),
            file_type=file_type,
            filesystem_client=self.mcp_filesystem_client,
            mistral_api_key=self.settings.mistral_api_key,
            mistral_ocr_endpoint=self.settings.mistral_ocr_endpoint,
            mistral_ocr_model=self.settings.mistral_ocr_model
        )
        return result

    async def _manage_files(self, path: str, mode: ManageMode, content: str | None = None) -> dict[str, str]:
        result = await manage_files(
            path=self._resolve_data_path(path),
            mode=mode,
            content=content,
            filesystem_client=self.mcp_filesystem_client
        )
        return result

    async def _send_declaration(self, task_name: str, declaration_path: str) -> dict[str, str]:
        result = await send_declaration(
            task_name=task_name,
            declaration_path=self._resolve_data_path(declaration_path),
            hub_client=self.hub_client,
            filesystem_client=self.mcp_filesystem_client
        )
        return result

    async def _execute_tools(self, tool_calls: list[dict]) -> list[dict]:
        tool_calls_info = []
        for tool_call in tool_calls:
            tool_name = tool_call['name']
            tool_args = json.loads(tool_call['arguments'])
            logger.info(f'Model called tool -> Tool Name: {tool_name}, Arguments: {tool_args}')

            tool_results = await self.tools_registry[tool_name](**tool_args)
            tool_calls_info.append(
                {
                    'type': 'function_call_output',
                    'call_id': tool_call['call_id'],
                    'output': json.dumps(tool_results, ensure_ascii=False)
                }
            )
        return tool_calls_info

    @staticmethod
    def _extract_output_message(output_items: list[dict[str, Any]]) -> dict[str, Any]:
        for item in output_items:
            if item.get('type') == 'message':
                return item
        return None

    async def chat_responses(self, conversation: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=70) as client:
            response = await client.post(
                url=self.settings.openai_responses_endpoint,
                headers={
                    'Authorization': f'Bearer {self.settings.openai_api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': self.settings.declaration_agent_model,
                    'input': conversation,
                    'instructions': self.SYSTEM_INSTRUCTIONS,
                    'tools': TOOLS_DEFINITION
                }
            )

        logger.info(f'Declaration agent response status code: {response.status_code}')
        return response.json()

    async def run_agent(self, user_message: str):
        logger.query(user_message)
        
        await self.mcp_filesystem_client.connect_to_server()
        conversation = [
            {'role': 'user', 'content': user_message}
        ]

        try:
            for iteration in range(self.settings.max_iterations):
                logger.info(f'Starting agent iteration {iteration + 1}/{self.settings.max_iterations}')
                response = await self.chat_responses(conversation)

                if response.get('error'):
                    logger.error('Response agent error', json.dumps(response['error']))
                    return 'The error occured while processing the request'

                output_items = response.get('output', [])
                if not output_items:
                    logger.warn('Returned empty output')
                    return 'No response received'

                tool_calls = [item for item in output_items if item.get('type') == 'function_call']
                tool_reasoning = [item for item in output_items if item.get('type') == 'reasoning']
                logger.info(f'Detected {len(tool_calls)} tool call(s) and {len(tool_reasoning)} reasoning(s) in current iteration')
                conversation.extend(output_items)
                
                if tool_calls:
                    logger.info('Agent Executing tools...')
                    tool_results = await self._execute_tools(tool_calls)
                    conversation.extend(tool_results)
                    logger.info('Tools executed.')
                    continue

                output_message = self._extract_output_message(output_items)
                if output_message:
                    message = output_message['content'][0]['text']
                    logger.response(message)
                    return message

                logger.error(
                    'Agent stalled',
                    'Model returned no tool calls and no final message.'
                )
                logger.info(f"Response status: {response.get('status')}")
                logger.info(f"Response incomplete details: {response.get('incomplete_details')}")
                logger.info(
                    f"Response output item types: {[item.get('type') for item in response.get('output', [])]}"
                )
                return 'Model did not return a final answer.'

            logger.warn('Max iterations reached.')
            
        finally:
            await self.mcp_filesystem_client.cleanup()




# ----------------- v2 -----------------------

# You are a document-driven task agent solving strict, verification-based challenges.

# You do NOT have full documentation. You must request files by EXACT filename and recursively discover all required data.

# --------------------------------------------------
# RULES
# --------------------------------------------------

# - Retrieved files are the ONLY source of truth.
# - NEVER invent values, formats, filenames, rules, or structure.
# - If not explicitly confirmed → UNKNOWN.
# - Do not guess — request more files or re-check.

# FILES:
# - Use exact filenames only (no guessing, no changes).
# - Extract and follow all references to other files.
# - Images may contain critical data — process them fully.

# --------------------------------------------------
# WORKFLOW
# --------------------------------------------------

# 1. DISCOVER
# - Read files, find rules, required fields, constraints.
# - Collect and request all referenced files.
# - Continue until nothing is unknown.

# 2. EXTRACT
# - Identify all required fields.
# - For each → find explicit confirmation.
# - If any missing → go back.

# 3. BUILD
# - Reproduce template EXACTLY (format, order, spacing).
# - Use ONLY verified data.

# 4. VALIDATE (CRITICAL)
# Check:
# - exact format match,
# - all required fields present,
# - values follow rules,
# - codes/routes/categories correct,
# - pricing/constraints satisfied,
# - no extra or forbidden content.

# If anything fails → fix and re-check.

# 5. RETRY LOOP
# - On verification error:
#   → treat it as a clue,
#   → find violated rule,
#   → fix using documentation,
#   → retry until success.

# --------------------------------------------------
# OUTPUT
# --------------------------------------------------

# - File request → output ONLY filename.
# - Final answer → output ONLY final document.
# - No explanations.

# --------------------------------------------------
# GOAL
# --------------------------------------------------

# Task is complete ONLY when the final output is correct and accepted.
# Never stop early.



# ----------------- v1 -----------------------

#     SYSTEM_INSTRUCTIONS = """
# You are a specialist in analyzing technical documentation and completing strict document-based tasks.

# You must work only from:
# - the user message,
# - downloaded documents,
# - local files,
# - tool outputs.

# General rules:
# - Treat the documentation as the only source of truth.
# - Do not invent facts, filenames, values, routes, categories, prices, limits, or document structure.
# - If something is not explicitly confirmed, treat it as unknown and keep investigating.
# - Prefer one more verification step over guessing.
# - Use exact filenames exactly as written in the source materials.
# - Do not invent alternative filenames, extensions, transliterations, or spelling variants.
# - If you are unsure about a referenced filename, inspect the available local files or re-read the source document instead of guessing.
# - Use filesystem tools only for paths inside the allowed local task workspace.
# - Organize working materials and generated outputs inside a separate local directory created for the task.
# - Preserve exact formatting whenever the task requires a strict template.
# - Prepare the final document in the same language as the source template or documentation, unless the task explicitly requires another language.

# Reasoning rules:
# - Work step by step.
# - Base every important decision on evidence from the documentation or tool outputs.
# - For every critical field or rule, make sure you have explicit support in the documentation before using it.
# - If multiple conditions must all be satisfied, treat the task as incomplete until each condition has been checked.
# - Do not stop after partial analysis.
# - Do not stop after drafting the result.
# - Do not stop after saving a draft.
# - The task is complete only after the final artifact has been saved and successfully submitted, if submission is required.

# Before submission, explicitly verify:
# - the exact template and formatting,
# - every field written in the final document,
# - all relevant codes, categories, and pricing or financing rules,
# - all operational and feasibility constraints,
# - any hidden rejection condition described in the documentation.

# If verification fails:
# - treat the verification error as a clue,
# - return to the documentation,
# - identify the violated rule,
# - correct the result based on evidence,
# - retry.

# When the task is complete, provide a short final summary.
# """.strip()