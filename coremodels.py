from dataclasses import dataclass, field
from typing import List


@dataclass
class GameSettings:
    """
    Настройки игры.

    Attributes:
        subject: выбранный предмет
        difficulty: уровень сложности
        time_limit: время игры в секундах
        penalty: штраф за пропуск
    """
    subject: str
    difficulty: str
    time_limit: int
    penalty: int


@dataclass
class GameState:
    """
    Текущее состояние игры.

    Attributes:
        score: количество правильных ответов
        skipped: количество пропусков
        penalty: штрафные очки
        time_left: оставшееся время
        current_word: текущее слово
        words_pool: список слов (по умолчанию пустой список)
        is_playing: идёт ли игра
    """
    score: int = 0
    skipped: int = 0
    penalty: int = 0
    time_left: int = 0
    current_word: str = ""
    # Используе�� default_factory, чтобы избежать общего изменяемого состояния между инстансами
    words_pool: List[str] = field(default_factory=list)
    is_playing: bool = False
