from pydantic import BaseModel, Field, ConfigDict
from typing import Any


class RequestsLimitations(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    retry_after: int | None = Field(default=None, alias='retry-after')
    x_rate_limit_remaining: int | None = Field(default=None, alias='x-ratelimit-remaining')
    x_rate_limit_reset: int | None = Field(default=None, alias='x-ratelimit-reset')


class RailwayApiResponse(BaseModel):
    status_code: int
    limitations: RequestsLimitations
    body: dict[str, Any] | None = None


class ActionArgument(BaseModel):
    model_config = ConfigDict(extra='forbid')

    name: str = Field(description='Argument name.')
    value: str = Field(description='Argument value.')


class PlannedAction(BaseModel):
    model_config = ConfigDict(extra='forbid')

    action: str = Field(
        description='Exact API action name to call next, taken from the API documentation.'
    )
    arguments: list[ActionArgument] = Field(
        ...,
        description='Ordered list of arguments for this action. Use an empty list if no arguments are required.'
    )
    reason: str = Field(
        description='Short explanation of why this action should be executed.'
    )


class AgentDecision(BaseModel):
    model_config = ConfigDict(extra='forbid')

    should_call_api: bool = Field(
        description='Set to true when the next step should call the API.'
    )
    actions: list[PlannedAction] = Field(
        ...,
        description='Ordered list of API actions to execute next. Use an empty list when no API call is needed.'
    )
    final_answer: str | None = Field(
        ...,
        description='Human-readable final answer. Use null when should_call_api is true.'
    )

