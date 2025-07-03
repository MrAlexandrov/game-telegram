"""
Модели для игр
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from .enums import GameType, QuestionType, RoundType


class Question(BaseModel):
    """Модель вопроса для викторины"""
    
    id: int = Field(..., description="ID вопроса")
    question: str = Field(..., description="Текст вопроса")
    type: QuestionType = Field(..., description="Тип вопроса")
    points: int = Field(10, description="Количество очков за правильный ответ")
    time_limit: Optional[int] = Field(None, description="Лимит времени в секундах")
    
    # Для multiple_choice
    options: Optional[List[str]] = Field(None, description="Варианты ответов")
    correct_answer: Optional[Union[int, bool, str, float]] = Field(None, description="Правильный ответ")
    
    # Для text_input
    correct_answers: Optional[List[str]] = Field(None, description="Список правильных ответов")
    case_sensitive: bool = Field(False, description="Учитывать регистр")
    
    # Дополнительные поля
    explanation: Optional[str] = Field(None, description="Объяснение ответа")
    hint: Optional[str] = Field(None, description="Подсказка")
    image_url: Optional[str] = Field(None, description="URL изображения")
    audio_url: Optional[str] = Field(None, description="URL аудио")
    
    # Для numeric
    tolerance: Optional[float] = Field(None, description="Допустимая погрешность для числовых ответов")


class Answer(BaseModel):
    """Модель ответа в игре 100 к 1"""
    
    text: str = Field(..., description="Текст ответа")
    points: int = Field(..., description="Количество очков")
    is_revealed: bool = Field(False, description="Открыт ли ответ")


class Round(BaseModel):
    """Модель раунда для игры 100 к 1"""
    
    id: int = Field(..., description="ID раунда")
    question: str = Field(..., description="Вопрос раунда")
    type: RoundType = Field(RoundType.SIMPLE, description="Тип раунда")
    answers: List[Answer] = Field(..., description="Список ответов")
    alternative_answers: Optional[Dict[str, List[str]]] = Field(None, description="Альтернативные варианты ответов")


class GamePack(BaseModel):
    """Модель игрового пака"""
    
    id: Optional[str] = Field(None, description="ID пака")
    name: str = Field(..., description="Название пака")
    description: str = Field(..., description="Описание пака")
    type: GameType = Field(..., description="Тип игры")
    author: Optional[str] = Field(None, description="Автор пака")
    difficulty: Optional[str] = Field(None, description="Сложность")
    estimated_time: Optional[int] = Field(None, description="Примерное время игры в минутах")
    
    # Настройки игры
    settings: Dict[str, Any] = Field(default_factory=dict, description="Настройки игры")
    
    # Данные игры
    questions: Optional[List[Question]] = Field(None, description="Вопросы для викторины")
    rounds: Optional[List[Round]] = Field(None, description="Раунды для 100 к 1")
    
    # Метаданные
    created_at: datetime = Field(default_factory=datetime.now, description="Время создания")
    created_by: Optional[int] = Field(None, description="ID создателя")
    version: str = Field("1.0", description="Версия пака")
    tags: List[str] = Field(default_factory=list, description="Теги")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class GameStateData(BaseModel):
    """Состояние игры"""
    
    session_id: str
    game_type: GameType
    state: str  # Используем строку вместо enum для избежания конфликта
    current_round: int = 0
    total_rounds: int = 0
    players_scores: Dict[int, int] = Field(default_factory=dict)
    current_question: Optional[Question] = None
    current_round_data: Optional[Round] = None
    round_start_time: Optional[datetime] = None
    game_data: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class RoundData(BaseModel):
    """Данные раунда для отправки игрокам"""
    
    round_number: int
    question: str
    options: Optional[List[str]] = None
    time_limit: Optional[int] = None
    round_type: Optional[str] = None
    image_url: Optional[str] = None
    audio_url: Optional[str] = None
    hint: Optional[str] = None


class AnswerResult(BaseModel):
    """Результат обработки ответа"""
    
    success: bool
    is_correct: Optional[bool] = None
    points: int = 0
    message: str = ""
    explanation: Optional[str] = None
    correct_answer: Optional[str] = None


class GameResults(BaseModel):
    """Результаты игры"""
    
    session_id: str
    game_type: GameType
    total_rounds: int
    players_results: List[tuple[int, int]]  # [(user_id, score), ...]
    winner: Optional[int] = None
    game_duration: Optional[int] = None  # в секундах
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    statistics: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class PlayerResult(BaseModel):
    """Результат игрока"""
    
    user_id: int
    username: Optional[str] = None
    display_name: str
    total_score: int = 0
    correct_answers: int = 0
    total_answers: int = 0
    accuracy: float = 0.0
    rank: int = 0
    
    @property
    def accuracy_percentage(self) -> float:
        """Точность в процентах"""
        if self.total_answers == 0:
            return 0.0
        return (self.correct_answers / self.total_answers) * 100