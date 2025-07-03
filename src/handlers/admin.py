"""
Обработчики команд для администратора
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from typing import List

from src.settings import settings
from src.sessions.manager import session_manager
from src.storage.pack_storage import pack_storage
from src.storage.user_storage import user_storage
from src.storage.session_storage import session_storage
from src.games.engine import game_engine


class AdminHandlers:
    """Обработчики команд для администратора"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start для администратора"""
        user_id = update.effective_user.id
        
        if user_id != settings.root_id:
            await update.message.reply_text("❌ У вас нет прав администратора.")
            return
        
        welcome_text = """
🎮 **Добро пожаловать в админ-панель игрового бота!**

**📋 Основные команды:**
/help - Справка по командам
/status - Статус системы

**📦 Управление паками:**
/list_packs - Список игровых паков
/pack_info <pack_id> - Информация о паке
/search_packs <запрос> - Поиск паков

**🎯 Управление сессиями:**
/create_session <pack_id> - Создать сессию
/start_game <session_id> - Запустить игру
/end_game <session_id> - Завершить игру
/cancel_game <session_id> - Отменить игру
/session_info <session_id> - Информация о сессии
/my_sessions - Мои сессии
/active_sessions - Активные сессии

**📊 Статистика:**
/stats - Общая статистика
/cleanup - Очистка старых данных

Удачного администрирования! 🚀
        """
        
        await update.message.reply_text(welcome_text, parse_mode='Markdown')
    
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /help"""
        user_id = update.effective_user.id
        
        if user_id != settings.root_id:
            await update.message.reply_text("❌ У вас нет прав администратора.")
            return
        
        help_text = """
📚 **Справка по командам администратора**

**🎯 Создание и запуск игры:**
1. `/list_packs` - посмотреть доступные игровые паки
2. `/create_session <pack_id>` - создать сессию
3. Поделиться кодом с игроками
4. `/start_game <session_id>` - запустить игру
5. `/end_game <session_id>` - завершить игру

**📦 Работа с паками:**
• `/pack_info quiz_1` - информация о паке
• `/search_packs история` - поиск паков по ключевому слову

**🔍 Мониторинг:**
• `/session_info <session_id>` - детали сессии
• `/active_sessions` - все активные игры
• `/stats` - статистика системы

**🧹 Обслуживание:**
• `/cleanup` - очистка старых данных
• `/status` - состояние системы

**💡 Советы:**
- Коды сессий генерируются автоматически
- QR-коды создаются для быстрого подключения
- Сессии автоматически истекают через час
        """
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /status - статус системы"""
        user_id = update.effective_user.id
        
        if user_id != settings.root_id:
            await update.message.reply_text("❌ У вас нет прав администратора.")
            return
        
        try:
            # Получаем статистику
            active_sessions = await session_storage.get_active_sessions()
            waiting_sessions = await session_storage.get_waiting_sessions()
            total_users = user_storage.get_users_count()
            active_games = game_engine.get_active_games_count()
            
            status_text = f"""
🔍 **Статус системы**

**🎮 Игры:**
• Активных игр: {active_games}
• Активных сессий: {len(active_sessions)}
• Сессий в ожидании: {len(waiting_sessions)}

**👥 Пользователи:**
• Всего пользователей: {total_users}

**⚙️ Настройки:**
• Макс. игроков в сессии: {settings.max_players_per_session}
• Таймаут сессии: {settings.session_timeout_minutes} мин
• Длина кода: {settings.session_code_length}

**🤖 Боты:**
• Админский бот: ✅ Работает
• Игровой бот: ✅ Работает

Система работает нормально! 🟢
            """
            
            await update.message.reply_text(status_text, parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f"Ошибка получения статуса: {e}")
            await update.message.reply_text("❌ Ошибка получения статуса системы.")
    
    async def list_packs(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /list_packs - список игровых паков"""
        user_id = update.effective_user.id
        
        if user_id != settings.root_id:
            await update.message.reply_text("❌ У вас нет прав администратора.")
            return
        
        try:
            packs = await pack_storage.list_packs()
            
            if not packs:
                await update.message.reply_text("📦 Игровые паки не найдены.")
                return
            
            # Группируем по типам
            quiz_packs = [p for p in packs if p["type"] == "quiz"]
            hundred_packs = [p for p in packs if p["type"] == "hundred_to_one"]
            
            text = "📦 **Доступные игровые паки:**\n\n"
            
            if quiz_packs:
                text += "🧠 **Викторины:**\n"
                for pack in quiz_packs[:10]:  # Показываем первые 10
                    questions_count = pack.get("questions_count", "?")
                    text += f"• `{pack['id']}` - {pack['name']} ({questions_count} вопросов)\n"
                text += "\n"
            
            if hundred_packs:
                text += "🎯 **100 к 1:**\n"
                for pack in hundred_packs[:10]:
                    rounds_count = pack.get("rounds_count", "?")
                    text += f"• `{pack['id']}` - {pack['name']} ({rounds_count} раундов)\n"
                text += "\n"
            
            text += f"Всего паков: {len(packs)}\n"
            text += "Используйте `/pack_info <id>` для подробной информации"
            
            await update.message.reply_text(text, parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f"Ошибка получения списка паков: {e}")
            await update.message.reply_text("❌ Ошибка получения списка игровых паков.")
    
    async def pack_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /pack_info - информация о паке"""
        user_id = update.effective_user.id
        
        if user_id != settings.root_id:
            await update.message.reply_text("❌ У вас нет прав администратора.")
            return
        
        if not context.args:
            await update.message.reply_text("📦 Укажите ID пака: `/pack_info <pack_id>`", parse_mode='Markdown')
            return
        
        pack_id = context.args[0]
        
        try:
            pack_info = await pack_storage.get_pack_info(pack_id)
            
            if not pack_info:
                await update.message.reply_text(f"❌ Пак `{pack_id}` не найден.", parse_mode='Markdown')
                return
            
            text = f"""
📦 **Информация о паке**

**🏷️ Основное:**
• ID: `{pack_info['id']}`
• Название: {pack_info['name']}
• Тип: {pack_info['type']}
• Описание: {pack_info.get('description', 'Не указано')}

**👤 Автор:** {pack_info.get('author', 'Неизвестен')}
**⭐ Сложность:** {pack_info.get('difficulty', 'Не указана')}
**⏱️ Время игры:** {pack_info.get('estimated_time', '?')} мин

**📊 Содержание:**
            """
            
            if pack_info.get('questions_count'):
                text += f"• Вопросов: {pack_info['questions_count']}\n"
            if pack_info.get('rounds_count'):
                text += f"• Раундов: {pack_info['rounds_count']}\n"
            
            text += f"\n**📅 Создан:** {pack_info.get('created_at', 'Неизвестно')}"
            text += f"\n**🏷️ Теги:** {', '.join(pack_info.get('tags', []))}"
            
            text += f"\n\nДля создания сессии: `/create_session {pack_id}`"
            
            await update.message.reply_text(text, parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f"Ошибка получения информации о паке {pack_id}: {e}")
            await update.message.reply_text("❌ Ошибка получения информации о паке.")
    
    async def create_session(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /create_session - создание сессии"""
        user_id = update.effective_user.id
        
        if user_id != settings.root_id:
            await update.message.reply_text("❌ У вас нет прав администратора.")
            return
        
        if not context.args:
            await update.message.reply_text("🎯 Укажите ID пака: `/create_session <pack_id>`", parse_mode='Markdown')
            return
        
        pack_id = context.args[0]
        
        try:
            # Создаем сессию
            session = await session_manager.create_session(pack_id, user_id)
            
            if not session:
                await update.message.reply_text(f"❌ Не удалось создать сессию для пака `{pack_id}`.", parse_mode='Markdown')
                return
            
            # Генерируем QR-код
            try:
                qr_code = await session_manager.generate_qr_code(session.code)
                
                message_text = f"""
✅ **Сессия создана!**

🆔 **ID сессии:** `{session.id}`
🔢 **Код для подключения:** `{session.code}`
👥 **Игроков:** 0/{session.max_players}
🎮 **Тип игры:** {session.game_type}

**Игроки могут подключиться:**
1. По коду: `/join {session.code}` в боте @{settings.player_bot_username or 'игровом_боте'}
2. По QR-коду (см. ниже)

**Для запуска:** `/start_game {session.id}`
                """
                
                await update.message.reply_text(message_text, parse_mode='Markdown')
                
                # Отправляем QR-код
                await update.message.reply_photo(
                    photo=qr_code,
                    caption=f"🔗 QR-код для подключения к игре `{session.code}`",
                    parse_mode='Markdown'
                )
                
            except Exception as qr_error:
                self.logger.error(f"Ошибка генерации QR-кода: {qr_error}")
                
                message_text = f"""
✅ **Сессия создана!**

🆔 **ID сессии:** `{session.id}`
🔢 **Код для подключения:** `{session.code}`
👥 **Игроков:** 0/{session.max_players}

Игроки могут подключиться командой `/join {session.code}`

**Для запуска:** `/start_game {session.id}`
                """
                
                await update.message.reply_text(message_text, parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f"Ошибка создания сессии: {e}")
            await update.message.reply_text("❌ Произошла ошибка при создании сессии.")
    
    async def start_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start_game - запуск игры"""
        user_id = update.effective_user.id
        
        if user_id != settings.root_id:
            await update.message.reply_text("❌ У вас нет прав администратора.")
            return
        
        if not context.args:
            await update.message.reply_text("🎮 Укажите ID сессии: `/start_game <session_id>`", parse_mode='Markdown')
            return
        
        session_id = context.args[0]
        
        try:
            success = await session_manager.start_session(session_id, user_id)
            
            if success:
                session_info = await session_manager.get_session_info(session_id)
                
                await update.message.reply_text(
                    f"🎮 **Игра запущена!**\n\n"
                    f"🆔 Сессия: `{session_id}`\n"
                    f"👥 Участников: {session_info.players_count}\n"
                    f"🎯 Тип игры: {session_info.game_type}\n\n"
                    f"Игра началась! 🚀",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text("❌ Не удалось запустить игру. Проверьте ID сессии и наличие игроков.")
                
        except Exception as e:
            self.logger.error(f"Ошибка запуска игры: {e}")
            await update.message.reply_text("❌ Произошла ошибка при запуске игры.")
    
    async def end_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /end_game - завершение игры"""
        user_id = update.effective_user.id
        
        if user_id != settings.root_id:
            await update.message.reply_text("❌ У вас нет прав администратора.")
            return
        
        if not context.args:
            await update.message.reply_text("🏁 Укажите ID сессии: `/end_game <session_id>`", parse_mode='Markdown')
            return
        
        session_id = context.args[0]
        
        try:
            results = await session_manager.end_session(session_id, user_id)
            
            if results:
                await update.message.reply_text(
                    f"🏁 **Игра завершена!**\n\n"
                    f"🆔 Сессия: `{session_id}`\n"
                    f"📊 Результаты сохранены\n"
                    f"🧹 Данные очищены",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text("❌ Не удалось завершить игру. Проверьте ID сессии.")
                
        except Exception as e:
            self.logger.error(f"Ошибка завершения игры: {e}")
            await update.message.reply_text("❌ Произошла ошибка при завершении игры.")
    
    async def cancel_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /cancel_game - отмена игры"""
        user_id = update.effective_user.id
        
        if user_id != settings.root_id:
            await update.message.reply_text("❌ У вас нет прав администратора.")
            return
        
        if not context.args:
            await update.message.reply_text("❌ Укажите ID сессии: `/cancel_game <session_id>`", parse_mode='Markdown')
            return
        
        session_id = context.args[0]
        
        try:
            success = await session_manager.cancel_session(session_id, user_id)
            
            if success:
                await update.message.reply_text(
                    f"❌ **Игра отменена**\n\n"
                    f"🆔 Сессия: `{session_id}`\n"
                    f"🧹 Данные очищены",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text("❌ Не удалось отменить игру. Проверьте ID сессии.")
                
        except Exception as e:
            self.logger.error(f"Ошибка отмены игры: {e}")
            await update.message.reply_text("❌ Произошла ошибка при отмене игры.")
    
    async def session_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /session_info - информация о сессии"""
        user_id = update.effective_user.id
        
        if user_id != settings.root_id:
            await update.message.reply_text("❌ У вас нет прав администратора.")
            return
        
        if not context.args:
            await update.message.reply_text("ℹ️ Укажите ID сессии: `/session_info <session_id>`", parse_mode='Markdown')
            return
        
        session_id = context.args[0]
        
        try:
            session = await session_storage.get_session(session_id)
            
            if not session:
                await update.message.reply_text(f"❌ Сессия `{session_id}` не найдена.", parse_mode='Markdown')
                return
            
            # Получаем состояние игры если активна
            game_state = None
            if session.status.value == "active":
                game_state = await game_engine.get_game_state(session_id)
            
            text = f"""
ℹ️ **Информация о сессии**

🆔 **ID:** `{session.id}`
🔢 **Код:** `{session.code}`
📊 **Статус:** {session.status.value}
🎮 **Тип игры:** {session.game_type.value}
👥 **Игроков:** {len(session.players)}/{session.max_players}

📅 **Создана:** {session.created_at.strftime('%d.%m.%Y %H:%M')}
            """
            
            if session.started_at:
                text += f"🚀 **Запущена:** {session.started_at.strftime('%d.%m.%Y %H:%M')}\n"
            
            if session.ended_at:
                text += f"🏁 **Завершена:** {session.ended_at.strftime('%d.%m.%Y %H:%M')}\n"
            
            if game_state:
                text += f"\n🎯 **Состояние игры:**\n"
                text += f"• Раунд: {game_state.get('current_round', 0)}/{game_state.get('total_rounds', 0)}\n"
                text += f"• Ответов в раунде: {game_state.get('round_answers_count', 0)}\n"
            
            if session.players:
                text += f"\n👥 **Игроки:** {', '.join(map(str, session.players))}"
            
            await update.message.reply_text(text, parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f"Ошибка получения информации о сессии: {e}")
            await update.message.reply_text("❌ Ошибка получения информации о сессии.")
    
    async def my_sessions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /my_sessions - мои сессии"""
        user_id = update.effective_user.id
        
        if user_id != settings.root_id:
            await update.message.reply_text("❌ У вас нет прав администратора.")
            return
        
        try:
            sessions = await session_manager.get_admin_sessions(user_id)
            
            if not sessions:
                await update.message.reply_text("📋 У вас нет созданных сессий.")
                return
            
            text = "📋 **Ваши сессии:**\n\n"
            
            for session in sessions[-10:]:  # Последние 10
                status_emoji = {
                    "waiting": "⏳",
                    "active": "🎮",
                    "finished": "✅",
                    "cancelled": "❌"
                }.get(session.status.value, "❓")
                
                text += f"{status_emoji} `{session.id}`\n"
                text += f"   Код: `{session.code}` | Игроков: {len(session.players)}\n"
                text += f"   {session.game_type.value} | {session.created_at.strftime('%d.%m %H:%M')}\n\n"
            
            await update.message.reply_text(text, parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f"Ошибка получения сессий администратора: {e}")
            await update.message.reply_text("❌ Ошибка получения списка сессий.")
    
    async def active_sessions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /active_sessions - активные сессии"""
        user_id = update.effective_user.id
        
        if user_id != settings.root_id:
            await update.message.reply_text("❌ У вас нет прав администратора.")
            return
        
        try:
            active_sessions = await session_storage.get_active_sessions()
            waiting_sessions = await session_storage.get_waiting_sessions()
            
            text = "🎮 **Активные сессии:**\n\n"
            
            if active_sessions:
                for session in active_sessions:
                    text += f"🎮 `{session.id}`\n"
                    text += f"   Код: `{session.code}` | Игроков: {len(session.players)}\n"
                    text += f"   {session.game_type.value} | Админ: {session.admin_id}\n\n"
            else:
                text += "Нет активных игр\n\n"
            
            text += "⏳ **Ожидают запуска:**\n\n"
            
            if waiting_sessions:
                for session in waiting_sessions:
                    text += f"⏳ `{session.id}`\n"
                    text += f"   Код: `{session.code}` | Игроков: {len(session.players)}\n"
                    text += f"   {session.game_type.value} | Админ: {session.admin_id}\n\n"
            else:
                text += "Нет сессий в ожидании"
            
            await update.message.reply_text(text, parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f"Ошибка получения активных сессий: {e}")
            await update.message.reply_text("❌ Ошибка получения списка активных сессий.")
    
    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /stats - статистика"""
        user_id = update.effective_user.id
        
        if user_id != settings.root_id:
            await update.message.reply_text("❌ У вас нет прав администратора.")
            return
        
        try:
            # Получаем статистику
            session_stats = await session_storage.get_session_stats()
            user_stats = await user_storage.get_user_statistics()
            pack_stats = await pack_storage.get_stats()
            
            text = f"""
📊 **Статистика системы**

**🎮 Сессии:**
• Всего: {session_stats.get('total_sessions', 0)}
• Активных: {session_stats.get('by_status', {}).get('active', 0)}
• В ожидании: {session_stats.get('by_status', {}).get('waiting', 0)}
• Завершенных: {session_stats.get('by_status', {}).get('finished', 0)}

**👥 Пользователи:**
• Всего: {user_stats.get('total_users', 0)}
• Администраторов: {user_stats.get('admins_count', 0)}
• Игроков: {user_stats.get('players_count', 0)}
• Активных: {user_stats.get('active_users', 0)}

**📦 Игровые паки:**
• Всего: {pack_stats.get('total_packs', 0)}
• Викторин: {pack_stats.get('by_type', {}).get('quiz', 0)}
• "100 к 1": {pack_stats.get('by_type', {}).get('hundred_to_one', 0)}

**🎯 Игры:**
• Всего сыграно: {user_stats.get('total_games_played', 0)}
• Общий счет: {user_stats.get('total_score', 0)}
• Среднее на игрока: {user_stats.get('average_games_per_user', 0):.1f}
            """
            
            await update.message.reply_text(text, parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f"Ошибка получения статистики: {e}")
            await update.message.reply_text("❌ Ошибка получения статистики.")
    
    async def cleanup(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /cleanup - очистка данных"""
        user_id = update.effective_user.id
        
        if user_id != settings.root_id:
            await update.message.reply_text("❌ У вас нет прав администратора.")
            return
        
        try:
            # Очищаем истекшие сессии
            cleaned_sessions = await session_manager.cleanup_expired_sessions()
            
            # Очищаем старые QR-коды
            from src.utils.qr_generator import qr_generator
            cleaned_qr = qr_generator.cleanup_old_qr_codes(24)
            
            text = f"""
🧹 **Очистка завершена**

• Очищено сессий: {cleaned_sessions}
• Удалено QR-кодов: {cleaned_qr}

Система очищена! ✨
            """
            
            await update.message.reply_text(text, parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f"Ошибка очистки данных: {e}")
            await update.message.reply_text("❌ Ошибка при очистке данных.")
    
    async def search_packs(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /search_packs - поиск паков"""
        user_id = update.effective_user.id
        
        if user_id != settings.root_id:
            await update.message.reply_text("❌ У вас нет прав администратора.")
            return
        
        if not context.args:
            await update.message.reply_text("🔍 Укажите поисковый запрос: `/search_packs <запрос>`", parse_mode='Markdown')
            return
        
        query = " ".join(context.args)
        
        try:
            found_packs = await pack_storage.search_packs(query)
            
            if not found_packs:
                await update.message.reply_text(f"🔍 По запросу `{query}` ничего не найдено.", parse_mode='Markdown')
                return
            
            text = f"🔍 **Результаты поиска по запросу:** `{query}`\n\n"
            
            for pack in found_packs[:10]:  # Первые 10 результатов
                content_info = ""
                if pack.get("questions_count"):
                    content_info = f"({pack['questions_count']} вопросов)"
                elif pack.get("rounds_count"):
                    content_info = f"({pack['rounds_count']} раундов)"
                
                text += f"• `{pack['id']}` - {pack['name']} {content_info}\n"
                text += f"  {pack.get('description', '')[:50]}...\n\n"
            
            if len(found_packs) > 10:
                text += f"... и еще {len(found_packs) - 10} результатов"
            
            await update.message.reply_text(text, parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f"Ошибка поиска паков: {e}")
            await update.message.reply_text("❌ Ошибка при поиске игровых паков.")
    
    async def unknown_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик неизвестных команд"""
        user_id = update.effective_user.id
        
        if user_id != settings.root_id:
            await update.message.reply_text("❌ У вас нет прав администратора.")
            return
        
        await update.message.reply_text(
            "❓ Неизвестная команда. Используйте /help для списка доступных команд."
        )