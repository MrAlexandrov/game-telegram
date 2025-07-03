"""
Основной менеджер ботов
"""
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram import Update
from telegram.ext import ContextTypes

from src.settings import settings
from src.handlers.admin import AdminHandlers
from src.handlers.player import PlayerHandlers
from src.handlers.common import CommonHandlers


class BotManager:
    """Менеджер для управления ботами"""
    
    def __init__(self):
        self.admin_app: Application = None
        self.player_app: Application = None
        self.logger = logging.getLogger(__name__)
        
        # Обработчики команд
        self.admin_handlers = AdminHandlers() if settings.is_admin_mode() else None
        self.player_handlers = PlayerHandlers() if settings.is_player_mode() else None
        self.common_handlers = CommonHandlers()
    
    async def initialize(self):
        """Инициализация ботов"""
        try:
            # Создаем приложения для ботов в зависимости от режима
            if settings.is_admin_mode():
                self.admin_app = Application.builder().token(settings.admin_bot_token).build()
                self._setup_admin_handlers()
                self.logger.info("Админский бот инициализирован")
            
            if settings.is_player_mode():
                self.player_app = Application.builder().token(settings.player_bot_token).build()
                self._setup_player_handlers()
                self.logger.info("Игровой бот инициализирован")
            
            self.logger.info(f"Боты инициализированы в режиме: {settings.mode}")
            
        except Exception as e:
            self.logger.error(f"Ошибка инициализации ботов: {e}")
            raise
    
    def _setup_admin_handlers(self):
        """Настройка обработчиков для админского бота"""
        try:
            # Основные команды
            self.admin_app.add_handler(CommandHandler("start", self.admin_handlers.start))
            self.admin_app.add_handler(CommandHandler("help", self.admin_handlers.help))
            self.admin_app.add_handler(CommandHandler("status", self.admin_handlers.status))
            
            # Управление паками
            self.admin_app.add_handler(CommandHandler("list_packs", self.admin_handlers.list_packs))
            self.admin_app.add_handler(CommandHandler("pack_info", self.admin_handlers.pack_info))
            self.admin_app.add_handler(CommandHandler("search_packs", self.admin_handlers.search_packs))
            
            # Управление сессиями
            self.admin_app.add_handler(CommandHandler("create_session", self.admin_handlers.create_session))
            self.admin_app.add_handler(CommandHandler("start_game", self.admin_handlers.start_game))
            self.admin_app.add_handler(CommandHandler("end_game", self.admin_handlers.end_game))
            self.admin_app.add_handler(CommandHandler("cancel_game", self.admin_handlers.cancel_game))
            self.admin_app.add_handler(CommandHandler("session_info", self.admin_handlers.session_info))
            self.admin_app.add_handler(CommandHandler("my_sessions", self.admin_handlers.my_sessions))
            self.admin_app.add_handler(CommandHandler("active_sessions", self.admin_handlers.active_sessions))
            
            # Статистика и мониторинг
            self.admin_app.add_handler(CommandHandler("stats", self.admin_handlers.stats))
            self.admin_app.add_handler(CommandHandler("cleanup", self.admin_handlers.cleanup))
            
            # Обработчик неизвестных команд
            self.admin_app.add_handler(MessageHandler(filters.COMMAND, self.admin_handlers.unknown_command))
            
            # Обработчик ошибок
            self.admin_app.add_error_handler(self._error_handler)
            
            self.logger.info("Обработчики админского бота настроены")
            
        except Exception as e:
            self.logger.error(f"Ошибка настройки обработчиков админского бота: {e}")
            raise
    
    def _setup_player_handlers(self):
        """Настройка обработчиков для игрового бота"""
        try:
            # Основные команды
            self.player_app.add_handler(CommandHandler("start", self.player_handlers.start))
            self.player_app.add_handler(CommandHandler("help", self.player_handlers.help))
            
            # Игровые команды
            self.player_app.add_handler(CommandHandler("join", self.player_handlers.join_session))
            self.player_app.add_handler(CommandHandler("leave", self.player_handlers.leave_session))
            self.player_app.add_handler(CommandHandler("status", self.player_handlers.game_status))
            self.player_app.add_handler(CommandHandler("score", self.player_handlers.my_score))
            
            # Пользовательские команды
            self.player_app.add_handler(CommandHandler("profile", self.player_handlers.profile))
            self.player_app.add_handler(CommandHandler("stats", self.player_handlers.my_stats))
            self.player_app.add_handler(CommandHandler("leaderboard", self.player_handlers.leaderboard))
            
            # Обработчик текстовых сообщений (ответы на вопросы)
            self.player_app.add_handler(MessageHandler(
                filters.TEXT & ~filters.COMMAND, 
                self.player_handlers.handle_answer
            ))
            
            # Обработчик неизвестных команд
            self.player_app.add_handler(MessageHandler(filters.COMMAND, self.player_handlers.unknown_command))
            
            # Обработчик ошибок
            self.player_app.add_error_handler(self._error_handler)
            
            self.logger.info("Обработчики игрового бота настроены")
            
        except Exception as e:
            self.logger.error(f"Ошибка настройки обработчиков игрового бота: {e}")
            raise
    
    async def _error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик ошибок"""
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
    
    async def start(self):
        """Запуск ботов"""
        try:
            # Инициализируем и запускаем админского бота
            if self.admin_app:
                await self.admin_app.initialize()
                await self.admin_app.start()
                await self.admin_app.updater.start_polling(
                    drop_pending_updates=True,
                    allowed_updates=["message", "callback_query"]
                )
                
                admin_bot = await self.admin_app.bot.get_me()
                self.logger.info(f"Админский бот запущен: @{admin_bot.username} ({admin_bot.first_name})")
                settings.admin_bot_username = admin_bot.username
            
            # Инициализируем и запускаем игрового бота
            if self.player_app:
                await self.player_app.initialize()
                await self.player_app.start()
                await self.player_app.updater.start_polling(
                    drop_pending_updates=True,
                    allowed_updates=["message", "callback_query"]
                )
                
                player_bot = await self.player_app.bot.get_me()
                self.logger.info(f"Игровой бот запущен: @{player_bot.username} ({player_bot.first_name})")
                settings.player_bot_username = player_bot.username
            
            self.logger.info(f"Боты запущены в режиме: {settings.mode}")
            
        except Exception as e:
            self.logger.error(f"Ошибка запуска ботов: {e}")
            raise
    
    async def stop(self):
        """Остановка ботов"""
        try:
            self.logger.info("Остановка ботов...")
            
            # Останавливаем polling
            if self.admin_app and self.admin_app.updater:
                await self.admin_app.updater.stop()
            if self.player_app and self.player_app.updater:
                await self.player_app.updater.stop()
            
            # Останавливаем приложения
            if self.admin_app:
                await self.admin_app.stop()
                await self.admin_app.shutdown()
            if self.player_app:
                await self.player_app.stop()
                await self.player_app.shutdown()
            
            self.logger.info("Боты остановлены")
            
        except Exception as e:
            self.logger.error(f"Ошибка остановки ботов: {e}")
    
    def get_admin_bot(self):
        """Получение админского бота"""
        return self.admin_app.bot if self.admin_app else None
    
    def get_player_bot(self):
        """Получение игрового бота"""
        return self.player_app.bot if self.player_app else None
    
    async def send_admin_message(self, message: str):
        """Отправка сообщения администратору"""
        try:
            if self.admin_app:
                await self.admin_app.bot.send_message(
                    chat_id=settings.root_id,
                    text=message
                )
        except Exception as e:
            self.logger.error(f"Ошибка отправки сообщения администратору: {e}")
    
    async def send_player_message(self, user_id: int, message: str):
        """Отправка сообщения игроку"""
        try:
            if self.player_app:
                await self.player_app.bot.send_message(
                    chat_id=user_id,
                    text=message
                )
        except Exception as e:
            self.logger.error(f"Ошибка отправки сообщения игроку {user_id}: {e}")
    
    async def broadcast_to_session(self, session_id: str, message: str):
        """Рассылка сообщения всем игрокам сессии"""
        try:
            from src.sessions.manager import session_manager
            
            session = await session_manager.get_session_info(session_id)
            if not session:
                return
            
            # Получаем полную информацию о сессии
            full_session = await session_manager.session_storage.get_session(session_id)
            if not full_session:
                return
            
            # Отправляем сообщение всем игрокам
            for player_id in full_session.players:
                try:
                    await self.send_player_message(player_id, message)
                except Exception as e:
                    self.logger.error(f"Ошибка отправки сообщения игроку {player_id}: {e}")
            
        except Exception as e:
            self.logger.error(f"Ошибка рассылки сообщения для сессии {session_id}: {e}")