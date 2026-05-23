from core.session import GameSession


class NextWordUseCase:
    def execute(self, session: GameSession, empty_word: str = "Нет слов") -> str:
        return session.next_word(empty_word=empty_word)
