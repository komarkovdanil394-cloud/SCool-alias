import asyncio
from typing import Callable


class GameTimer:
    """
    Асинхронный таймер игры.
    """

    def __init__(self, tick_callback: Callable, end_callback: Callable):
        """
        Args:
            tick_callback: вызывается каждую секунду
            end_callback: вызывается при окончании времени
        """
        self.tick_callback = tick_callback
        self.end_callback = end_callback
        self._running = False

    async def start(self):
        """
        Запуск таймера.
        """
        self._running = True

        while self._running:
            await asyncio.sleep(1)
            self.tick_callback()

            if not self._running:
                break

    def stop(self):
        """
        Остановка таймера.
        """
        self._running = False