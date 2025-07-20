"""
Logging Middleware for Player Bot
"""

from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
import structlog
import time

logger = structlog.get_logger()


class LoggingMiddleware(BaseMiddleware):
    """Middleware для логирования запросов"""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        start_time = time.time()
        
        # Логируем входящий запрос
        await self.log_incoming_event(event)
        
        try:
            # Обновляем активность пользователя
            if hasattr(event, 'from_user') and event.from_user:
                api_client = data.get("api_client")
                if api_client:
                    try:
                        await api_client.update_player_activity(event.from_user.id)
                    except Exception as e:
                        logger.warning(f"Failed to update player activity for {event.from_user.id}: {e}")
            
            result = await handler(event, data)
            
            # Логируем успешное выполнение
            execution_time = time.time() - start_time
            await self.log_success(event, execution_time)
            
            return result
            
        except Exception as e:
            # Логируем ошибку
            execution_time = time.time() - start_time
            await self.log_error(event, e, execution_time)
            raise
    
    async def log_incoming_event(self, event: TelegramObject):
        """Логирование входящего события"""
        if isinstance(event, Message):
            logger.info(
                "Incoming message",
                user_id=event.from_user.id if event.from_user else None,
                username=event.from_user.username if event.from_user else None,
                first_name=event.from_user.first_name if event.from_user else None,
                chat_id=event.chat.id,
                message_type=event.content_type,
                text=event.text[:100] if event.text else None
            )
        elif isinstance(event, CallbackQuery):
            logger.info(
                "Incoming callback query",
                user_id=event.from_user.id if event.from_user else None,
                username=event.from_user.username if event.from_user else None,
                first_name=event.from_user.first_name if event.from_user else None,
                callback_data=event.data,
                message_id=event.message.message_id if event.message else None
            )
    
    async def log_success(self, event: TelegramObject, execution_time: float):
        """Логирование успешного выполнения"""
        event_type = "message" if isinstance(event, Message) else "callback_query"
        
        logger.info(
            f"Handler executed successfully",
            event_type=event_type,
            execution_time_ms=round(execution_time * 1000, 2),
            user_id=event.from_user.id if event.from_user else None
        )
    
    async def log_error(self, event: TelegramObject, error: Exception, execution_time: float):
        """Логирование ошибки"""
        event_type = "message" if isinstance(event, Message) else "callback_query"
        
        logger.error(
            f"Handler execution failed",
            event_type=event_type,
            execution_time_ms=round(execution_time * 1000, 2),
            user_id=event.from_user.id if event.from_user else None,
            error=str(error),
            error_type=type(error).__name__
        )


class PlayerActionLogger:
    """Логгер для действий игроков"""
    
    @staticmethod
    def log_player_joined(player_id: int, session_id: str, session_code: str, username: str = None):
        """Логирование подключения игрока к игре"""
        logger.info(
            "Player joined game",
            player_id=player_id,
            username=username,
            session_id=session_id,
            session_code=session_code,
            action="player_joined"
        )
    
    @staticmethod
    def log_player_left(player_id: int, session_id: str, username: str = None):
        """Логирование выхода игрока из игры"""
        logger.info(
            "Player left game",
            player_id=player_id,
            username=username,
            session_id=session_id,
            action="player_left"
        )
    
    @staticmethod
    def log_answer_submitted(player_id: int, session_id: str, question_id: str, 
                           answer: str, is_correct: bool = None, points: int = None):
        """Логирование отправки ответа"""
        logger.info(
            "Answer submitted",
            player_id=player_id,
            session_id=session_id,
            question_id=question_id,
            answer=answer[:100],  # Ограничиваем длину ответа в логах
            is_correct=is_correct,
            points=points,
            action="answer_submitted"
        )
    
    @staticmethod
    def log_question_skipped(player_id: int, session_id: str, question_id: str):
        """Логирование пропуска вопроса"""
        logger.info(
            "Question skipped",
            player_id=player_id,
            session_id=session_id,
            question_id=question_id,
            action="question_skipped"
        )
    
    @staticmethod
    def log_game_finished_for_player(player_id: int, session_id: str, final_score: int, 
                                   position: int, total_players: int):
        """Логирование завершения игры для игрока"""
        logger.info(
            "Game finished for player",
            player_id=player_id,
            session_id=session_id,
            final_score=final_score,
            position=position,
            total_players=total_players,
            action="game_finished_for_player"
        )
    
    @staticmethod
    def log_invalid_session_code(player_id: int, session_code: str):
        """Логирование попытки подключения с неверным кодом"""
        logger.warning(
            "Invalid session code attempt",
            player_id=player_id,
            session_code=session_code,
            action="invalid_session_code"
        )
    
    @staticmethod
    def log_connection_error(player_id: int, error_type: str, details: str = None):
        """Логирование ошибки подключения"""
        logger.error(
            "Player connection error",
            player_id=player_id,
            error_type=error_type,
            details=details,
            action="connection_error"
        )
    
    @staticmethod
    def log_answer_timeout(player_id: int, session_id: str, question_id: str):
        """Логирование истечения времени на ответ"""
        logger.warning(
            "Answer timeout",
            player_id=player_id,
            session_id=session_id,
            question_id=question_id,
            action="answer_timeout"
        )
    
    @staticmethod
    def log_reconnection(player_id: int, session_id: str, session_code: str):
        """Логирование переподключения игрока"""
        logger.info(
            "Player reconnected",
            player_id=player_id,
            session_id=session_id,
            session_code=session_code,
            action="player_reconnected"
        )
    
    @staticmethod
    def log_score_viewed(player_id: int, session_id: str = None, current_score: int = None):
        """Логирование просмотра счета"""
        logger.info(
            "Score viewed",
            player_id=player_id,
            session_id=session_id,
            current_score=current_score,
            action="score_viewed"
        )
    
    @staticmethod
    def log_leaderboard_viewed(player_id: int, session_id: str):
        """Логирование просмотра таблицы лидеров"""
        logger.info(
            "Leaderboard viewed",
            player_id=player_id,
            session_id=session_id,
            action="leaderboard_viewed"
        )