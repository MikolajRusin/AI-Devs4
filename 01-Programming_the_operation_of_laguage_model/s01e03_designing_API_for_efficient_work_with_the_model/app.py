from fastapi import FastAPI, status

from src.agent.transport_agent import TransportAgent
from src.config.settings import Settings
from src.schemas import ChatResponse, MessageRequest
from src.services.session_service import SessionService
from src.utils.logging import setup_logging

settings = Settings()
session_logger = setup_logging(
    level=settings.log_level,
    logger_name='SESSION',
    log_file=settings.log_file,
)
app_logger = setup_logging(
    level=settings.log_level,
    logger_name='SERVER',
    log_file=settings.log_file,
)
agent_logger = setup_logging(
    level=settings.log_level,
    logger_name='AGENT',
    log_file=settings.log_file,
)
session_service = SessionService(settings.sessions_dir)
agent = TransportAgent(settings=settings, session_service=session_service)

app_logger.debug('Settings loaded')
app_logger.info('Starting server')

app = FastAPI()

@app.post('/chat', response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def transport(req: MessageRequest):
    app_logger.info('Received chat request for session %s', req.sessionID)
    response_text = agent.run_conversation(
        user_message=req.msg,
        session_id=req.sessionID,
    )
    response = ChatResponse(msg=response_text)
    app_logger.info('Request handled successfully for session %s', req.sessionID)
    app_logger.debug(
        'Response payload for session %s: %s',
        req.sessionID,
        response.model_dump_json(),
    )
    return response
