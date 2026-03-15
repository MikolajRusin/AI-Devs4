import logging
from pathlib import Path


LOG_FORMAT = '%(asctime)s | %(levelname)s | %(name)s | %(message)s'


def setup_logging(
    level: str = 'INFO',
    logger_name: str = 'agent',
    log_file: str = 'logs/app.log',
) -> logging.Logger:
    logging.getLogger('httpx').disabled = True
    logging.getLogger('httpcore').disabled = True
    logging.getLogger('mcp').disabled = True
    
    logger = logging.getLogger(logger_name)

    if logger.handlers:
        return logger

    logger.setLevel(level.upper())
    logger.propagate = False

    log_file_path = Path(__file__).parents[2] / log_file
    log_file_path.parent.mkdir(parents=True, exist_ok=True)

    handler = logging.FileHandler(log_file_path, encoding='utf-8')
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(handler)

    return logger


def get_logger(name: str = 'agent') -> logging.Logger:
    return logging.getLogger(name)
