from __future__ import annotations

import random
from typing import List, Optional, Protocol

from core.engine import AnswerResult, GameEngine
from core.models import ReviewedWord, RoundConfig, RoundState, WordReviewStatus


class WordProviderPort(Protocol):
    def get_words(self, subject: str, difficulty_id: str, language_code: str = "ru") -> List[str]:
        ...


class GameSession:
    def __init__(
        self,
        state: RoundState,
        word_provider: WordProviderPort,
        rng: random.Random,
        language_code: str = "ru",
        engine: Optional[GameEngine] = None,
    ):
        self.state = state
        self.word_provider = word_provider
        self.rng = rng
        self.language_code = language_code
        self.engine = engine or GameEngine()

    @classmethod
    def create(
        cls,
        config: RoundConfig,
        word_provider: WordProviderPort,
        rng: random.Random,
        engine: Optional[GameEngine] = None,
    ) -> "GameSession":
        words = word_provider.get_words(
            subject=config.subject,
            difficulty_id=config.difficulty_id,
            language_code=config.language_code,
        )
        pool = list(words)
        rng.shuffle(pool)
        state = RoundState(
            subject=config.subject,
            difficulty_label=config.difficulty_label,
            difficulty_id=config.difficulty_id,
            time_total=config.time_total,
            time_left=float(config.time_total),
            penalty=config.penalty,
            team=config.team,
            words_pool=pool,
        )
        return cls(
            state=state,
            word_provider=word_provider,
            rng=rng,
            language_code=config.language_code,
            engine=engine,
        )

    def next_word(self, empty_word: str = "Нет слов") -> str:
        if not self.state.words_pool:
            refill = self.word_provider.get_words(
                subject=self.state.subject,
                difficulty_id=self.state.difficulty_id,
                language_code=self.language_code,
            )
            self.state.words_pool = list(refill)
            self.rng.shuffle(self.state.words_pool)

        if not self.state.words_pool:
            self.state.current_word = empty_word
        else:
            self.state.current_word = self.state.words_pool.pop()
            self.state.reviewed_words.append(ReviewedWord(self.state.current_word))
        return self.state.current_word

    def apply_answer(self, is_correct: bool) -> AnswerResult:
        result = self.engine.apply_answer(self.state, is_correct)
        if self.state.reviewed_words:
            current = self.state.reviewed_words[-1]
            if current.status == WordReviewStatus.PENDING:
                current.status = WordReviewStatus.CORRECT if is_correct else WordReviewStatus.SKIPPED
        return result

    def set_review_status(self, index: int, status: str) -> AnswerResult:
        if 0 <= index < len(self.state.reviewed_words):
            self.state.reviewed_words[index].status = status
        return self.engine.recalculate_from_reviews(self.state)

    def tick(self, delta_seconds: float) -> float:
        delta = max(0.0, float(delta_seconds))
        self.state.time_left = max(0.0, self.state.time_left - delta)
        return self.state.time_left

    def is_finished(self) -> bool:
        return self.state.time_left <= 0.0
