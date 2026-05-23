import random

from core.models import RoundConfig
from core.session import GameSession, WordProviderPort


class StartRoundUseCase:
    def execute(
        self,
        config: RoundConfig,
        word_provider: WordProviderPort,
        rng: random.Random,
    ) -> GameSession:
        return GameSession.create(config=config, word_provider=word_provider, rng=rng)
