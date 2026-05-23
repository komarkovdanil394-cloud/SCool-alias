from dataclasses import dataclass

from core.models import RoundState
from core.models import WordReviewStatus


@dataclass(frozen=True)
class AnswerResult:
    is_correct: bool
    score_delta: int
    score: int
    correct: int
    skipped: int
    streak: int
    best_streak: int
    multiplier: int
    combo_triggered: bool


class GameEngine:
    def apply_answer(self, state: RoundState, is_correct: bool) -> AnswerResult:
        if is_correct:
            state.correct += 1
            state.streak += 1
            if state.streak > state.best_streak:
                state.best_streak = state.streak
            combo_triggered = False
            if state.streak > 1 and state.streak % 3 == 0:
                state.multiplier = min(5, state.multiplier + 1)
                combo_triggered = state.multiplier >= 2
            score_delta = state.multiplier
            state.score += score_delta
        else:
            state.skipped += 1
            state.streak = 0
            state.multiplier = 1
            prev_score = state.score
            state.score = max(0, state.score - state.penalty)
            score_delta = state.score - prev_score
            combo_triggered = False

        return AnswerResult(
            is_correct=is_correct,
            score_delta=score_delta,
            score=state.score,
            correct=state.correct,
            skipped=state.skipped,
            streak=state.streak,
            best_streak=state.best_streak,
            multiplier=state.multiplier,
            combo_triggered=combo_triggered,
        )

    def recalculate_from_reviews(self, state: RoundState) -> AnswerResult:
        state.score = 0
        state.correct = 0
        state.skipped = 0
        state.streak = 0
        state.best_streak = 0
        state.multiplier = 1
        last_result = AnswerResult(False, 0, 0, 0, 0, 0, 0, 1, False)

        for item in state.reviewed_words:
            if item.status == WordReviewStatus.CORRECT:
                last_result = self.apply_answer(state, True)
            elif item.status == WordReviewStatus.SKIPPED:
                last_result = self.apply_answer(state, False)
            else:
                state.streak = 0
                state.multiplier = 1

        return AnswerResult(
            is_correct=last_result.is_correct,
            score_delta=last_result.score_delta,
            score=state.score,
            correct=state.correct,
            skipped=state.skipped,
            streak=state.streak,
            best_streak=state.best_streak,
            multiplier=state.multiplier,
            combo_triggered=last_result.combo_triggered,
        )
