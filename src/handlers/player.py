"""
Обработчики команд для игроков
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from src.settings import settings
from src.sessions.manager import session_manager
from src.storage.user_storage import user_storage
from src.games.engine import game_engine
from src.utils.code_generator import validate_session_code, normalize_session_code


class PlayerHandlers:
    """Обработчики команд для игроков"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start для игрока"""
        user = update.effective_user
        
        # Регистрируем пользователя
        await user_storage.register_user(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        # Проверяем на автоматическое подключение к игре
        if context.args and context.args[0].startswith("join_"):
            session_code = context.args[0][5:]  # Убираем "join_"
            await self._join_session_by_code(update, session_code)
            return
        
        welcome_text = """
🎮 **Добро пожаловать в игрового бота!**

**🎯 Основные команды:**
/join <код> - Подключиться к игре
/leave - Покинуть текущую игру
/status - Статус текущей игры
/score - Мой счет в игре

**👤 Профиль:**
/profile - Мой профиль
/stats - Моя статистика
/leaderboard - Таблица лидеров

**ℹ️ Справка:**
/help - Подробная справка

**🎲 Как играть:**
1. Получите код игры от администратора
2. Введите `/join <код>` для подключения
3. Дождитесь начала игры
4. Отвечайте на вопросы обычными сообщениями

Удачной игры! 🍀
        """
        
        await update.message.reply_text(welcome_text, parse_mode='Markdown')
    
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /help"""
        help_text = """
📚 **Справка по командам**

**🎮 Игровые команды:**
• `/join ABC123` - подключиться к игре по коду
• `/leave` - покинуть текущую игру
• `/status` - узнать статус игры
• `/score` - посмотреть свой счет

**👤 Профиль и статистика:**
• `/profile` - информация о профиле
• `/stats` - личная статистика
• `/leaderboard` - топ игроков

**🎯 Как играть в викторину:**
1. Подключитесь к игре командой `/join <код>`
2. Дождитесь начала игры
3. Отвечайте на вопросы:
   - Для выбора варианта: отправьте номер (1, 2, 3, 4)
   - Для текстового ответа: напишите ответ
   - Для да/нет: напишите "да" или "нет"

**🎲 Как играть в "100 к 1":**
1. Подключитесь к игре
2. Отвечайте на вопросы наиболее популярными ответами
3. Играйте в команде или индивидуально

**💡 Советы:**
• Отвечайте быстро - время ограничено
• Внимательно читайте вопросы
• Следите за счетом в игре

Удачи! 🚀
        """
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def join_session(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /join - подключение к игре"""
        if not context.args:
            await update.message.reply_text(
                "🎯 Укажите код игры: `/join <код>`\n\n"
                "Пример: `/join ABC123`",
                parse_mode='Markdown'
            )
            return
        
        session_code = context.args[0].upper().strip()
        await self._join_session_by_code(update, session_code)
    
    async def _join_session_by_code(self, update: Update, session_code: str):
        """Подключение к сессии по коду"""
        user_id = update.effective_user.id
        
        try:
            # Нормализуем код
            session_code = normalize_session_code(session_code)
            
            # Валидируем код
            if not validate_session_code(session_code):
                await update.message.reply_text(
                    f"❌ Неверный формат кода игры: `{session_code}`\n\n"
                    f"Код должен содержать {settings.session_code_length} символов (буквы и цифры)",
                    parse_mode='Markdown'
                )
                return
            
            # Подключаемся к сессии
            success = await session_manager.join_session(session_code, user_id)
            
            if success:
                # Получаем информацию о сессии
                session = await session_manager.get_session_by_code(session_code)
                
                await update.message.reply_text(
                    f"✅ **Вы подключились к игре!**\n\n"
                    f"🔢 Код игры: `{session_code}`\n"
                    f"🎮 Тип игры: {session.game_type.value}\n"
                    f"👥 Игроков в игре: {len(session.players)}/{session.max_players}\n"
                    f"📊 Статус: {session.status.value}\n\n"
                    f"Ожидайте начала игры... ⏳",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    f"❌ **Не удалось подключиться к игре** `{session_code}`\n\n"
                    f"**Возможные причины:**\n"
                    f"• Неверный код игры\n"
                    f"• Игра уже началась\n"
                    f"• Достигнуто максимальное количество игроков\n"
                    f"• Игра завершена или отменена\n\n"
                    f"Проверьте код и попробуйте снова.",
                    parse_mode='Markdown'
                )
                
        except Exception as e:
            self.logger.error(f"Ошибка подключения к сессии {session_code}: {e}")
            await update.message.reply_text(
                "❌ Произошла ошибка при подключении к игре. Попробуйте позже."
            )
    
    async def leave_session(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /leave - покинуть игру"""
        user_id = update.effective_user.id
        
        try:
            # Находим активные сессии пользователя
            user_sessions = await session_manager.get_player_sessions(user_id)
            active_sessions = [s for s in user_sessions if s.status.value in ["waiting", "active"]]
            
            if not active_sessions:
                await update.message.reply_text("❌ Вы не участвуете ни в одной игре.")
                return
            
            # Если несколько активных сессий, покидаем последнюю
            session = active_sessions[-1]
            
            success = await session_manager.leave_session(session.id, user_id)
            
            if success:
                await update.message.reply_text(
                    f"👋 **Вы покинули игру**\n\n"
                    f"🔢 Код игры: `{session.code}`\n"
                    f"🎮 Тип игры: {session.game_type.value}",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text("❌ Не удалось покинуть игру.")
                
        except Exception as e:
            self.logger.error(f"Ошибка выхода из сессии для пользователя {user_id}: {e}")
            await update.message.reply_text("❌ Произошла ошибка при выходе из игры.")
    
    async def game_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /status - статус игры"""
        user_id = update.effective_user.id
        
        try:
            # Находим активные сессии пользователя
            user_sessions = await session_manager.get_player_sessions(user_id)
            active_sessions = [s for s in user_sessions if s.status.value in ["waiting", "active"]]
            
            if not active_sessions:
                await update.message.reply_text("❌ Вы не участвуете ни в одной игре.")
                return
            
            session = active_sessions[-1]  # Последняя активная сессия
            
            # Получаем состояние игры
            game_state = None
            if session.status.value == "active":
                game_state = await game_engine.get_game_state(session.id)
            
            status_emoji = {
                "waiting": "⏳",
                "active": "🎮",
                "finished": "✅",
                "cancelled": "❌"
            }.get(session.status.value, "❓")
            
            text = f"""
{status_emoji} **Статус игры**

🔢 **Код:** `{session.code}`
🎮 **Тип:** {session.game_type.value}
📊 **Статус:** {session.status.value}
👥 **Игроков:** {len(session.players)}/{session.max_players}
            """
            
            if game_state:
                text += f"\n🎯 **Прогресс игры:**\n"
                text += f"• Раунд: {game_state.get('current_round', 0)}/{game_state.get('total_rounds', 0)}\n"
                
                # Показываем счет игрока
                player_score = game_state.get('scores', {}).get(user_id, 0)
                text += f"• Ваш счет: {player_score}\n"
                
                # Показываем время до конца раунда
                time_remaining = game_state.get('time_remaining')
                if time_remaining is not None:
                    text += f"• Времени осталось: {time_remaining}с\n"
            
            await update.message.reply_text(text, parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f"Ошибка получения статуса игры для пользователя {user_id}: {e}")
            await update.message.reply_text("❌ Ошибка получения статуса игры.")
    
    async def my_score(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /score - мой счет"""
        user_id = update.effective_user.id
        
        try:
            # Находим активные сессии пользователя
            user_sessions = await session_manager.get_player_sessions(user_id)
            active_sessions = [s for s in user_sessions if s.status.value == "active"]
            
            if not active_sessions:
                await update.message.reply_text("❌ Вы не участвуете в активной игре.")
                return
            
            session = active_sessions[-1]
            
            # Получаем состояние игры
            game_state = await game_engine.get_game_state(session.id)
            
            if not game_state:
                await update.message.reply_text("❌ Не удалось получить информацию об игре.")
                return
            
            scores = game_state.get('scores', {})
            player_score = scores.get(user_id, 0)
            
            # Сортируем игроков по счету
            sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            player_position = next((i + 1 for i, (pid, _) in enumerate(sorted_scores) if pid == user_id), 0)
            
            text = f"""
🏆 **Ваш счет в игре**

🔢 **Код игры:** `{session.code}`
🎯 **Ваш счет:** {player_score}
📊 **Позиция:** {player_position} из {len(scores)}

**🏅 Топ игроков:**
            """
            
            # Показываем топ-5
            for i, (pid, score) in enumerate(sorted_scores[:5]):
                emoji = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else "🏅"
                is_you = " (вы)" if pid == user_id else ""
                text += f"{emoji} {score} очков{is_you}\n"
            
            await update.message.reply_text(text, parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f"Ошибка получения счета для пользователя {user_id}: {e}")
            await update.message.reply_text("❌ Ошибка получения счета.")
    
    async def handle_answer(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ответов игрока"""
        user_id = update.effective_user.id
        answer = update.message.text.strip()
        
        try:
            # Находим активные сессии пользователя
            user_sessions = await session_manager.get_player_sessions(user_id)
            active_sessions = [s for s in user_sessions if s.status.value == "active"]
            
            if not active_sessions:
                # Не отвечаем на обычные сообщения если пользователь не в игре
                return
            
            session = active_sessions[-1]
            
            # Обрабатываем ответ через игровой движок
            result = await game_engine.process_answer(session.id, user_id, answer)
            
            if not result:
                await update.message.reply_text("❌ Не удалось обработать ответ.")
                return
            
            if not result.success:
                await update.message.reply_text(f"❌ {result.message}")
                return
            
            # Формируем ответ
            response_text = f"{result.message}"
            
            if result.is_correct is not None:
                if result.is_correct:
                    response_text += f" (+{result.points} очков)"
                else:
                    response_text += f" ({result.points} очков)" if result.points != 0 else ""
            
            # Добавляем объяснение если есть
            if result.explanation:
                response_text += f"\n\n💡 {result.explanation}"
            
            # Показываем правильный ответ если неправильно
            if result.correct_answer and not result.is_correct:
                response_text += f"\n\n✅ Правильный ответ: {result.correct_answer}"
            
            await update.message.reply_text(response_text)
            
            # Обновляем пользовательскую сессию
            await user_storage.update_user_session(
                user_id, session.id, result.points, result.is_correct or False
            )
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки ответа от пользователя {user_id}: {e}")
            await update.message.reply_text("❌ Произошла ошибка при обработке ответа.")
    
    async def profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /profile - профиль пользователя"""
        user_id = update.effective_user.id
        
        try:
            user = await user_storage.get_user(user_id)
            
            if not user:
                await update.message.reply_text("❌ Профиль не найден.")
                return
            
            text = f"""
👤 **Ваш профиль**

**📝 Основная информация:**
• Имя: {user.display_name}
• ID: `{user.telegram_id}`
• Роль: {user.role.value}

**🎮 Игровая статистика:**
• Игр сыграно: {user.games_played}
• Игр выиграно: {user.games_won}
• Процент побед: {user.win_rate:.1f}%
• Общий счет: {user.total_score}

**📅 Активность:**
• Зарегистрирован: {user.created_at.strftime('%d.%m.%Y')}
            """
            
            if user.last_active:
                text += f"• Последняя активность: {user.last_active.strftime('%d.%m.%Y %H:%M')}"
            
            await update.message.reply_text(text, parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f"Ошибка получения профиля пользователя {user_id}: {e}")
            await update.message.reply_text("❌ Ошибка получения профиля.")
    
    async def my_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /stats - статистика пользователя"""
        user_id = update.effective_user.id
        
        try:
            stats = await user_storage.get_user_stats(user_id)
            
            if not stats:
                await update.message.reply_text("❌ Статистика не найдена.")
                return
            
            text = f"""
📊 **Ваша статистика**

**🎮 Игры:**
• Всего игр: {stats.games_played}
• Побед: {stats.games_won}
• Процент побед: {stats.win_rate:.1f}%

**🏆 Очки:**
• Общий счет: {stats.total_score}
• Средний счет: {stats.average_score:.1f}
• Лучший результат: {stats.best_score}

**📈 Прогресс:**
• Любимый тип игр: {stats.favorite_game_type or 'Не определен'}
            """
            
            if stats.last_game_date:
                text += f"• Последняя игра: {stats.last_game_date.strftime('%d.%m.%Y %H:%M')}"
            
            await update.message.reply_text(text, parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f"Ошибка получения статистики пользователя {user_id}: {e}")
            await update.message.reply_text("❌ Ошибка получения статистики.")
    
    async def leaderboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /leaderboard - таблица лидеров"""
        try:
            leaderboard = await user_storage.get_leaderboard(10)
            
            if not leaderboard:
                await update.message.reply_text("📊 Таблица лидеров пуста.")
                return
            
            text = "🏆 **Таблица лидеров**\n\n"
            
            for i, user in enumerate(leaderboard):
                emoji = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."
                
                text += f"{emoji} **{user.display_name}**\n"
                text += f"   💰 {user.total_score} очков | "
                text += f"🎮 {user.games_played} игр | "
                text += f"🏆 {user.win_rate:.1f}% побед\n\n"
            
            await update.message.reply_text(text, parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f"Ошибка получения таблицы лидеров: {e}")
            await update.message.reply_text("❌ Ошибка получения таблицы лидеров.")
    
    async def unknown_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик неизвестных команд"""
        await update.message.reply_text(
            "❓ Неизвестная команда. Используйте /help для списка доступных команд."
        )