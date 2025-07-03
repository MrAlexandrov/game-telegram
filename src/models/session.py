"""
Модель игровой сессии
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, List, Optional, Any
from .enums import SessionStatus, GameType


class Session(BaseModel):
    """Модель игровой сессии"""
    
    id: str = Field(..., description="Уникальный ID сессии")
    code: str = Field(..., description="Код для подключения к сессии")
    admin_id: int = Field(..., description="ID администратора сессии")
    game_pack_id: str = Field(..., description="ID игрового пака")
    game_type: GameType = Field(..., description="Тип игры")
    
    # Статус и состояние
    status: SessionStatus = Field(SessionStatus.WAITING, description="Статус сессии")
    current_round: int = Field(0, description="Текущий раунд")
    
    # Участники
    players: List[int] = Field(default_factory=list, description="Список ID игроков")
    max_players: int = Field(50, description="Максимальное количество игроков")
    
    # Временные метки
    created_at: datetime = Field(default_factory=datetime.now, description="Время создания")
    started_at: Optional[datetime] = Field(None, description="Время начала игры")
    ended_at: Optional[datetime] = Field(None, description="Время окончания игры")
    expires_at: Optional[datetime] = Field(None, description="Время истечения сессии")
    
    # Результаты и данные
    results: Optional[Dict[str, Any]] = Field(None, description="Результаты игры")
    game_data: Dict[str, Any] = Field(default_factory=dict, description="Данные игры")
    
    # Настройки сессии
    settings: Dict[str, Any] = Field(default_factory=dict, description="Настройки сессии")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
    
    @property
    def is_active(self) -> bool:
        """Проверка, активна ли сессия"""
        return self.status == SessionStatus.ACTIVE
    
    @property
    def is_waiting(self) -> bool:
        """Проверка, ожидает ли сессия игроков"""
        return self.status == SessionStatus.WAITING
    
    @property
    def is_finished(self) -> bool:
        """Проверка, завершена ли сессия"""
        return self.status in [SessionStatus.FINISHED, SessionStatus.CANCELLED]
    
    @property
    def players_count(self) -> int:
        """Количество подключенных игроков"""
        return len(self.players)
    
    @property
    def can_join(self) -> bool:
        """Можно ли подключиться к сессии"""
        return (
            self.status == SessionStatus.WAITING and
            self.players_count < self.max_players
        )
    
    @property
    def duration(self) -> Optional[int]:
        """Длительность игры в секундах"""
        if self.started_at and self.ended_at:
            return int((self.ended_at - self.started_at).total_seconds())
        return None
    
    def add_player(self, user_id: int) -> bool:
        """Добавление игрока в сессию"""
        if not self.can_join or user_id in self.players:
            return False
        
        self.players.append(user_id)
        return True
    
    def remove_player(self, user_id: int) -> bool:
        """Удаление игрока из сессии"""
        if user_id in self.players:
            self.players.remove(user_id)
            return True
        return False
    
    def start_session(self) -> bool:
        """Запуск сессии"""
        if self.status != SessionStatus.WAITING:
            return False
        
        self.status = SessionStatus.ACTIVE
        self.started_at = datetime.now()
        return True
    
    def finish_session(self, results: Optional[Dict[str, Any]] = None) -> bool:
        """Завершение сессии"""
        if self.status != SessionStatus.ACTIVE:
            return False
        
        self.status = SessionStatus.FINISHED
        self.ended_at = datetime.now()
        if results:
            self.results = results
        return True
    
    def cancel_session(self) -> bool:
        """Отмена сессии"""
        if self.is_finished:
            return False
        
        self.status = SessionStatus.CANCELLED
        self.ended_at = datetime.now()
        return True


class SessionInfo(BaseModel):
    """Краткая информация о сессии"""
    
    id: str
    code: str
    game_type: GameType
    status: SessionStatus
    players_count: int
    max_players: int
    created_at: datetime
    admin_id: int
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SessionStats(BaseModel):
    """Статистика сессии"""
    
    session_id: str
    total_players: int
    game_duration: Optional[int] = None  # в секундах
    total_rounds: int = 0
    average_score: float = 0.0
    highest_score: int = 0
    lowest_score: int = 0
    completion_rate: float = 0.0  # процент игроков, завершивших игру
    
    # Статистика по раундам
    rounds_stats: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Статистика по игрокам
    players_stats: List[Dict[str, Any]] = Field(default_factory=list)


class ActiveSession(BaseModel):
    """Активная сессия с дополнительной информацией"""
    
    session: Session
    game_state: Optional[Dict[str, Any]] = None
    current_players: List[Dict[str, Any]] = Field(default_factory=list)
    last_activity: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def update_activity(self):
        """Обновление времени последней активности"""
        self.last_activity = datetime.now()