"""
Session Management Handlers for Admin Bot
Обработчики для управления игровыми сессиями
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext
import structlog
import io

from ..states import SessionManagementStates, GameControlStates, AdminStates
from ..keyboards import MainMenuKeyboard, SessionControlKeyboard, GameManagementKeyboard
from ..services.api_client import APIClient, APIClientError
from ..services.qr_generator import QRGenerator

logger = structlog.get_logger()
router = Router()


@router.callback_query(F.data == "start_session")
async def start_session_menu_handler(callback: CallbackQuery, api_client: APIClient):
    """Меню запуска сессии"""
    user_id = callback.from_user.id
    
    try:
        games = await api_client.get_user_games(user_id)
        
        if not games:
            await callback.message.edit_text(
                "🚀 <b>Запуск игровой сессии</b>\n\n"
                "У вас нет созданных игр.\n"
                "Сначала создайте игру!",
                parse_mode="HTML",
                reply_markup=MainMenuKeyboard.get_back_button("create_game")
            )
        else:
            await callback.message.edit_text(
                f"🚀 <b>Запуск игровой сессии</b>\n\n"
                f"Выберите игру для запуска ({len(games)} доступно):",
                parse_mode="HTML",
                reply_markup=GameManagementKeyboard.get_games_list(games)
            )
        
    except APIClientError as e:
        logger.error(f"Error getting games for session: {e}")
        await callback.answer("❌ Ошибка получения списка игр", show_alert=True)
    
    await callback.answer()


@router.callback_query(F.data.startswith("start_session:"))
async def create_session_handler(callback: CallbackQuery, state: FSMContext, api_client: APIClient):
    """Создание новой игровой сессии"""
    game_id = callback.data.split(":", 1)[1]
    user_id = callback.from_user.id
    
    try:
        # Получаем информацию об игре
        game = await api_client.get_game_details(game_id)
        if not game:
            await callback.answer("❌ Игра не найдена", show_alert=True)
            return
        
        # Создаем сессию
        session = await api_client.create_session(game_id, user_id)
        
        await state.set_state(SessionManagementStates.WAITING_PLAYERS)
        await state.update_data(
            session_id=session['id'],
            game_id=game_id,
            session_code=session['session_code']
        )
        
        # Генерируем QR-код
        qr_generator = QRGenerator()
        qr_data = qr_generator.generate_qr_with_text(
            session['session_code'], 
            game['title']
        )
        
        session_text = (
            f"🎉 <b>Сессия создана!</b>\n\n"
            f"<b>Игра:</b> {game['title']}\n"
            f"<b>Код сессии:</b> <code>{session['session_code']}</code>\n"
            f"<b>Игроков:</b> 0\n\n"
            "Игроки могут подключиться:\n"
            f"• По коду: <code>{session['session_code']}</code>\n"
            "• Отсканировав QR-код ниже\n\n"
            "Ожидание игроков..."
        )
        
        # Отправляем QR-код
        qr_file = BufferedInputFile(qr_data, filename=f"qr_{session['session_code']}.png")
        await callback.message.answer_photo(
            photo=qr_file,
            caption=session_text,
            parse_mode="HTML",
            reply_markup=SessionControlKeyboard.get_session_control(
                session['id'], 
                "waiting", 
                0
            )
        )
        
        # Удаляем предыдущее сообщение
        await callback.message.delete()
        
        logger.info(f"Session created: {session['id']} by user {user_id}")
        
    except APIClientError as e:
        logger.error(f"Error creating session: {e}")
        await callback.answer("❌ Ошибка создания сессии", show_alert=True)
    
    await callback.answer()


@router.callback_query(F.data == "active_sessions")
async def active_sessions_handler(callback: CallbackQuery, api_client: APIClient):
    """Список активных сессий"""
    user_id = callback.from_user.id
    
    try:
        sessions = await api_client.get_user_sessions(user_id)
        active_sessions = [s for s in sessions if s.get('status') in ['waiting', 'in_progress', 'paused']]
        
        if not active_sessions:
            await callback.message.edit_text(
                "⚡ <b>Активные сессии</b>\n\n"
                "У вас нет активных сессий.\n"
                "Создайте новую сессию!",
                parse_mode="HTML",
                reply_markup=SessionControlKeyboard.get_active_sessions([])
            )
        else:
            await callback.message.edit_text(
                f"⚡ <b>Активные сессии ({len(active_sessions)})</b>\n\n"
                "Выберите сессию для управления:",
                parse_mode="HTML",
                reply_markup=SessionControlKeyboard.get_active_sessions(active_sessions)
            )
        
    except APIClientError as e:
        logger.error(f"Error getting active sessions: {e}")
        await callback.answer("❌ Ошибка получения сессий", show_alert=True)
    
    await callback.answer()


@router.callback_query(F.data.startswith("manage_session:"))
async def manage_session_handler(callback: CallbackQuery, state: FSMContext, api_client: APIClient):
    """Управление конкретной сессией"""
    session_id = callback.data.split(":", 1)[1]
    
    try:
        session = await api_client.get_session_details(session_id)
        if not session:
            await callback.answer("❌ Сессия не найдена", show_alert=True)
            return
        
        players = await api_client.get_session_players(session_id)
        
        await state.update_data(
            session_id=session_id,
            session_code=session.get('session_code')
        )
        
        status_text = {
            'waiting': 'Ожидание игроков',
            'in_progress': 'Игра идет',
            'paused': 'Пауза',
            'finished': 'Завершена'
        }.get(session.get('status'), 'Неизвестно')
        
        session_text = (
            f"⚡ <b>Управление сессией</b>\n\n"
            f"<b>Игра:</b> {session.get('game_title', 'Неизвестная')}\n"
            f"<b>Код:</b> <code>{session.get('session_code', 'N/A')}</code>\n"
            f"<b>Статус:</b> {status_text}\n"
            f"<b>Игроков:</b> {len(players)}\n"
        )
        
        if session.get('current_question'):
            session_text += f"<b>Текущий вопрос:</b> {session['current_question']}\n"
        
        await callback.message.edit_text(
            session_text,
            parse_mode="HTML",
            reply_markup=SessionControlKeyboard.get_session_control(
                session_id,
                session.get('status', 'unknown'),
                len(players)
            )
        )
        
    except APIClientError as e:
        logger.error(f"Error getting session details: {e}")
        await callback.answer("❌ Ошибка получения данных сессии", show_alert=True)
    
    await callback.answer()


@router.callback_query(F.data.startswith("start_game:"))
async def start_game_handler(callback: CallbackQuery, state: FSMContext, api_client: APIClient):
    """Запуск игры"""
    session_id = callback.data.split(":", 1)[1]
    
    try:
        # Проверяем количество игроков
        players = await api_client.get_session_players(session_id)
        
        if len(players) == 0:
            await callback.answer(
                "❌ Нельзя начать игру без игроков!\n"
                "Дождитесь подключения хотя бы одного игрока.",
                show_alert=True
            )
            return
        
        # Запускаем игру
        result = await api_client.start_game(session_id)
        
        await state.set_state(GameControlStates.SHOWING_QUESTION)
        
        await callback.message.edit_text(
            f"🎮 <b>Игра началась!</b>\n\n"
            f"Участников: {len(players)}\n"
            f"Первый вопрос отправлен игрокам.\n\n"
            "Управляйте ходом игры с помощью кнопок ниже:",
            parse_mode="HTML",
            reply_markup=SessionControlKeyboard.get_question_control(
                session_id, 1, result.get('total_questions', 0)
            )
        )
        
        logger.info(f"Game started for session {session_id}")
        
    except APIClientError as e:
        logger.error(f"Error starting game: {e}")
        await callback.answer("❌ Ошибка запуска игры", show_alert=True)
    
    await callback.answer()


@router.callback_query(F.data.startswith("next_question:"))
async def next_question_handler(callback: CallbackQuery, api_client: APIClient):
    """Переход к следующему вопросу"""
    session_id = callback.data.split(":", 1)[1]
    
    try:
        result = await api_client.next_question(session_id)
        
        if result.get('game_finished'):
            # Игра завершена
            await callback.message.edit_text(
                "🏁 <b>Игра завершена!</b>\n\n"
                "Все вопросы пройдены.\n"
                "Подсчитываем результаты...",
                parse_mode="HTML",
                reply_markup=SessionControlKeyboard.get_game_results(session_id)
            )
        else:
            # Следующий вопрос
            question_num = result.get('current_question', 0)
            total_questions = result.get('total_questions', 0)
            
            await callback.message.edit_text(
                f"➡️ <b>Вопрос {question_num}</b>\n\n"
                f"Вопрос отправлен игрокам.\n"
                f"Прогресс: {question_num}/{total_questions}\n\n"
                "Ожидание ответов игроков...",
                parse_mode="HTML",
                reply_markup=SessionControlKeyboard.get_question_control(
                    session_id, question_num, total_questions
                )
            )
        
        logger.info(f"Next question for session {session_id}")
        
    except APIClientError as e:
        logger.error(f"Error getting next question: {e}")
        await callback.answer("❌ Ошибка перехода к следующему вопросу", show_alert=True)
    
    await callback.answer()


@router.callback_query(F.data.startswith("show_players:"))
async def show_players_handler(callback: CallbackQuery, api_client: APIClient):
    """Показать список игроков"""
    session_id = callback.data.split(":", 1)[1]
    
    try:
        players = await api_client.get_session_players(session_id)
        
        if not players:
            await callback.message.edit_text(
                "👥 <b>Игроки сессии</b>\n\n"
                "Пока никто не подключился.\n"
                "Поделитесь кодом сессии с игроками!",
                parse_mode="HTML",
                reply_markup=SessionControlKeyboard.get_players_list(session_id, [])
            )
        else:
            players_text = f"👥 <b>Игроки сессии ({len(players)})</b>\n\n"
            
            for i, player in enumerate(players, 1):
                score = player.get('score', 0)
                status_emoji = "🟢" if player.get('is_online') else "🔴"
                players_text += f"{i}. {status_emoji} {player['name']} - {score} очков\n"
            
            await callback.message.edit_text(
                players_text,
                parse_mode="HTML",
                reply_markup=SessionControlKeyboard.get_players_list(session_id, players)
            )
        
    except APIClientError as e:
        logger.error(f"Error getting players: {e}")
        await callback.answer("❌ Ошибка получения списка игроков", show_alert=True)
    
    await callback.answer()


@router.callback_query(F.data.startswith("pause_game:"))
async def pause_game_handler(callback: CallbackQuery, api_client: APIClient):
    """Пауза игры"""
    session_id = callback.data.split(":", 1)[1]
    
    try:
        success = await api_client.pause_game(session_id)
        
        if success:
            await callback.message.edit_text(
                "⏸️ <b>Игра поставлена на паузу</b>\n\n"
                "Игроки получили уведомление о паузе.\n"
                "Вы можете продолжить игру в любой момент.",
                parse_mode="HTML",
                reply_markup=SessionControlKeyboard.get_session_control(
                    session_id, "paused", 0
                )
            )
            logger.info(f"Game paused for session {session_id}")
        else:
            await callback.answer("❌ Ошибка постановки на паузу", show_alert=True)
        
    except APIClientError as e:
        logger.error(f"Error pausing game: {e}")
        await callback.answer("❌ Ошибка постановки на паузу", show_alert=True)
    
    await callback.answer()


@router.callback_query(F.data.startswith("resume_game:"))
async def resume_game_handler(callback: CallbackQuery, api_client: APIClient):
    """Возобновление игры"""
    session_id = callback.data.split(":", 1)[1]
    
    try:
        success = await api_client.resume_game(session_id)
        
        if success:
            await callback.message.edit_text(
                "▶️ <b>Игра возобновлена</b>\n\n"
                "Игроки получили уведомление о продолжении игры.",
                parse_mode="HTML",
                reply_markup=SessionControlKeyboard.get_session_control(
                    session_id, "in_progress", 0
                )
            )
            logger.info(f"Game resumed for session {session_id}")
        else:
            await callback.answer("❌ Ошибка возобновления игры", show_alert=True)
        
    except APIClientError as e:
        logger.error(f"Error resuming game: {e}")
        await callback.answer("❌ Ошибка возобновления игры", show_alert=True)
    
    await callback.answer()


@router.callback_query(F.data.startswith("end_game:"))
async def end_game_handler(callback: CallbackQuery, api_client: APIClient):
    """Завершение игры"""
    session_id = callback.data.split(":", 1)[1]
    
    try:
        result = await api_client.finish_game(session_id)
        
        await callback.message.edit_text(
            "🛑 <b>Игра завершена</b>\n\n"
            "Игра была принудительно завершена администратором.\n"
            "Результаты подсчитаны на основе текущих ответов.",
            parse_mode="HTML",
            reply_markup=SessionControlKeyboard.get_game_results(session_id)
        )
        
        logger.info(f"Game ended for session {session_id}")
        
    except APIClientError as e:
        logger.error(f"Error ending game: {e}")
        await callback.answer("❌ Ошибка завершения игры", show_alert=True)
    
    await callback.answer()


@router.callback_query(F.data.startswith("show_qr:"))
async def show_qr_handler(callback: CallbackQuery, state: FSMContext):
    """Показать QR-код для подключения"""
    session_id = callback.data.split(":", 1)[1]
    state_data = await state.get_data()
    session_code = state_data.get('session_code')
    
    if not session_code:
        await callback.answer("❌ Код сессии не найден", show_alert=True)
        return
    
    try:
        qr_generator = QRGenerator()
        
        # Создаем сообщение для шаринга
        share_message = qr_generator.create_shareable_message(session_code)
        
        await callback.message.answer(
            f"📋 <b>Информация для подключения</b>\n\n{share_message}",
            parse_mode="HTML"
        )
        
        await callback.answer("📱 Информация для подключения отправлена")
        
    except Exception as e:
        logger.error(f"Error showing QR: {e}")
        await callback.answer("❌ Ошибка генерации QR-кода", show_alert=True)


@router.callback_query(F.data.startswith("detailed_results:"))
async def detailed_results_handler(callback: CallbackQuery, api_client: APIClient):
    """Подробные результаты игры"""
    session_id = callback.data.split(":", 1)[1]
    
    try:
        results = await api_client.get_game_results(session_id)
        
        if not results.get('players'):
            await callback.answer("❌ Результаты не найдены", show_alert=True)
            return
        
        results_text = "📊 <b>Подробные результаты</b>\n\n"
        
        for i, player in enumerate(results['players'][:10], 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            results_text += (
                f"{medal} <b>{player['name']}</b>\n"
                f"   Очки: {player['score']}\n"
                f"   Правильных ответов: {player.get('correct_answers', 0)}\n"
                f"   Всего ответов: {player.get('total_answers', 0)}\n\n"
            )
        
        if len(results['players']) > 10:
            results_text += f"... и еще {len(results['players']) - 10} игроков"
        
        await callback.message.edit_text(
            results_text,
            parse_mode="HTML",
            reply_markup=SessionControlKeyboard.get_game_results(session_id, True)
        )
        
    except APIClientError as e:
        logger.error(f"Error getting detailed results: {e}")
        await callback.answer("❌ Ошибка получения результатов", show_alert=True)
    
    await callback.answer()