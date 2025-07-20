"""
Admin Bot Main Handlers
Основные обработчики команд администратора
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
import structlog

from ..states import AdminStates
from ..keyboards import MainMenuKeyboard
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
    
    try:
        # Проверяем права администратора
        is_admin = await api_client.check_admin_permissions(user_id)
        
        if not is_admin:
            await message.answer(
                "❌ У вас нет прав администратора.\n\n"
                "Этот бот предназначен только для администраторов игровой системы."
            )
            return
        
        # Регистрируем/обновляем пользователя
        try:
            await api_client.register_user(
                telegram_id=user_id,
                username=username,
                first_name=first_name,
                last_name=last_name
            )
        except APIClientError:
            # Пользователь уже существует, это нормально
            pass
        
        # Устанавливаем состояние главного меню
        await state.set_state(AdminStates.MAIN_MENU)
        
        welcome_text = (
            f"👋 Добро пожаловать, {first_name}!\n\n"
            "🎮 Вы в панели администратора игровой системы.\n\n"
            "Здесь вы можете:\n"
            "• Создавать и управлять играми\n"
            "• Запускать игровые сессии\n"
            "• Контролировать ход игры\n"
            "• Валидировать ответы игроков\n\n"
            "Выберите действие:"
        )
        
        await message.answer(
            welcome_text,
            reply_markup=MainMenuKeyboard.get_main_menu()
        )
        
        logger.info(f"Admin {user_id} ({username}) started the bot")
        
    except APIClientError as e:
        logger.error(f"API error in start handler: {e}")
        await message.answer(
            "❌ Ошибка подключения к системе. Попробуйте позже."
        )


@router.callback_query(F.data == "back_to_main")
async def back_to_main_handler(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню"""
    await state.set_state(AdminStates.MAIN_MENU)
    
    await callback.message.edit_text(
        "🏠 Главное меню\n\nВыберите действие:",
        reply_markup=MainMenuKeyboard.get_main_menu()
    )
    
    await callback.answer()


@router.message(Command("help"))
async def help_handler(message: Message):
    """Обработчик команды /help"""
    help_text = (
        "🆘 <b>Справка по командам</b>\n\n"
        
        "<b>Основные команды:</b>\n"
        "/start - Запуск бота и главное меню\n"
        "/help - Показать эту справку\n"
        "/status - Статус активных сессий\n"
        "/cancel - Отменить текущее действие\n\n"
        
        "<b>Управление играми:</b>\n"
        "• Создание игр из JSON паков\n"
        "• Редактирование существующих игр\n"
        "• Просмотр статистики игр\n\n"
        
        "<b>Управление сессиями:</b>\n"
        "• Запуск игровых сессий\n"
        "• Контроль хода игры\n"
        "• Управление вопросами\n"
        "• Валидация ответов игроков\n\n"
        
        "<b>Поддерживаемые типы игр:</b>\n"
        "• Викторина (quiz)\n"
        "• 100 к одному (family_feud)\n\n"
        
        "Для начала работы используйте /start"
    )
    
    await message.answer(help_text, parse_mode="HTML")


@router.message(Command("status"))
async def status_handler(message: Message, api_client: APIClient):
    """Обработчик команды /status"""
    user_id = message.from_user.id
    
    try:
        # Получаем активные сессии пользователя
        sessions = await api_client.get_user_sessions(user_id, status="active")
        
        if not sessions:
            await message.answer("📊 У вас нет активных сессий")
            return
        
        status_text = "📊 <b>Ваши активные сессии:</b>\n\n"
        
        for session in sessions:
            status_emoji = {
                "waiting": "⏳",
                "in_progress": "🎮",
                "paused": "⏸️"
            }.get(session.get('status', 'unknown'), "❓")
            
            status_text += (
                f"{status_emoji} <b>{session.get('game_title', 'Неизвестная игра')}</b>\n"
                f"   Код: <code>{session.get('session_code', 'N/A')}</code>\n"
                f"   Игроков: {session.get('players_count', 0)}\n"
                f"   Статус: {session.get('status', 'unknown')}\n\n"
            )
        
        await message.answer(status_text, parse_mode="HTML")
        
    except APIClientError as e:
        logger.error(f"Error getting status: {e}")
        await message.answer("❌ Ошибка получения статуса")


@router.message(Command("cancel"))
async def cancel_handler(message: Message, state: FSMContext):
    """Обработчик команды /cancel"""
    current_state = await state.get_state()
    
    if current_state is None:
        await message.answer("Нет активных действий для отмены")
        return
    
    await state.clear()
    await state.set_state(AdminStates.MAIN_MENU)
    
    await message.answer(
        "❌ Действие отменено\n\nВозвращаемся в главное меню:",
        reply_markup=MainMenuKeyboard.get_main_menu()
    )


@router.callback_query(F.data == "statistics")
async def statistics_handler(callback: CallbackQuery, api_client: APIClient):
    """Обработчик статистики"""
    user_id = callback.from_user.id
    
    try:
        # Получаем статистику пользователя
        games = await api_client.get_user_games(user_id)
        sessions = await api_client.get_user_sessions(user_id)
        
        total_games = len(games)
        total_sessions = len(sessions)
        active_sessions = len([s for s in sessions if s.get('status') in ['waiting', 'in_progress', 'paused']])
        
        stats_text = (
            "📊 <b>Ваша статистика:</b>\n\n"
            f"🎮 Всего игр: {total_games}\n"
            f"🚀 Всего сессий: {total_sessions}\n"
            f"⚡ Активных сессий: {active_sessions}\n\n"
        )
        
        if games:
            game_types = {}
            for game in games:
                game_type = game.get('game_type', 'unknown')
                game_types[game_type] = game_types.get(game_type, 0) + 1
            
            stats_text += "<b>По типам игр:</b>\n"
            for game_type, count in game_types.items():
                type_name = {
                    'quiz': 'Викторины',
                    'family_feud': '100 к одному'
                }.get(game_type, game_type)
                stats_text += f"• {type_name}: {count}\n"
        
        await callback.message.edit_text(
            stats_text,
            parse_mode="HTML",
            reply_markup=MainMenuKeyboard.get_back_button()
        )
        
    except APIClientError as e:
        logger.error(f"Error getting statistics: {e}")
        await callback.answer("❌ Ошибка получения статистики", show_alert=True)
    
    await callback.answer()


@router.message(F.text)
async def unknown_message_handler(message: Message, state: FSMContext):
    """Обработчик неизвестных сообщений"""
    current_state = await state.get_state()
    
    # Если пользователь не в состоянии ввода данных, показываем помощь
    if current_state in [AdminStates.MAIN_MENU, None]:
        await message.answer(
            "❓ Неизвестная команда.\n\n"
            "Используйте кнопки меню или команду /help для получения справки.",
            reply_markup=MainMenuKeyboard.get_main_menu()
        )


@router.callback_query()
async def unknown_callback_handler(callback: CallbackQuery):
    """Обработчик неизвестных callback'ов"""
    await callback.answer("❓ Неизвестное действие", show_alert=True)