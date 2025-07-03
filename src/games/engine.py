"""
Игровой движок для управления играми
"""
from typing import Dict, Optional, Any
import logging
from datetime import datetime

from src.games.base import BaseGame
from src.games.quiz.game import QuizGame
from src.models.game import GameResults, RoundData, AnswerResult
from src.models.enums import GameType


class GameEngine:
    """Движок для управления играми"""
    
    def __init__(self):
        self.active_games: Dict[str, BaseGame] = {}
        self.logger = logging.getLogger(__name__)
        
        # Регистрация доступных типов игр
        self._game_classes = {
            GameType.QUIZ: QuizGame,
            # GameType.HUNDRED_TO_ONE: HundredToOneGame,  # Будет добавлено позже
        }
    
    async def initialize_game(self, session_id: str, game_type: str, pack_data: Dict[str, Any]) -> bool:
        """
        Инициализация новой игры
        
        Args:
            session_id: ID сессии
            game_type: Тип игры
            pack_data: Данные игрового пака
            
        Returns:
            True если игра успешно инициализирована
        """
        try:
            # Проверяем, что игра для этой сессии еще не создана
            if session_id in self.active_games:
                self.logger.warning(f"Игра для сессии {session_id} уже существует")
                return False
            
            # Получаем класс игры
            game_class = self._game_classes.get(GameType(game_type))
            if not game_class:
                self.logger.error(f"Неизвестный тип игры: {game_type}")
                return False
            
            # Создаем экземпляр игры
            game = game_class(session_id, pack_data)
            
            # Инициализируем игру
            await game.initialize()
            
            # Сохраняем в активных играх
            self.active_games[session_id] = game
            
            self.logger.info(f"Игра {game_type} для сессии {session_id} инициализирована")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка инициализации игры {game_type} для сессии {session_id}: {e}")
            return False
    
    async def start_game(self, session_id: str) -> bool:
        """
        Запуск игры
        
        Args:
            session_id: ID сессии
            
        Returns:
            True если игра успешно запущена
        """
        game = self.active_games.get(session_id)
        if not game:
            self.logger.error(f"Игра для сессии {session_id} не найдена")
            return False
        
        try:
            success = await game.start_game()
            if success:
                self.logger.info(f"Игра для сессии {session_id} запущена")
            return success
        except Exception as e:
            self.logger.error(f"Ошибка запуска игры для сессии {session_id}: {e}")
            return False
    
    async def start_round(self, session_id: str) -> Optional[RoundData]:
        """
        Начало нового раунда
        
        Args:
            session_id: ID сессии
            
        Returns:
            Данные раунда или None
        """
        game = self.active_games.get(session_id)
        if not game:
            self.logger.error(f"Игра для сессии {session_id} не найдена")
            return None
        
        try:
            return await game.start_round()
        except Exception as e:
            self.logger.error(f"Ошибка начала раунда для сессии {session_id}: {e}")
            return None
    
    async def process_answer(self, session_id: str, user_id: int, answer: str) -> Optional[AnswerResult]:
        """
        Обработка ответа игрока
        
        Args:
            session_id: ID сессии
            user_id: ID пользователя
            answer: Ответ пользователя
            
        Returns:
            Результат обработки ответа
        """
        game = self.active_games.get(session_id)
        if not game:
            self.logger.error(f"Игра для сессии {session_id} не найдена")
            return None
        
        try:
            return await game.process_answer(user_id, answer)
        except Exception as e:
            self.logger.error(f"Ошибка обработки ответа для сессии {session_id}: {e}")
            return AnswerResult(
                success=False,
                message="Произошла ошибка при обработке ответа"
            )
    
    async def next_round(self, session_id: str) -> Optional[RoundData]:
        """
        Переход к следующему раунду
        
        Args:
            session_id: ID сессии
            
        Returns:
            Данные следующего раунда или None если игра завершена
        """
        game = self.active_games.get(session_id)
        if not game:
            self.logger.error(f"Игра для сессии {session_id} не найдена")
            return None
        
        try:
            return await game.next_round()
        except Exception as e:
            self.logger.error(f"Ошибка перехода к следующему раунду для сессии {session_id}: {e}")
            return None
    
    async def finish_game(self, session_id: str) -> Optional[GameResults]:
        """
        Завершение игры
        
        Args:
            session_id: ID сессии
            
        Returns:
            Результаты игры
        """
        game = self.active_games.get(session_id)
        if not game:
            self.logger.error(f"Игра для сессии {session_id} не найдена")
            return None
        
        try:
            results = await game.finish_game()
            self.logger.info(f"Игра для сессии {session_id} завершена")
            return results
        except Exception as e:
            self.logger.error(f"Ошибка завершения игры для сессии {session_id}: {e}")
            return None
    
    async def get_game_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Получение состояния игры
        
        Args:
            session_id: ID сессии
            
        Returns:
            Состояние игры
        """
        game = self.active_games.get(session_id)
        if not game:
            return None
        
        try:
            return await game.get_current_state()
        except Exception as e:
            self.logger.error(f"Ошибка получения состояния игры для сессии {session_id}: {e}")
            return None
    
    def add_player_to_game(self, session_id: str, user_id: int) -> bool:
        """
        Добавление игрока в игру
        
        Args:
            session_id: ID сессии
            user_id: ID пользователя
            
        Returns:
            True если игрок добавлен
        """
        game = self.active_games.get(session_id)
        if not game:
            return False
        
        try:
            game.add_player(user_id)
            self.logger.info(f"Игрок {user_id} добавлен в игру сессии {session_id}")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка добавления игрока {user_id} в игру сессии {session_id}: {e}")
            return False
    
    def remove_player_from_game(self, session_id: str, user_id: int) -> bool:
        """
        Удаление игрока из игры
        
        Args:
            session_id: ID сессии
            user_id: ID пользователя
            
        Returns:
            True если игрок удален
        """
        game = self.active_games.get(session_id)
        if not game:
            return False
        
        try:
            game.remove_player(user_id)
            self.logger.info(f"Игрок {user_id} удален из игры сессии {session_id}")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка удаления игрока {user_id} из игры сессии {session_id}: {e}")
            return False
    
    async def pause_game(self, session_id: str) -> bool:
        """
        Приостановка игры
        
        Args:
            session_id: ID сессии
            
        Returns:
            True если игра приостановлена
        """
        game = self.active_games.get(session_id)
        if not game:
            return False
        
        try:
            return await game.pause_game()
        except Exception as e:
            self.logger.error(f"Ошибка приостановки игры для сессии {session_id}: {e}")
            return False
    
    async def resume_game(self, session_id: str) -> bool:
        """
        Возобновление игры
        
        Args:
            session_id: ID сессии
            
        Returns:
            True если игра возобновлена
        """
        game = self.active_games.get(session_id)
        if not game:
            return False
        
        try:
            return await game.resume_game()
        except Exception as e:
            self.logger.error(f"Ошибка возобновления игры для сессии {session_id}: {e}")
            return False
    
    async def cleanup_game(self, session_id: str) -> bool:
        """
        Очистка игры из памяти
        
        Args:
            session_id: ID сессии
            
        Returns:
            True если игра очищена
        """
        if session_id in self.active_games:
            try:
                game = self.active_games[session_id]
                if not game.is_finished():
                    await game.end_game()
                
                del self.active_games[session_id]
                self.logger.info(f"Игра для сессии {session_id} очищена из памяти")
                return True
            except Exception as e:
                self.logger.error(f"Ошибка очистки игры для сессии {session_id}: {e}")
                return False
        
        return True  # Игра уже отсутствует
    
    def get_active_games_count(self) -> int:
        """Получение количества активных игр"""
        return len(self.active_games)
    
    def get_active_sessions(self) -> list[str]:
        """Получение списка активных сессий"""
        return list(self.active_games.keys())
    
    def is_game_active(self, session_id: str) -> bool:
        """Проверка, активна ли игра"""
        game = self.active_games.get(session_id)
        return game is not None and game.is_active()
    
    def register_game_type(self, game_type: GameType, game_class: type) -> None:
        """
        Регистрация нового типа игры
        
        Args:
            game_type: Тип игры
            game_class: Класс игры
        """
        self._game_classes[game_type] = game_class
        self.logger.info(f"Зарегистрирован новый тип игры: {game_type}")
    
    def get_supported_game_types(self) -> list[GameType]:
        """Получение списка поддерживаемых типов игр"""
        return list(self._game_classes.keys())


# Глобальный экземпляр игрового движка
game_engine = GameEngine()