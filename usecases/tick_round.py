from core.session import GameSession


class TickRoundUseCase:
    def execute(self, session: GameSession, delta_seconds: float) -> float:
        return session.tick(delta_seconds)
