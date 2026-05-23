from dataclasses import dataclass
from typing import Optional

from core.models import RoundState


@dataclass
class GameViewModel:
    has_active_round: bool = False
    team: str = ""
    subject: str = ""
    difficulty_label: str = ""
    language_caption: str = ""
    current_word: str = ""
    score: int = 0
    correct: int = 0
    skipped: int = 0
    multiplier: int = 1
    time_left: float = 0.0
    time_total: int = 0
    penalty: int = 0

    @classmethod
    def from_round_state(
        cls, round_state: Optional[RoundState], language_caption: str = ""
    ) -> "GameViewModel":
        if round_state is None:
            return cls()

        return cls(
            has_active_round=True,
            team=round_state.team,
            subject=round_state.subject,
            difficulty_label=round_state.difficulty_label,
            language_caption=language_caption,
            current_word=round_state.current_word,
            score=round_state.score,
            correct=round_state.correct,
            skipped=round_state.skipped,
            multiplier=round_state.multiplier,
            time_left=round_state.time_left,
            time_total=round_state.time_total,
            penalty=round_state.penalty,
        )
