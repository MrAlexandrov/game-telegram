"""
Перечисления для системы
"""
from enum import Enum


class SessionStatus(str, Enum):
    """Статусы игровых сессий"""
    WAITING = "waiting"      # Ожидание игроков
    ACTIVE = "active"        # Игра идет
    FINISHED = "finished"    # Игра завершена
    CANCELLED = "cancelled"  # Игра отменена


class GameType(str, Enum):
    """Типы игр"""
    QUIZ = "quiz"
    HUNDRED_TO_ONE = "hundred_to_one"


class GameState(str, Enum):
    """Состояния игры"""
    WAITING = "waiting"      # Ожидание начала
    READY = "ready"          # Готова к запуску
    ACTIVE = "active"        # Активна
    PAUSED = "paused"        # Приостановлена
    FINISHED = "finished"    # Завершена


class QuestionType(str, Enum):
    """Типы вопросов в викторине"""
    MULTIPLE_CHOICE = "multiple_choice"  # Множественный выбор
    TEXT_INPUT = "text_input"            # Текстовый ввод
    TRUE_FALSE = "true_false"            # Правда/Ложь
    NUMERIC = "numeric"                  # Числовой ответ


class RoundType(str, Enum):
    """Типы раундов в игре 100 к 1"""
    SIMPLE = "simple"        # Обычный раунд (x1)
    DOUBLE = "double"        # Двойной раунд (x2)
    TRIPLE = "triple"        # Тройной раунд (x3)
    FINAL = "final"          # Финальный раунд (x5)


class UserRole(str, Enum):
    """Роли пользователей"""
    ADMIN = "admin"          # Администратор
    PLAYER = "player"        # Игрок
    SPECTATOR = "spectator"  # Наблюдатель