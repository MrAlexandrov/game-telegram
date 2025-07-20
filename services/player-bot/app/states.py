"""
Player Bot FSM States
Состояния для управления диалогами игроков
"""

from aiogram.fsm.state import State, StatesGroup


class PlayerStates(StatesGroup):
    """Основные состояния игрока"""
    MAIN_MENU = State()
    WAITING_CONNECTION = State()


class GameJoinStates(StatesGroup):
    """Состояния подключения к игре"""
    ENTERING_CODE = State()
    CONFIRMING_JOIN = State()
    WAITING_GAME_START = State()


class GamePlayStates(StatesGroup):
    """Состояния игрового процесса"""
    IN_GAME = State()
    ANSWERING_QUESTION = State()
    WAITING_NEXT_QUESTION = State()
    VIEWING_RESULTS = State()


class QuestionStates(StatesGroup):
    """Состояния ответа на вопросы"""
    MULTIPLE_CHOICE = State()
    TEXT_INPUT = State()
    TRUE_FALSE = State()
    FAMILY_FEUD = State()


class ResultStates(StatesGroup):
    """Состояния просмотра результатов"""
    CURRENT_SCORE = State()
    LEADERBOARD = State()
    FINAL_RESULTS = State()
