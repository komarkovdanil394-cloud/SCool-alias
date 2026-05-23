import asyncio
from typing import Optional

from coregame import GameEngine
from coremodels import GameSettings
from coretimer import GameTimer
from datawords import DIFFICULTIES


class GameController:
    """
    Контроллер игры.
    Связывает UI и игровую логику.
    """

    def __init__(self, update_ui_callback):
        """
        Args:
            update_ui_callback: функция обновления UI
        """
        self.engine: Optional[GameEngine] = None
        self.timer: Optional[GameTimer] = None
        self.update_ui = update_ui_callback

    def start_game(self, subject: str, difficulty_label: str) -> None:
        """
        Запуск новой игры.
        
        Args:
            subject: выбранный предмет
            difficulty_label: уровень сложности (текст)
        """
        diff = DIFFICULTIES[difficulty_label]

        settings = GameSettings(
            subject=subject,
            difficulty=diff["id"],
            time_limit=diff["time"],
            penalty=diff["penalty"]
        )

        self.engine = GameEngine(settings)

        # создаём таймер
        self.timer = GameTimer(
            tick_callback=self._on_tick,
            end_callback=self._on_finish
        )

        asyncio.create_task(self.timer.start())

    def next_word(self) -> str:
        """
        Получить следующее слово.
        """
        return self.engine.next_word()

    def answer(self, correct: bool) -> None:
        """
        Обработка ответа пользователя.
        
        Args:
            correct: правильный ли ответ
        """
        self.engine.answer(correct)

        # сразу обновляем UI
        self.update_ui(self.engine.state)

    def _on_tick(self) -> None:
        """
        Вызывается каждую секунду.
        """
        self.engine.tick()
        self.update_ui(self.engine.state)

        if not self.engine.state.is_playing:
            self._on_finish()

    def _on_finish(self) -> None:
        """
        Завершение игры.
        """
        if self.timer:
            self.timer.stop()

        self.update_ui(self.engine.state)