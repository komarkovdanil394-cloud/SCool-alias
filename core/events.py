from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict


class GameEventType(str, Enum):
    ROUND_STARTED = "round_started"
    WORD_CHANGED = "word_changed"
    ANSWER_SUBMITTED = "answer_submitted"
    TIME_UPDATED = "time_updated"
    ROUND_FINISHED = "round_finished"


@dataclass(frozen=True)
class GameEvent:
    event_type: GameEventType
    payload: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
