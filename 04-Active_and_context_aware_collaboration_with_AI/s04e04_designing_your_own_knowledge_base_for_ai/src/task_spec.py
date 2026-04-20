from collections.abc import Callable
from dataclasses import dataclass

from .hub_client import HubClient


@dataclass(frozen=True)
class TaskSpec:
    name: str
    extractor_instructions: str
    reviewer_instructions: str
    normalize_extracted: Callable[[dict], dict]
    lock_reviewed: Callable[[dict, dict], dict]
    build: Callable[[dict, HubClient], dict]
    max_review_attempts: int = 3
