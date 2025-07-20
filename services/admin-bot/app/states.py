"""
Admin Bot FSM States
Состояния для управления диалогами администратора
"""

from aiogram.fsm.state import State, StatesGroup


class AdminStates(StatesGroup):
    """Основные состояния администратора"""
    MAIN_MENU = State()
    WAITING_AUTH = State()


class GameCreationStates(StatesGroup):
    """Состояния создания игры"""
    SELECTING_TYPE = State()
    UPLOADING_PACK = State()
    CONFIRMING_GAME = State()
    ENTERING_TITLE = State()
    ENTERING_DESCRIPTION = State()


class SessionManagementStates(StatesGroup):
    """Состояния управления сессией"""
    SELECTING_GAME = State()
    SESSION_ACTIVE = State()
    WAITING_PLAYERS = State()
    GAME_IN_PROGRESS = State()
    QUESTION_ACTIVE = State()
    VALIDATING_ANSWER = State()


class GameControlStates(StatesGroup):
    """Состояния управления ходом игры"""
    SHOWING_QUESTION = State()
    WAITING_ANSWERS = State()
    REVIEWING_ANSWERS = State()
    SHOWING_RESULTS = State()


class ValidationStates(StatesGroup):
    """Состояния валидации ответов"""
    REVIEWING_ANSWER = State()
    CONFIRMING_VALIDATION = State()