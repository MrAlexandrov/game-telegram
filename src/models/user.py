"""
Модель пользователя
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from .enums import UserRole


class User(BaseModel):
    """Модель пользователя"""
    
    telegram_id: int = Field(..., description="ID пользователя в Telegram")
    username: Optional[str] = Field(None, description="Username в Telegram")
    first_name: Optional[str] = Field(None, description="Имя пользователя")
    last_name: Optional[str] = Field(None, description="Фамилия пользователя")
    role: UserRole = Field(UserRole.PLAYER, description="Роль пользователя")
    is_admin: bool = Field(False, description="Является ли администратором")
    created_at: datetime = Field(default_factory=datetime.now, description="Время создания")
    last_active: Optional[datetime] = Field(None, description="Последняя активность")
    
    # Статистика
    games_played: int = Field(0, description="Количество сыгранных игр")
    games_won: int = Field(0, description="Количество выигранных игр")
    total_score: int = Field(0, description="Общий счет")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
        
    @property
    def display_name(self) -> str:
        """Отображаемое имя пользователя"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.username:
            return f"@{self.username}"
        else:
            return f"User {self.telegram_id}"
    
    @property
    def win_rate(self) -> float:
        """Процент побед"""
        if self.games_played == 0:
            return 0.0
        return (self.games_won / self.games_played) * 100
    
    def update_activity(self) -> None:
        """Обновление времени последней активности"""
        self.last_active = datetime.now()
    
    def add_game_result(self, won: bool, score: int) -> None:
        """Добавление результата игры"""
        self.games_played += 1
        if won:
            self.games_won += 1
        self.total_score += score
        self.update_activity()


class UserStats(BaseModel):
    """Статистика пользователя"""
    
    user_id: int
    games_played: int = 0
    games_won: int = 0
    total_score: int = 0
    average_score: float = 0.0
    win_rate: float = 0.0
    favorite_game_type: Optional[str] = None
    best_score: int = 0
    last_game_date: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class UserSession(BaseModel):
    """Информация о пользователе в сессии"""
    
    user_id: int
    session_id: str
    joined_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = True
    current_score: int = 0
    answers_count: int = 0
    correct_answers: int = 0
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @property
    def accuracy(self) -> float:
        """Точность ответов в процентах"""
        if self.answers_count == 0:
            return 0.0
        return (self.correct_answers / self.answers_count) * 100