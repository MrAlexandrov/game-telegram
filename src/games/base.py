"""
Базовый класс для всех игр
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio

from src.models.game import GameStateData, RoundData, AnswerResult, GameResults
from src.models.enums import GameState as GameStateEnum


class BaseGame(ABC):
    """Базовый абстрактный класс для всех игр"""
    
    def __init__(self, session_id: str, pack_data: Dict[str, Any]):
        """
        Инициализация игры
        
        Args:
            session_id: ID сессии
            pack_data: Данные игрового пака
        """
        self.session_id = session_id
        self.pack_data = pack_data
        self.current_round = 0
        self.players_scores: Dict[int, int] = {}
        self.game_state = GameStateEnum.WAITING
        self.started_at: Optional[datetime] = None
        self.finished_at: Optional[datetime] = None
        
        # Настройки игры из пака
        self.settings = pack_data.get("settings", {})
        self.name = pack_data.get("name", "Неизвестная игра")
        self.description = pack_data.get("description", "")
    
    @abstractmethod
    async def initialize(self) -> None:
        """Инициализация игры перед началом"""
        pass
    
    @abstractmethod
    async def start_round(self) -> Optional[RoundData]:
        """
        Начало нового раунда
        
        Returns:
            Данные раунда или None если раундов больше нет
        """
        pass
    
    @abstractmethod
    async def process_answer(self, user_id: int, answer: str) -> AnswerResult:
        """
        Обработка ответа игрока
        
        Args:
            user_id: ID пользователя
            answer: Ответ пользователя
            
        Returns:
            Результат обработки ответа
        """
        pass
    
    @abstractmethod
    async def next_round(self) -> Optional[RoundData]:
        """
        Переход к следующему раунду
        
        Returns:
            Данные следующего раунда или None если игра завершена
        """
        pass
    
    @abstractmethod
    async def finish_game(self) -> GameResults:
        """
        Завершение игры и подсчет результатов
        
        Returns:
            Результаты игры
        """
        pass
    
    @abstractmethod
    async def get_current_state(self) -> Dict[str, Any]:
        """
        Получение текущего состояния игры
        
        Returns:
            Словарь с состоянием игры
        """
        pass
    
    # Общие методы для всех игр
    
    def add_player(self, user_id: int) -> None:
        """
        Добавление игрока в игру
        
        Args:
            user_id: ID пользователя
        """
        if user_id not in self.players_scores:
            self.players_scores[user_id] = 0
    
    def remove_player(self, user_id: int) -> None:
        """
        Удаление игрока из игры
        
        Args:
            user_id: ID пользователя
        """
        self.players_scores.pop(user_id, None)
    
    def get_players(self) -> List[int]:
        """
        Получение списка игроков
        
        Returns:
            Список ID игроков
        """
        return list(self.players_scores.keys())
    
    def get_player_score(self, user_id: int) -> int:
        """
        Получение счета игрока
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Счет игрока
        """
        return self.players_scores.get(user_id, 0)
    
    def update_player_score(self, user_id: int, points: int) -> None:
        """
        Обновление счета игрока
        
        Args:
            user_id: ID пользователя
            points: Количество очков для добавления
        """
        if user_id in self.players_scores:
            self.players_scores[user_id] += points
    
    def set_player_score(self, user_id: int, score: int) -> None:
        """
        Установка счета игрока
        
        Args:
            user_id: ID пользователя
            score: Новый счет
        """
        if user_id in self.players_scores:
            self.players_scores[user_id] = score
    
    def get_leaderboard(self) -> List[tuple[int, int]]:
        """
        Получение таблицы лидеров
        
        Returns:
            Список кортежей (user_id, score) отсортированный по убыванию счета
        """
        return sorted(
            self.players_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
    
    def get_winner(self) -> Optional[int]:
        """
        Получение победителя
        
        Returns:
            ID победителя или None если нет игроков
        """
        leaderboard = self.get_leaderboard()
        return leaderboard[0][0] if leaderboard else None
    
    async def start_game(self) -> bool:
        """
        Запуск игры
        
        Returns:
            True если игра успешно запущена
        """
        if self.game_state != GameStateEnum.WAITING:
            return False
        
        await self.initialize()
        self.game_state = GameStateEnum.READY
        self.started_at = datetime.now()
        return True
    
    async def end_game(self) -> GameResults:
        """
        Завершение игры
        
        Returns:
            Результаты игры
        """
        if self.game_state not in [GameStateEnum.ACTIVE, GameStateEnum.READY]:
            # Если игра уже завершена, возвращаем пустые результаты
            return GameResults(
                session_id=self.session_id,
                game_type=self.pack_data.get("type", "unknown"),
                total_rounds=self.current_round,
                players_results=[],
                started_at=self.started_at,
                finished_at=datetime.now()
            )
        
        self.game_state = GameStateEnum.FINISHED
        self.finished_at = datetime.now()
        
        return await self.finish_game()
    
    def is_active(self) -> bool:
        """Проверка, активна ли игра"""
        return self.game_state == GameStateEnum.ACTIVE
    
    def is_finished(self) -> bool:
        """Проверка, завершена ли игра"""
        return self.game_state == GameStateEnum.FINISHED
    
    def get_game_duration(self) -> Optional[int]:
        """
        Получение длительности игры в секундах
        
        Returns:
            Длительность в секундах или None если игра не завершена
        """
        if self.started_at and self.finished_at:
            return int((self.finished_at - self.started_at).total_seconds())
        return None
    
    def get_players_count(self) -> int:
        """Получение количества игроков"""
        return len(self.players_scores)
    
    async def pause_game(self) -> bool:
        """
        Приостановка игры
        
        Returns:
            True если игра приостановлена
        """
        if self.game_state == GameStateEnum.ACTIVE:
            self.game_state = GameStateEnum.PAUSED
            return True
        return False
    
    async def resume_game(self) -> bool:
        """
        Возобновление игры
        
        Returns:
            True если игра возобновлена
        """
        if self.game_state == GameStateEnum.PAUSED:
            self.game_state = GameStateEnum.ACTIVE
            return True
        return False