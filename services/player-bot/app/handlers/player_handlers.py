"""
Player Bot Main Handlers
Основные обработчики команд игроков
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
import structlog
import re

from ..states import PlayerStates, GameJoinStates
from ..keyboards import MainMenuKeyboard, GameJoinKeyboard
from ..services.api_client import APIClient, APIClientError

logger = structlog.get_logger()
router = Router()


@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext, api_client: APIClient):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    
    # Проверяем, есть ли код сессии в параметрах start
    args = message.text.split()[1:] if len(message.text.split()) > 1 else []
    session_code = args[0] if args else None
    
    try:
        # Регистрируем/обновляем игрока
        try:
            await api_client.register_player(
                telegram_id=user_id,
                username=username,
                first_name=first_name,
                last_name=last_name
            )
        except APIClientError:
            # Игрок уже существует, это нормально
            pass
        
        # Если есть код сессии, сразу пытаемся подключиться
        if session_code and len(session_code) >= 6:
            session_info = await api_client.get_session_info(session_code.upper())
            
            if session_info:
                await state.set_state(GameJoinStates.CONFIRMING_JOIN)
                await state.update_data(session_code=session_code.upper())
                
                await message.answer(
                    f"🎮 <b>Подключение к игре</b>\n\n"
                    f"<b>Игра:</b> {session_info.get('game_title', 'Неизвестная игра')}\n"
                    f"<b>Код:</b> <code>{session_code.upper()}</code>\n"
                    f"<b>Игроков:</b> {session_info.get('players_count', 0)}\n"
                    f"<b>Статус:</b> {session_info.get('status', 'unknown')}\n\n"
                    "Присоединиться к этой игре?",
                    parse_mode="HTML",
                    reply_markup=GameJoinKeyboard.get_join_confirmation(
                        session_code.upper(), 
                        session_info.get('game_title', 'Игра')
                    )
                )
                return
        
        # Обычное приветствие
        await state.set_state(PlayerStates.MAIN_MENU)
        
        welcome_text = (
            f"👋 Привет, {first_name}!\n\n"
            "🎮 Добро пожаловать в игровую систему!\n\n"
            "Здесь ты можешь:\n"
            "• Присоединяться к играм по коду или QR-коду\n"
            "• Отвечать на вопросы и зарабатывать очки\n"
            "• Соревноваться с другими игроками\n"
            "• Просматривать свою статистику\n\n"
            "Что хочешь делать?"
        )
        
        await message.answer(
            welcome_text,
            reply_markup=MainMenuKeyboard.get_main_menu()
        )
        
        logger.info(f"Player {user_id} ({username}) started the bot")
        
    except APIClientError as e:
        logger.error(f"API error in start handler: {e}")
        await message.answer(
            "❌ Ошибка подключения к системе. Попробуйте позже."
        )


@router.callback_query(F.data == "back_to_main")
async def back_to_main_handler(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню"""
    await state.set_state(PlayerStates.MAIN_MENU)
    
    await callback.message.edit_text(
        "🏠 Главное меню\n\nВыберите действие:",
        reply_markup=MainMenuKeyboard.get_main_menu()
    )
    
    await callback.answer()


@router.message(Command("help"))
async def help_handler(message: Message):
    """Обработчик команды /help"""
    help_text = (
        "🆘 <b>Справка по игровому боту</b>\n\n"
        
        "<b>Основные команды:</b>\n"
        "/start - Запуск бота и главное меню\n"
        "/join <код> - Присоединиться к игре по коду\n"
        "/score - Показать текущий счет\n"
        "/help - Показать эту справку\n"
        "/cancel - Отменить текущее действие\n\n"
        
        "<b>Как играть:</b>\n"
        "1. Получите код игры от администратора\n"
        "2. Введите код или отсканируйте QR-код\n"
        "3. Дождитесь начала игры\n"
        "4. Отвечайте на вопросы быстро и правильно\n"
        "5. Зарабатывайте очки и побеждайте!\n\n"
        
        "<b>Типы вопросов:</b>\n"
        "• Выбор из вариантов - нажмите кнопку\n"
        "• Текстовый ответ - напишите ответ\n"
        "• Правда/Ложь - выберите вариант\n\n"
        
        "Удачи в игре! 🍀"
    )
    
    await message.answer(help_text, parse_mode="HTML")


@router.callback_query(F.data == "help")
async def help_callback_handler(callback: CallbackQuery):
    """Обработчик кнопки помощи"""
    await callback.message.edit_text(
        "ℹ️ <b>Помощь</b>\n\nВыберите раздел:",
        parse_mode="HTML",
        reply_markup=MainMenuKeyboard.get_help_menu()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("help_"))
async def help_section_handler(callback: CallbackQuery):
    """Обработчик разделов помощи"""
    section = callback.data.split("_", 1)[1]
    
    help_texts = {
        "how_to_play": (
            "🎯 <b>Как играть</b>\n\n"
            "1. <b>Подключение:</b>\n"
            "   • Получите код игры от администратора\n"
            "   • Нажмите 'Присоединиться к игре'\n"
            "   • Введите код или отсканируйте QR\n\n"
            "2. <b>Ожидание:</b>\n"
            "   • Дождитесь других игроков\n"
            "   • Администратор запустит игру\n\n"
            "3. <b>Игровой процесс:</b>\n"
            "   • Читайте вопросы внимательно\n"
            "   • Отвечайте быстро и точно\n"
            "   • Следите за таймером\n\n"
            "4. <b>Результаты:</b>\n"
            "   • Смотрите свой счет\n"
            "   • Сравнивайтесь с другими\n"
            "   • Радуйтесь победе! 🏆"
        ),
        "game_types": (
            "🎮 <b>Типы игр</b>\n\n"
            "<b>Викторина:</b>\n"
            "• Вопросы с вариантами ответов\n"
            "• Текстовые вопросы\n"
            "• Вопросы Правда/Ложь\n"
            "• Ограничение по времени\n\n"
            "<b>100 к одному:</b>\n"
            "• Угадайте популярные ответы\n"
            "• Чем популярнее ответ, тем больше очков\n"
            "• Несколько раундов\n"
            "• Командная игра\n\n"
            "Каждая игра уникальна и интересна!"
        ),
        "scoring": (
            "🏆 <b>Система очков</b>\n\n"
            "<b>Викторина:</b>\n"
            "• Правильный ответ: +10 очков\n"
            "• Быстрый ответ: бонус +1-5 очков\n"
            "• Неправильный ответ: 0 очков\n"
            "• Пропуск вопроса: 0 очков\n\n"
            "<b>100 к одному:</b>\n"
            "• Очки = популярность ответа\n"
            "• Самый популярный: 40+ очков\n"
            "• Редкий ответ: 1-10 очков\n"
            "• Неправильный: 0 очков\n\n"
            "Стремитесь к максимуму! 🎯"
        )
    }
    
    text = help_texts.get(section, "Раздел не найден")
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=MainMenuKeyboard.get_back_button("help")
    )
    await callback.answer()


@router.message(Command("score"))
async def score_command_handler(message: Message, api_client: APIClient):
    """Обработчик команды /score"""
    user_id = message.from_user.id
    
    try:
        # Проверяем активную сессию
        session = await api_client.get_player_session(user_id)
        
        if session:
            # Получаем текущий счет в игре
            score_data = await api_client.get_player_score(session['id'], user_id)
            
            score_text = (
                f"📊 <b>Ваш текущий счет</b>\n\n"
                f"<b>Игра:</b> {session.get('game_title', 'Неизвестная')}\n"
                f"<b>Очки:</b> {score_data.get('score', 0)}\n"
                f"<b>Правильных ответов:</b> {score_data.get('correct_answers', 0)}\n"
                f"<b>Всего ответов:</b> {score_data.get('total_answers', 0)}\n"
            )
            
            if score_data.get('total_answers', 0) > 0:
                accuracy = round((score_data.get('correct_answers', 0) / score_data['total_answers']) * 100, 1)
                score_text += f"<b>Точность:</b> {accuracy}%\n"
            
            # Получаем позицию в таблице лидеров
            leaderboard = await api_client.get_session_leaderboard(session['id'])
            position = next((i + 1 for i, p in enumerate(leaderboard) if p.get('telegram_id') == user_id), None)
            
            if position:
                score_text += f"<b>Позиция:</b> {position} из {len(leaderboard)}"
        else:
            # Общая статистика игрока
            stats = await api_client.get_player_stats(user_id)
            
            if stats:
                score_text = (
                    f"📊 <b>Ваша общая статистика</b>\n\n"
                    f"<b>Игр сыграно:</b> {stats.get('games_played', 0)}\n"
                    f"<b>Побед:</b> {stats.get('games_won', 0)}\n"
                    f"<b>Общий счет:</b> {stats.get('total_score', 0)}\n"
                    f"<b>Правильных ответов:</b> {stats.get('correct_answers', 0)}\n"
                )
                
                if stats.get('games_played', 0) > 0:
                    win_rate = round((stats.get('games_won', 0) / stats['games_played']) * 100, 1)
                    score_text += f"<b>Процент побед:</b> {win_rate}%"
            else:
                score_text = (
                    "📊 <b>Статистика</b>\n\n"
                    "Вы еще не играли в игры.\n"
                    "Присоединитесь к игре, чтобы начать зарабатывать очки!"
                )
        
        await message.answer(score_text, parse_mode="HTML")
        
    except APIClientError as e:
        logger.error(f"Error getting score: {e}")
        await message.answer("❌ Ошибка получения статистики")


@router.message(Command("cancel"))
async def cancel_handler(message: Message, state: FSMContext):
    """Обработчик команды /cancel"""
    current_state = await state.get_state()
    
    if current_state is None:
        await message.answer("Нет активных действий для отмены")
        return
    
    await state.clear()
    await state.set_state(PlayerStates.MAIN_MENU)
    
    await message.answer(
        "❌ Действие отменено\n\nВозвращаемся в главное меню:",
        reply_markup=MainMenuKeyboard.get_main_menu()
    )


@router.callback_query(F.data == "my_score")
async def my_score_callback_handler(callback: CallbackQuery, api_client: APIClient):
    """Обработчик кнопки "Мой счет" """
    # Используем ту же логику, что и в команде /score
    await score_command_handler(callback.message, api_client)
    await callback.answer()


@router.message(F.text.regexp(r"^🎮\s*(.+)"))
async def quick_join_handler(message: Message, state: FSMContext):
    """Быстрое подключение через reply кнопку"""
    if "ввести код" in message.text.lower():
        await state.set_state(GameJoinStates.ENTERING_CODE)
        
        await message.answer(
            "🔤 <b>Подключение к игре</b>\n\n"
            "Введите код игры (6-8 символов):\n\n"
            "Код можно получить от администратора игры "
            "или отсканировать QR-код.",
            parse_mode="HTML",
            reply_markup=MainMenuKeyboard.get_back_button("back_to_main")
        )


@router.message(F.text)
async def unknown_message_handler(message: Message, state: FSMContext):
    """Обработчик неизвестных сообщений"""
    current_state = await state.get_state()
    
    # Если пользователь не в состоянии ввода данных, показываем помощь
    if current_state in [PlayerStates.MAIN_MENU, None]:
        # Проверяем, не код ли это игры
        text = message.text.strip().upper()
        if re.match(r'^[A-Z0-9]{6,8}$', text):
            await state.set_state(GameJoinStates.ENTERING_CODE)
            # Обрабатываем как код игры
            from .game_handlers import process_game_code
            await process_game_code(message, state, message.bot.get("api_client"))
            return
        
        await message.answer(
            "❓ Не понимаю команду.\n\n"
            "Используйте кнопки меню или команду /help для получения справки.",
            reply_markup=MainMenuKeyboard.get_main_menu()
        )


@router.callback_query()
async def unknown_callback_handler(callback: CallbackQuery):
    """Обработчик неизвестных callback'ов"""
    await callback.answer("❓ Неизвестное действие", show_alert=True)