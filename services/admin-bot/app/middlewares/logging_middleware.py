"""
Logging Middleware for Admin Bot
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
                        await api_client.update_user_activity(event.from_user.id)
                    except Exception as e:
                        logger.warning(f"Failed to update user activity for {event.from_user.id}: {e}")
            
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
                chat_id=event.chat.id,
                message_type=event.content_type,
                text=event.text[:100] if event.text else None,
                has_document=bool(event.document),
                has_photo=bool(event.photo)
            )
        elif isinstance(event, CallbackQuery):
            logger.info(
                "Incoming callback query",
                user_id=event.from_user.id if event.from_user else None,
                username=event.from_user.username if event.from_user else None,
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


class AdminActionLogger:
    """Логгер для действий администратора"""
    
    @staticmethod
    def log_game_created(admin_id: int, game_id: str, game_title: str):
        """Логирование создания игры"""
        logger.info(
            "Game created",
            admin_id=admin_id,
            game_id=game_id,
            game_title=game_title,
            action="game_created"
        )
    
    @staticmethod
    def log_session_started(admin_id: int, session_id: str, game_title: str):
        """Логирование запуска сессии"""
        logger.info(
            "Session started",
            admin_id=admin_id,
            session_id=session_id,
            game_title=game_title,
            action="session_started"
        )
    
    @staticmethod
    def log_game_started(admin_id: int, session_id: str, players_count: int):
        """Логирование начала игры"""
        logger.info(
            "Game started",
            admin_id=admin_id,
            session_id=session_id,
            players_count=players_count,
            action="game_started"
        )
    
    @staticmethod
    def log_question_sent(admin_id: int, session_id: str, question_id: str, question_num: int):
        """Логирование отправки вопроса"""
        logger.info(
            "Question sent",
            admin_id=admin_id,
            session_id=session_id,
            question_id=question_id,
            question_num=question_num,
            action="question_sent"
        )
    
    @staticmethod
    def log_answer_validated(admin_id: int, answer_id: str, is_correct: bool, points: int = None):
        """Логирование валидации ответа"""
        logger.info(
            "Answer validated",
            admin_id=admin_id,
            answer_id=answer_id,
            is_correct=is_correct,
            points=points,
            action="answer_validated"
        )
    
    @staticmethod
    def log_game_finished(admin_id: int, session_id: str, players_count: int, duration_minutes: float = None):
        """Логирование завершения игры"""
        logger.info(
            "Game finished",
            admin_id=admin_id,
            session_id=session_id,
            players_count=players_count,
            duration_minutes=duration_minutes,
            action="game_finished"
        )
    
    @staticmethod
    def log_game_deleted(admin_id: int, game_id: str, game_title: str):
        """Логирование удаления игры"""
        logger.warning(
            "Game deleted",
            admin_id=admin_id,
            game_id=game_id,
            game_title=game_title,
            action="game_deleted"
        )
    
    @staticmethod
    def log_session_deleted(admin_id: int, session_id: str):
        """Логирование удаления сессии"""
        logger.warning(
            "Session deleted",
            admin_id=admin_id,
            session_id=session_id,
            action="session_deleted"
        )
    
    @staticmethod
    def log_file_uploaded(admin_id: int, filename: str, file_size: int, file_type: str):
        """Логирование загрузки файла"""
        logger.info(
            "File uploaded",
            admin_id=admin_id,
            filename=filename,
            file_size=file_size,
            file_type=file_type,
            action="file_uploaded"
        )
    
    @staticmethod
    def log_unauthorized_access(user_id: int, username: str = None, action: str = None):
        """Логирование попытки несанкционированного доступа"""
        logger.warning(
            "Unauthorized access attempt",
            user_id=user_id,
            username=username,
            attempted_action=action,
            action="unauthorized_access"
        )