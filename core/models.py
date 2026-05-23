from dataclasses import dataclass, field
from typing import List


class WordReviewStatus:
    PENDING = "pending"
    CORRECT = "correct"
    SKIPPED = "skipped"
    IGNORED = "ignored"


@dataclass
class ReviewedWord:
    word: str
    status: str = WordReviewStatus.PENDING


@dataclass(frozen=True)
class RoundConfig:
    subject: str
    difficulty_label: str
    difficulty_id: str
    time_total: int
    penalty: int
    team: str
    language_code: str = "ru"


@dataclass
class RoundState:
    subject: str
    difficulty_label: str
    difficulty_id: str
    time_total: int
    time_left: float
    penalty: int
    team: str
    words_pool: List[str]
    score: int = 0
    correct: int = 0
    skipped: int = 0
    streak: int = 0
    best_streak: int = 0
    multiplier: int = 1
    current_word: str = ""
    reviewed_words: List[ReviewedWord] = field(default_factory=list)
