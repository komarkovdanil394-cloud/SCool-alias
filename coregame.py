import random
from typing import List

from coremodels import GameState, GameSettings
from datawords import DATA


class GameEngine:
    """
    Основной движок игры.
    Содержит всю бизнес-логику.
    """

    def __init__(self, settings: GameSettings):
        self.settings = settings
        self.state = GameState()

        self._init_game()

    def _init_game(self) -> None:
        """
        Инициализация игры.
        Если заданные subject/difficulty отсутствуют в DATA, инициализируем пустой пул и ставим is_playing=False.
        """
        try:
            words: List[str] = DATA[self.settings.subject][self.settings.difficulty].copy()
        except KeyError:
            # Если данных нет, инициализируем пустой пул и пометим, что игра не запущена
            self.state.words_pool = []
            self.state.time_left = 0
            self.state.is_playing = False
            return

        # Перетасовывае�� пул; shuffle может быть замокирован в тестах
        random.shuffle(words)

        self.state.words_pool = words
        self.state.time_left = self.settings.time_limit
        self.state.is_playing = True

    def next_word(self) -> str:
        """
        Возвращает следующее слово.

        Returns:
            str: новое слово
        """
        if not self.state.words_pool:
            return ""

        self.state.current_word = self.state.words_pool.pop()
        return self.state.current_word

    def answer(self, correct: bool) -> None:
        """
        Обрабатывает ответ игрока.

        Args:
            correct: правильный ли ответ
        """
        if not self.state.is_playing:
            return

        if correct:
            self.state.score += 1
        else:
            self.state.skipped += 1
            self.state.penalty += self.settings.penalty

    def tick(self) -> None:
        """
        Уменьшает время на 1 секунду. Не разрешаем уходит ниже 0.
        """
        if not self.state.is_playing:
            return

        # Уменьшаем время
        self.state.time_left -= 1

        # Если время закончилось или стало отрицательным — останавливаем игру
        if self.state.time_left <= 0:
            self.state.time_left = max(0, self.state.time_left)
            self.state.is_playing = False

    def get_score(self) -> int:
        """
        Возвращает итоговый счёт.

        Returns:
            int: финальный результат
        """
        return self.state.score - self.state.penalty
