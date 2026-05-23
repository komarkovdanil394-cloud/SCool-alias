from core.engine import AnswerResult
from core.session import GameSession


class SubmitAnswerUseCase:
    def execute(self, session: GameSession, is_correct: bool) -> AnswerResult:
        return session.apply_answer(is_correct)
