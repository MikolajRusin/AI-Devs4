import re
import tiktoken
from typing import Literal

from ..clients.hub_client import AiDevsHubClient


async def download_logs(hub_client: AiDevsHubClient) -> str:
    return await hub_client.download_logs()

def parse_logs(logs: str) -> list[dict[str, str]]:
    pattern = re.compile(r'^\[(.*?)\]\s+\[(.*?)\]\s+(.*)$')

    parsed_logs = []
    for line in logs.splitlines():
        match = pattern.match(line)
        if match:
            time, event, message = match.groups()
            parsed_logs.append({
                'time': time,
                'event': event,
                'message': message
            })
    return parsed_logs

EventType = Literal['INFO', 'WARN', 'ERRO', 'CRIT']
def filter_by_event(logs: list[dict[str, str]], event: list[EventType]) -> list[dict[str, str]]:
    return [log_info for log_info in logs if any(e in log_info['event'] for e in event)]

def filter_by_search(logs: list[dict[str, str]], search: list[str]) -> list[dict[str, str]]:
    return  [log_info for log_info in logs if any(s in log_info['message'] for s in search)]

def take_first_n_per_group(logs: list[dict[str, str]], first_n: int) -> list[dict[str, str]]:
    counts: dict[tuple[str, str], int] = {}
    dedup_logs = []

    for log_info in logs:
        key = (log_info['event'], log_info['message'])
        current_count = counts.get(key, 0)
        if current_count < first_n:
            dedup_logs.append(log_info)
            counts[key] = current_count + 1
    
    return dedup_logs

def logs2text(logs: list[dict[str, str]]) -> str:
    logs_list = [f"[{log_info['time']}] [{log_info['event']}] {log_info['message']}" for log_info in logs]
    # logs_list = [f"[{log_info['event']}] {log_info['message']}" for log_info in logs]
    return '\n'.join(logs_list)

def number_of_tokens(text: str, model: str) -> int:
    encoding = tiktoken.encoding_for_model(model)
    tokens = encoding.encode(text)
    return len(tokens)