from enum import Enum
from typing import Optional


class DifficultyId(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

    @classmethod
    def from_value(cls, value: str) -> Optional["DifficultyId"]:
        try:
            return cls(value)
        except ValueError:
            return None
