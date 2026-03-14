from pydantic import BaseModel

class MessageRequest(BaseModel):
    sessionID: str
    msg: str

class ChatResponse(BaseModel):
    msg: str