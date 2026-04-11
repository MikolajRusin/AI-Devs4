from dataclasses import dataclass
from typing import Any, Callable

from .middleware import on_tool_call
from .oko_scraper import scrape_page
from .oko_service import OkoService


@dataclass
class Tool:
    definition: dict
    handler: Callable[..., Any]


def make_tools(service: OkoService) -> list[Tool]:
    def oko_execute(action: str, **kwargs) -> dict:
        result = service.execute(action, **kwargs)
        return on_tool_call(result)

    def oko_done() -> dict:
        result = service.done()
        return on_tool_call(result)

    def oko_scrape(path: str, id: str | None = None) -> list[dict] | str:
        return scrape_page(path, record_id=id)

    return [
        Tool(
            definition={
                'type': 'function',
                'name': 'oko_scrape',
                'description': (
                    'Log into the OKO web panel, scrape the given page, and return a list of records '
                    'with their id, title and status. Use this to find the 32-char hex IDs needed for update actions. '
                    'Available paths: /incydenty, /zadania, /notatki, /uzytkownicy.'
                ),
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'path': {
                            'type': 'string',
                            'description': 'Page path to scrape, e.g. "/incydenty" or "/zadania".'
                        },
                        'id': {
                            'type': 'string',
                            'description': (
                                'Optional 32-char hex record ID. '
                                'Omit to get the full list with id, title, status and a short excerpt (~100 chars). '
                                'Provide to fetch the complete detail page for that specific record.'
                            )
                        }
                    },
                    'required': ['path']
                }
            },
            handler=oko_scrape
        ),
        Tool(
            definition={
                'type': 'function',
                'name': 'oko_execute',
                'description': (
                    'Execute any OKO editor API action. '
                    'Call with action="help" first to discover available commands and their parameters.'
                ),
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'action': {
                            'type': 'string',
                            'description': 'The action name to execute, e.g. "help" or "update".'
                        }
                    },
                    'required': ['action'],
                    'additionalProperties': True
                }
            },
            handler=oko_execute
        ),
        Tool(
            definition={
                'type': 'function',
                'name': 'oko_done',
                'description': 'Signal that all required edits are complete and verify the final result.',
                'parameters': {
                    'type': 'object',
                    'properties': {},
                    'required': []
                }
            },
            handler=oko_done
        ),
    ]


def find_tool(tool_name: str, tools: list[Tool]) -> Callable[..., Any] | None:
    for tool in tools:
        if tool.definition.get('name') == tool_name:
            return tool.handler
    return None
