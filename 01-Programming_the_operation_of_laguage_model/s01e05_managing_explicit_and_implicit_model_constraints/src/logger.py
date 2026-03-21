import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any


class _Ansi:
    RESET = '\x1b[0m'
    BRIGHT = '\x1b[1m'
    DIM = '\x1b[2m'
    RED = '\x1b[31m'
    GREEN = '\x1b[32m'
    YELLOW = '\x1b[33m'
    BLUE = '\x1b[34m'
    MAGENTA = '\x1b[35m'
    CYAN = '\x1b[36m'
    WHITE = '\x1b[37m'
    BG_BLUE = '\x1b[44m'
    BG_MAGENTA = '\x1b[45m'


class ColoredFormatter(logging.Formatter):
    LEVEL_COLORS = {
        logging.DEBUG: _Ansi.DIM,
        logging.INFO: _Ansi.CYAN,
        logging.WARNING: _Ansi.YELLOW,
        logging.ERROR: _Ansi.RED,
        logging.CRITICAL: _Ansi.RED + _Ansi.BRIGHT,
    }

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')
        prefix = f'{_Ansi.DIM}[{timestamp}]{_Ansi.RESET}'
        color = self.LEVEL_COLORS.get(record.levelno, _Ansi.WHITE)
        message = record.getMessage()
        return f'{prefix} {color}{message}{_Ansi.RESET}'


class PlainFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')
        message = re.sub(r'\x1b\[[0-9;]*m', '', record.getMessage())
        return f'[{timestamp}] {message}'


def _truncate(value: Any, max_length: int) -> str:
    text = str(value or '')
    return text if len(text) <= max_length else f'{text[:max_length]}...'


def _label(name: str, color: str) -> str:
    return f'{color}[{name}]{_Ansi.RESET}'


def configure_logger(
    name: str = 'app',
    log_file: str | Path | None = None,
    level: int = logging.INFO,
) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    if logger.handlers:
        return logger

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(ColoredFormatter())
    logger.addHandler(console_handler)

    if log_file is not None:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(PlainFormatter())
        logger.addHandler(file_handler)

    return logger


class AppLogger:
    def __init__(self, logger: logging.Logger):
        self._logger = logger

    def info(self, message: str) -> None:
        self._logger.info(f"{_label('INFO', _Ansi.CYAN)} {message}")

    def success(self, message: str) -> None:
        self._logger.info(f"{_label('SUCCESS', _Ansi.GREEN)} {message}")

    def error(self, title: str, message: str = '') -> None:
        suffix = f' {message}' if message else ''
        self._logger.error(f"{_label('ERROR', _Ansi.RED)} {title}{suffix}")

    def warn(self, message: str) -> None:
        self._logger.warning(f"{_label('WARN', _Ansi.YELLOW)} {message}")

    def start(self, message: str) -> None:
        self._logger.info(f"{_label('START', _Ansi.CYAN)} {message}")

    def mcp_filesystem(self, message: str) -> None:
        self._logger.info(f"{_label('MCP_FILESYSTEM', _Ansi.BLUE)} {message}")

    def query(self, query: str) -> None:
        self._logger.info('')
        self._logger.info(f'{_Ansi.BG_BLUE}{_Ansi.WHITE} QUERY {_Ansi.RESET} {query}')
        self._logger.info('')

    def response(self, response: str) -> None:
        self._logger.info('')
        self._logger.info(f"{_label('RESPONSE', _Ansi.GREEN)} {_truncate(response, 500)}")
        self._logger.info('')

    def vision(self, message: str) -> None:
        self._logger.info(f"{_label('VISION', _Ansi.BLUE)}")
        self._logger.info(f'{_Ansi.DIM} {message}{_Ansi.RESET}')

    def hint(self, text: str) -> None:
        self._logger.info('')
        self._logger.info(f'{_Ansi.DIM}{text}{_Ansi.RESET}')
        self._logger.info('')

    def tool(self, name: str, args: Any) -> None:
        arg_str = _truncate(json.dumps(args, ensure_ascii=False), 100)
        self._logger.info(f"{_label('TOOL', _Ansi.YELLOW)} {name} {_Ansi.DIM}{arg_str}{_Ansi.RESET}")

    def tool_result(self, name: str, success: bool, output: str) -> None:
        status = 'OK' if success else 'ERROR'
        self._logger.info(f"{_label('TOOL_RESULT', _Ansi.DIM)} {name} {status} {_truncate(output, 150)}")


def get_logger(
    name: str = 'app',
    log_file: str | Path | None = None,
    level: int = logging.INFO,
) -> AppLogger:
    return AppLogger(configure_logger(name=name, log_file=log_file, level=level))


logger = get_logger()
