"""
Error Handler Middleware for Player Bot
"""

from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
import structlog
import traceback

logger = structlog.get_logger()


class ErrorHandlerMiddleware(BaseMiddleware):
    """Middleware для обработки ошибок"""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        try:
            return await handler(event, data)
        except Exception as e:
            await self.handle_error(event, e, data)
            return None
    
    async def handle_error(self, event: TelegramObject, error: Exception, data: Dict[str, Any]):
        """Обработка ошибки"""
        user_id = None
        chat_id = None
        
        # Получаем информацию о пользователе и чате
        if isinstance(event, (Message, CallbackQuery)):
            user_id = event.from_user.id if event.from_user else None
            chat_id = event.chat.id if hasattr(event, 'chat') and event.chat else None
            
            if isinstance(event, CallbackQuery) and event.message:
                chat_id = event.message.chat.id
        
        # Логируем ошибку
        logger.error(
            "Unhandled error in handler",
            error=str(error),
            error_type=type(error).__name__,
            user_id=user_id,
            chat_id=chat_id,
            traceback=traceback.format_exc()
        )
        
        # Отправляем сообщение пользователю
        try:
            error_message = self.get_user_friendly_error_message(error)
            
            if isinstance(event, Message):
                await event.answer(error_message)
            elif isinstance(event, CallbackQuery):
                await event.answer(error_message, show_alert=True)
                
        except Exception as send_error:
            logger.error(f"Failed to send error message to user: {send_error}")
    
    def get_user_friendly_error_message(self, error: Exception) -> str:
        """Получить пользовательское сообщение об ошибке"""
        error_messages = {
            "APIClientError": "❌ Ошибка подключения к серверу. Попробуйте позже.",
            "ValidationError": "❌ Ошибка валидации данных. Проверьте введенную информацию.",
            "TimeoutError": "❌ Превышено время ожидания. Попробуйте еще раз.",
            "ValueError": "❌ Неверное значение. Проверьте введенные данные.",
            "KeyError": "❌ Отсутствуют необходимые данные.",
            "ConnectionError": "❌ Ошибка соединения. Проверьте подключение к интернету.",
            "SessionNotFoundError": "❌ Игровая сессия не найдена. Проверьте код игры.",
            "GameFinishedError": "❌ Игра уже завершена.",
            "PlayerNotInGameError": "❌ Вы не участвуете в этой игре.",
            "AnswerTimeoutError": "⏰ Время на ответ истекло.",
            "InvalidAnswerError": "❌ Неверный формат ответа."
        }
        
        error_type = type(error).__name__
        return error_messages.get(error_type, "❌ Произошла неожиданная ошибка. Попробуйте позже.")