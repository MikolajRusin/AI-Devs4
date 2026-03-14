from ..utils.logging import get_logger

from pathlib import Path
import json

logger = get_logger(name='SESSION')


class SessionService:
    def __init__(self, session_dir: str):
        self.session_dir_path = Path(__file__).parents[2] / session_dir
        self.session_dir_path.mkdir(parents=True, exist_ok=True)

    def _create_new_session(self, session_path: Path | str) -> list:
        new_session = []
        with open(session_path, 'w') as file:
            json.dump(new_session, file)
            logger.info('Created session history with session_id: %s', session_path.stem)
        return new_session

    def _read_session(self, session_path: Path | str) -> list[dict]:
        with open(session_path, 'r', encoding='utf-8') as file:
            session_history = json.load(file)
            logger.info('Loaded session with session_id: %s', session_path.stem)
        return session_history
        
    def load_session(self, session_id: str) -> list:
        session_path = self.session_dir_path / f'{session_id}.json'
        if session_path.exists():
            session_history = self._read_session(session_path)
        else:
            session_history = self._create_new_session(session_path)
        return session_history

    def write_session(self, conversation: list[dict], session_id: str):
        session_path = self.session_dir_path / f'{session_id}.json'
        with open(session_path, 'w', encoding='utf-8') as file:
            json.dump(conversation, file, indent=4)
        logger.info('History updated')