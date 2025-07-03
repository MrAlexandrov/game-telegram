"""
Общие обработчики команд
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes


class CommonHandlers:
    """Общие обработчики команд для обоих ботов"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Общий обработчик ошибок"""
        try:
            self.logger.error(f"Ошибка в боте: {context.error}", exc_info=context.error)
            
            # Отправляем сообщение пользователю если возможно
            if update and update.effective_chat:
                try:
                    await update.effective_chat.send_message(
                        "😔 Произошла ошибка. Попробуйте позже или обратитесь к администратору."
                    )
                except Exception:
                    pass  # Игнорируем ошибки отправки сообщения об ошибке
                    
        except Exception as e:
            self.logger.error(f"Ошибка в обработчике ошибок: {e}")
    
    async def maintenance_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Сообщение о технических работах"""
        await update.message.reply_text(
            "🔧 Ведутся технические работы. Попробуйте позже."
        )
    
    async def rate_limit_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Сообщение о превышении лимита запросов"""
        await update.message.reply_text(
            "⏱️ Слишком много запросов. Подождите немного и попробуйте снова."
        )