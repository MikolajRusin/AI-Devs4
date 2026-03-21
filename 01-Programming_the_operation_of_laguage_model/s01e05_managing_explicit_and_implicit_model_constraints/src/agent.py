from .hub_api import hub_response
from .chat_api import chat_responses
from .config import MAX_ITERATIONS, CHAT_MODEL, INSTRUCTIONS, RESPONSE_FORMAT
from .schemas import AgentDecision, RailwayApiResponse
from .logger import logger
from typing import Any
import json
import time


def extract_output_message(output_items: list[dict[str, Any]]) -> dict[str, Any] | None:
    for item in output_items:
        if item.get('type') == 'message':
            return item
    return None

def extract_message_text(output_message: dict[str, Any]) -> str | None:
    content = output_message.get('content', [])
    if not content:
        return None

    first_content = content[0]
    return first_content.get('text')

def append_user_message(conversation: list[dict[str, Any]], text: str) -> None:
    conversation.append({
        'role': 'user',
        'content': [
            {
                'type': 'input_text',
                'text': text
            }
        ]
    })

def run_agent(user_message: str):
    conversation: list[dict[str, Any]] = []
    append_user_message(
        conversation,
        user_message
    )

    logger.info(f'Model {CHAT_MODEL}')
    for _ in range(MAX_ITERATIONS):
        chat_response = chat_responses(CHAT_MODEL, conversation, INSTRUCTIONS, response_format=RESPONSE_FORMAT)
        
        output_items = chat_response.get('output', '')
        if not output_items:
            logger.warn('Returned empty output')
            return 'No response received'

        output_message = extract_output_message(output_items)
        if not output_message:
            logger.warn('No output message found in model response')
            return 'No output message received from the model.'

        response_text = extract_message_text(output_message)
        if not response_text:
            logger.warn('No text found in output message')
            return 'No text content received from the model.'

        try:
            response_dict = json.loads(output_message['content'][0]['text'])
        except json.JSONDecodeError as error:
            logger.warn(f'Failed to parse model response as JSON: {error}')
            logger.warn(f'Raw model response: {response_text}')
            return 'Model returned invalid JSON.'
        
        try:
            decision = AgentDecision.model_validate(response_dict)
        except Exception as e:
            logger.warn(f'Failed to validate model response: {error}')
            logger.warn(f'Parsed model response: {response_dict}')
            return 'Model returned data that does not match the expected schema.'

        logger.info(f'Agent decision: {decision.model_dump_json()}')

        if not decision.should_call_api:
            if decision.final_answer:
                return decision.final_answer

            logger.warn('Agent decided not to call API but did not provide final_answer')
            return 'Agent stopped without returning a final answer.'

        if not decision.actions:
            logger.warn('Agent decided to call API but returned no actions')
            return 'Agent wanted to call the API but did not provide any actions.'

        logger.start('Start actions...')
        for action in decision.actions:
            action_name      = action.action
            action_arguments = {arg.name: arg.value for arg in action.arguments}
            action_reason    = action.reason

            logger.info(f'Action reason: {action_reason}')
            logger.info(f'Action name: {action_name}')
            logger.info(f'Action arguments: {action_arguments}')
            
            action_result: RailwayApiResponse = hub_response(
                action=action_name,
                arguments=action_arguments
            )
            logger.info(f'Action result: {action_result.model_dump_json()}')
            
            append_user_message(
                conversation,
                (
                    f'Result of API action "{action_name}" '
                    f'with arguments {action_arguments}: '
                    f'{action_result.model_dump_json()}'
                ),
            )

    logger.warn('Max iterations reached')

