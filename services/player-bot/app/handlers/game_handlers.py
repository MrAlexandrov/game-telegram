"""
Game Handlers for Player Bot
Обработчики для подключения к играм и управления игровым процессом
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
import structlog
import re

from ..states import GameJoinStates, GamePlayStates, PlayerStates
from ..keyboards import MainMenuKeyboard, GameJoinKeyboard, GamePlayKeyboard
from ..services.api_client import APIClient, APIClientError

logger = structlog.get_logger()
router = Router()


@router.callback_query(F.data == "join_game")
async def join_game_handler(callback: CallbackQuery, state: FSMContext):
    """Начало подключения к игре"""
    await state.set_state(GameJoinStates.ENTERING_CODE)
    
    await callback.message.edit_text(
        "🎮 <b>Подключение к игре</b>\n\n"
        "Выберите способ подключения:",
        parse_mode="HTML",
        reply_markup=GameJoinKeyboard.get_join_options()
    )
    
    await callback.answer()


@router.callback_query(F.data == "enter_game_code")
async def enter_game_code_handler(callback: CallbackQuery, state: FSMContext):
    """Ввод кода игры"""
    await state.set_state(GameJoinStates.ENTERING_CODE)
    
    await callback.message.edit_text(
        "🔤 <b>Ввод кода игры</b>\n\n"
        "Введите код игры (6-8 символов):\n\n"
        "Код можно получить от администратора игры "
        "или найти в QR-коде.",
        parse_mode="HTML",
        reply_markup=MainMenuKeyboard.get_back_button("join_game")
    )
    
    await callback.answer()


@router.message(F.text, GameJoinStates.ENTERING_CODE)
async def process_game_code(message: Message, state: FSMContext, api_client: APIClient):
    """Обработка введенного кода игры"""
    code = message.text.strip().upper()
    
    # Валидация кода
    if not re.match(r'^[A-Z0-9]{6,8}$', code):
        await message.answer(
            "❌ Неверный формат кода!\n\n"
            "Код должен содержать 6-8 символов (буквы и цифры).\n"
            "Попробуйте еще раз:"
        )
        return
    
    try:
        # Проверяем существование сессии
        session_info = await api_client.get_session_info(code)
        
        if not session_info:
            await message.answer(
                "❌ Игра с таким кодом не найдена!\n\n"
                "Проверьте правильность кода и попробуйте еще раз:"
            )
            return
        
        # Проверяем статус сессии
        if session_info.get('status') not in ['waiting', 'in_progress']:
            status_messages = {
                'finished': 'Игра уже завершена',
                'cancelled': 'Игра была отменена',
                'paused': 'Игра на паузе'
            }
            status_msg = status_messages.get(session_info.get('status'), 'Игра недоступна')
            
            await message.answer(
                f"❌ {status_msg}\n\n"
                "Попробуйте подключиться к другой игре."
            )
            return
        
        # Сохраняем информацию о сессии
        await state.update_data(
            session_code=code,
            session_info=session_info
        )
        await state.set_state(GameJoinStates.CONFIRMING_JOIN)
        
        # Показываем информацию об игре
        game_status = {
            'waiting': 'Ожидание игроков',
            'in_progress': 'Игра идет'
        }.get(session_info.get('status'), 'Неизвестно')
        
        confirm_text = (
            f"🎮 <b>Информация об игре</b>\n\n"
            f"<b>Название:</b> {session_info.get('game_title', 'Неизвестная игра')}\n"
            f"<b>Тип:</b> {session_info.get('game_type', 'unknown')}\n"
            f"<b>Код:</b> <code>{code}</code>\n"
            f"<b>Игроков:</b> {session_info.get('players_count', 0)}\n"
            f"<b>Статус:</b> {game_status}\n\n"
            "Присоединиться к этой игре?"
        )
        
        await message.answer(
            confirm_text,
            parse_mode="HTML",
            reply_markup=GameJoinKeyboard.get_join_confirmation(
                code, 
                session_info.get('game_title', 'Игра')
            )
        )
        
    except APIClientError as e:
        logger.error(f"Error checking session: {e}")
        await message.answer(
            "❌ Ошибка подключения к серверу.\n"
            "Попробуйте позже."
        )


@router.callback_query(F.data.startswith("confirm_join:"))
async def confirm_join_handler(callback: CallbackQuery, state: FSMContext, api_client: APIClient):
    """Подтверждение подключения к игре"""
    session_code = callback.data.split(":", 1)[1]
    user_id = callback.from_user.id
    
    try:
        # Присоединяемся к сессии
        result = await api_client.join_session(session_code, user_id)
        
        await state.set_state(GameJoinStates.WAITING_GAME_START)
        await state.update_data(
            session_id=result['session_id'],
            session_code=session_code
        )
        
        success_text = (
            f"✅ <b>Вы присоединились к игре!</b>\n\n"
            f"<b>Игра:</b> {result.get('game_title', 'Неизвестная')}\n"
            f"<b>Ваш номер:</b> {result.get('player_number', '?')}\n"
            f"<b>Игроков в сессии:</b> {result.get('total_players', 1)}\n\n"
        )
        
        if result.get('game_status') == 'waiting':
            success_text += (
                "⏳ Ожидание начала игры...\n\n"
                "Администратор запустит игру, когда все будут готовы."
            )
        else:
            success_text += (
                "🎮 Игра уже идет!\n\n"
                "Вы присоединились к игре в процессе."
            )
        
        await callback.message.edit_text(
            success_text,
            parse_mode="HTML",
            reply_markup=GameJoinKeyboard.get_waiting_game_start()
        )
        
        logger.info(f"Player {user_id} joined session {session_code}")
        
    except APIClientError as e:
        logger.error(f"Error joining session: {e}")
        
        error_messages = {
            "session_not_found": "Игра не найдена",
            "session_full": "Игра переполнена",
            "already_joined": "Вы уже в этой игре",
            "session_finished": "Игра уже завершена"
        }
        
        error_msg = error_messages.get(str(e), "Ошибка подключения к игре")
        await callback.answer(f"❌ {error_msg}", show_alert=True)
    
    await callback.answer()


@router.callback_query(F.data == "show_players")
async def show_players_handler(callback: CallbackQuery, state: FSMContext, api_client: APIClient):
    """Показать список игроков"""
    state_data = await state.get_data()
    session_id = state_data.get('session_id')
    
    if not session_id:
        await callback.answer("❌ Сессия не найдена", show_alert=True)
        return
    
    try:
        players = await api_client.get_session_players(session_id)
        
        if not players:
            players_text = "👥 <b>Игроки в сессии</b>\n\nПока никого нет."
        else:
            players_text = f"👥 <b>Игроки в сессии ({len(players)})</b>\n\n"
            
            for i, player in enumerate(players, 1):
                status_emoji = "🟢" if player.get('is_online', True) else "🔴"
                score = f" - {player.get('score', 0)} очков" if player.get('score', 0) > 0 else ""
                players_text += f"{i}. {status_emoji} {player['name']}{score}\n"
        
        await callback.message.edit_text(
            players_text,
            parse_mode="HTML",
            reply_markup=GameJoinKeyboard.get_waiting_game_start()
        )
        
    except APIClientError as e:
        logger.error(f"Error getting players: {e}")
        await callback.answer("❌ Ошибка получения списка игроков", show_alert=True)
    
    await callback.answer()


@router.callback_query(F.data == "game_info")
async def game_info_handler(callback: CallbackQuery, state: FSMContext, api_client: APIClient):
    """Информация об игре"""
    state_data = await state.get_data()
    session_info = state_data.get('session_info', {})
    
    game_type_names = {
        'quiz': 'Викторина',
        'family_feud': '100 к одному'
    }
    
    game_type = session_info.get('game_type', 'unknown')
    game_type_name = game_type_names.get(game_type, game_type)
    
    info_text = (
        f"ℹ️ <b>Информация об игре</b>\n\n"
        f"<b>Название:</b> {session_info.get('game_title', 'Неизвестная игра')}\n"
        f"<b>Тип:</b> {game_type_name}\n"
        f"<b>Описание:</b> {session_info.get('description', 'Нет описания')}\n"
    )
    
    if session_info.get('questions_count'):
        info_text += f"<b>Вопросов:</b> {session_info['questions_count']}\n"
    
    if session_info.get('time_limit'):
        info_text += f"<b>Время на ответ:</b> {session_info['time_limit']} сек\n"
    
    # Добавляем правила игры
    if game_type == 'quiz':
        info_text += (
            "\n<b>Правила:</b>\n"
            "• Отвечайте на вопросы быстро и правильно\n"
            "• За правильный ответ получаете очки\n"
            "• Быстрый ответ дает бонусные очки\n"
            "• Следите за таймером!"
        )
    elif game_type == 'family_feud':
        info_text += (
            "\n<b>Правила:</b>\n"
            "• Угадывайте популярные ответы\n"
            "• Чем популярнее ответ, тем больше очков\n"
            "• Несколько раундов\n"
            "• Работайте в команде!"
        )
    
    await callback.message.edit_text(
        info_text,
        parse_mode="HTML",
        reply_markup=GameJoinKeyboard.get_waiting_game_start()
    )
    
    await callback.answer()


@router.callback_query(F.data == "leave_game")
async def leave_game_handler(callback: CallbackQuery, state: FSMContext):
    """Покинуть игру"""
    await callback.message.edit_text(
        "🚪 <b>Покинуть игру</b>\n\n"
        "Вы действительно хотите покинуть игру?\n"
        "Ваш прогресс будет потерян.",
        parse_mode="HTML",
        reply_markup=GameJoinKeyboard.get_leave_confirmation()
    )
    
    await callback.answer()


@router.callback_query(F.data == "confirm_leave")
async def confirm_leave_handler(callback: CallbackQuery, state: FSMContext, api_client: APIClient):
    """Подтверждение выхода из игры"""
    user_id = callback.from_user.id
    state_data = await state.get_data()
    session_id = state_data.get('session_id')
    
    if session_id:
        try:
            await api_client.leave_session(session_id, user_id)
            logger.info(f"Player {user_id} left session {session_id}")
        except APIClientError as e:
            logger.error(f"Error leaving session: {e}")
    
    await state.clear()
    await state.set_state(PlayerStates.MAIN_MENU)
    
    await callback.message.edit_text(
        "👋 Вы покинули игру\n\n"
        "Возвращаемся в главное меню:",
        reply_markup=MainMenuKeyboard.get_main_menu()
    )
    
    await callback.answer("Вы покинули игру")


@router.callback_query(F.data == "cancel_leave")
async def cancel_leave_handler(callback: CallbackQuery):
    """Отмена выхода из игры"""
    await callback.message.edit_text(
        "✅ Остаемся в игре!\n\n"
        "Ожидание начала игры...",
        reply_markup=GameJoinKeyboard.get_waiting_game_start()
    )
    
    await callback.answer("Остаемся в игре")


@router.callback_query(F.data == "scan_qr_info")
async def scan_qr_info_handler(callback: CallbackQuery):
    """Информация о сканировании QR-кода"""
    info_text = (
        "📱 <b>Сканирование QR-кода</b>\n\n"
        "К сожалению, прямое сканирование QR-кода "
        "в Telegram боте невозможно.\n\n"
        "<b>Как использовать QR-код:</b>\n"
        "1. Отсканируйте QR-код камерой телефона\n"
        "2. Перейдите по ссылке\n"
        "3. Бот автоматически подключит вас к игре\n\n"
        "<b>Или:</b>\n"
        "Введите код игры вручную - он указан под QR-кодом."
    )
    
    await callback.message.edit_text(
        info_text,
        parse_mode="HTML",
        reply_markup=GameJoinKeyboard.get_qr_scan_info()
    )
    
    await callback.answer()


@router.callback_query(F.data == "leaderboard")
async def leaderboard_handler(callback: CallbackQuery, state: FSMContext, api_client: APIClient):
    """Таблица лидеров"""
    state_data = await state.get_data()
    session_id = state_data.get('session_id')
    user_id = callback.from_user.id
    
    if not session_id:
        # Показываем общую статистику
        await callback.answer("Подключитесь к игре, чтобы увидеть таблицу лидеров", show_alert=True)
        return
    
    try:
        leaderboard = await api_client.get_session_leaderboard(session_id)
        
        if not leaderboard:
            await callback.answer("Таблица лидеров пока пуста", show_alert=True)
            return
        
        await callback.message.edit_text(
            "🏆 Таблица лидеров",
            reply_markup=GamePlayKeyboard.get_leaderboard(leaderboard, user_id)
        )
        
    except APIClientError as e:
        logger.error(f"Error getting leaderboard: {e}")
        await callback.answer("❌ Ошибка получения таблицы лидеров", show_alert=True)
    
    await callback.answer()


@router.callback_query(F.data.startswith("reconnect:"))
async def reconnect_handler(callback: CallbackQuery, state: FSMContext, api_client: APIClient):
    """Переподключение к игре"""
    session_code = callback.data.split(":", 1)[1]
    user_id = callback.from_user.id
    
    try:
        # Проверяем статус сессии
        session_info = await api_client.get_session_info(session_code)
        
        if not session_info:
            await callback.answer("❌ Игра не найдена", show_alert=True)
            return
        
        # Проверяем, участвует ли игрок в сессии
        current_session = await api_client.get_player_session(user_id)
        
        if current_session and current_session.get('session_code') == session_code:
            await state.set_state(GamePlayStates.IN_GAME)
            await state.update_data(
                session_id=current_session['id'],
                session_code=session_code
            )
            
            await callback.message.edit_text(
                "🔄 <b>Переподключение успешно!</b>\n\n"
                "Вы снова в игре.",
                parse_mode="HTML",
                reply_markup=GamePlayKeyboard.get_game_status()
            )
        else:
            await callback.answer("❌ Вы не участвуете в этой игре", show_alert=True)
        
    except APIClientError as e:
        logger.error(f"Error reconnecting: {e}")
        await callback.answer("❌ Ошибка переподключения", show_alert=True)
    
    await callback.answer()