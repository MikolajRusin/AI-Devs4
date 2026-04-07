from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict

from src.tools import search_from_params


app = FastAPI(title='AI Devs S03E04 Tools')


class ToolRequest(BaseModel):
    model_config = ConfigDict(extra='allow')
    params: Any = None


@app.post('/search')
def search(request: ToolRequest) -> dict[str, str]:
    print(f'[search] request={request}')
    raw_request = request.model_dump(exclude_none=True)
    print(f'[search] request={raw_request}')
    payload = request.params if request.params is not None else raw_request
    print(f'[search] payload={payload}')
    output = search_from_params(payload)
    print(f'[search] output={output}')
    return {'output': output}
