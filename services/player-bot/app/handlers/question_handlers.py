"""
Question Handlers for Player Bot
Обработчики для ответов на вопросы
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
import structlog
import asyncio

from ..states import QuestionStates, GamePlayStates
from ..keyboards import QuestionKeyboard, GamePlayKeyboard, MainMenuKeyboard
from ..services.api_client import APIClient, APIClientError
from ..config import settings

logger = structlog.get_logger()
router = Router()


@router.callback_query(F.data.startswith("answer:"))
async def answer_callback_handler(callback: CallbackQuery, state: FSMContext, api_client: APIClient):
    """Обработчик ответов через кнопки"""
    parts = callback.data.split(":", 3)
    if len(parts) != 4:
        await callback.answer("❌ Неверный формат ответа", show_alert=True)
        return
    
    _, question_id, option_index, answer_text = parts
    user_id = callback.from_user.id
    
    state_data = await state.get_data()
    session_id = state_data.get('session_id')
    
    if not session_id:
        await callback.answer("❌ Сессия не найдена", show_alert=True)
        return
    
    try:
        # Отправляем ответ
        result = await api_client.submit_answer(
            session_id=session_id,
            question_id=question_id,
            telegram_id=user_id,
            answer=answer_text
        )
        
        # Обновляем сообщение с результатом
        if result.get('requires_validation'):
            result_text = (
                f"📝 <b>Ответ отправлен!</b>\n\n"
                f"Ваш ответ: <b>{answer_text}</b>\n\n"
                "⏳ Ожидание проверки администратором..."
            )
            keyboard = QuestionKeyboard.get_waiting_validation()
        else:
            is_correct = result.get('is_correct', False)
            points = result.get('points_earned', 0)
            
            if is_correct:
                result_text = (
                    f"✅ <b>Правильно!</b>\n\n"
                    f"Ваш ответ: <b>{answer_text}</b>\n"
                    f"Получено очков: <b>+{points}</b>\n\n"
                    "🎉 Отличная работа!"
                )
            else:
                correct_answer = result.get('correct_answer', 'Неизвестно')
                result_text = (
                    f"❌ <b>Неправильно</b>\n\n"
                    f"Ваш ответ: <b>{answer_text}</b>\n"
                    f"Правильный ответ: <b>{correct_answer}</b>\n"
                    f"Получено очков: <b>{points}</b>\n\n"
                    "Не расстраивайтесь, следующий вопрос будет лучше!"
                )
            
            keyboard = QuestionKeyboard.get_answer_result(is_correct, points)
        
        await callback.message.edit_text(
            result_text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        
        # Обновляем состояние
        await state.set_state(GamePlayStates.WAITING_NEXT_QUESTION)
        
        logger.info(f"Player {user_id} answered question {question_id}: {answer_text}")
        
    except APIClientError as e:
        logger.error(f"Error submitting answer: {e}")
        await callback.answer("❌ Ошибка отправки ответа", show_alert=True)
    
    await callback.answer()


@router.message(F.text, QuestionStates.TEXT_INPUT)
async def text_answer_handler(message: Message, state: FSMContext, api_client: APIClient):
    """Обработчик текстовых ответов"""
    answer_text = message.text.strip()
    user_id = message.from_user.id
    
    # Проверяем длину ответа
    if len(answer_text) > settings.MAX_ANSWER_LENGTH:
        await message.answer(
            f"❌ Ответ слишком длинный!\n"
            f"Максимум {settings.MAX_ANSWER_LENGTH} символов."
        )
        return
    
    if len(answer_text) < 1:
        await message.answer("❌ Ответ не может быть пустым!")
        return
    
    state_data = await state.get_data()
    session_id = state_data.get('session_id')
    question_id = state_data.get('current_question_id')
    
    if not session_id or not question_id:
        await message.answer("❌ Ошибка: данные сессии не найдены")
        return
    
    try:
        # Отправляем ответ
        result = await api_client.submit_answer(
            session_id=session_id,
            question_id=question_id,
            telegram_id=user_id,
            answer=answer_text
        )
        
        # Показываем результат
        if result.get('requires_validation'):
            result_text = (
                f"📝 <b>Ответ отправлен!</b>\n\n"
                f"Ваш ответ: <i>{answer_text}</i>\n\n"
                "⏳ Администратор проверит ваш ответ.\n"
                "Результат будет объявлен позже."
            )
            keyboard = QuestionKeyboard.get_waiting_validation()
        else:
            is_correct = result.get('is_correct', False)
            points = result.get('points_earned', 0)
            
            if is_correct:
                result_text = (
                    f"✅ <b>Правильно!</b>\n\n"
                    f"Ваш ответ: <i>{answer_text}</i>\n"
                    f"Получено очков: <b>+{points}</b>\n\n"
                    "🎉 Отлично!"
                )
            else:
                correct_answers = result.get('correct_answers', [])
                correct_text = ", ".join(correct_answers) if correct_answers else "Неизвестно"
                
                result_text = (
                    f"❌ <b>Неправильно</b>\n\n"
                    f"Ваш ответ: <i>{answer_text}</i>\n"
                    f"Правильные ответы: <i>{correct_text}</i>\n"
                    f"Получено очков: <b>{points}</b>\n\n"
                    "Попробуйте лучше в следующий раз!"
                )
            
            keyboard = QuestionKeyboard.get_answer_result(is_correct, points)
        
        await message.answer(
            result_text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        
        # Обновляем состояние
        await state.set_state(GamePlayStates.WAITING_NEXT_QUESTION)
        
        logger.info(f"Player {user_id} answered text question {question_id}: {answer_text}")
        
    except APIClientError as e:
        logger.error(f"Error submitting text answer: {e}")
        await message.answer("❌ Ошибка отправки ответа. Попробуйте еще раз.")


@router.callback_query(F.data == "skip_question")
async def skip_question_handler(callback: CallbackQuery, state: FSMContext, api_client: APIClient):
    """Пропуск вопроса"""
    user_id = callback.from_user.id
    state_data = await state.get_data()
    session_id = state_data.get('session_id')
    question_id = state_data.get('current_question_id')
    
    if not session_id or not question_id:
        await callback.answer("❌ Ошибка: данные не найдены", show_alert=True)
        return
    
    try:
        success = await api_client.skip_question(session_id, question_id, user_id)
        
        if success:
            await callback.message.edit_text(
                "⏭️ <b>Вопрос пропущен</b>\n\n"
                "Вы не получили очков за этот вопрос.\n"
                "Ожидание следующего вопроса...",
                parse_mode="HTML",
                reply_markup=GamePlayKeyboard.get_waiting_next_question()
            )
            
            await state.set_state(GamePlayStates.WAITING_NEXT_QUESTION)
            logger.info(f"Player {user_id} skipped question {question_id}")
        else:
            await callback.answer("❌ Ошибка пропуска вопроса", show_alert=True)
        
    except APIClientError as e:
        logger.error(f"Error skipping question: {e}")
        await callback.answer("❌ Ошибка пропуска вопроса", show_alert=True)
    
    await callback.answer()


@router.callback_query(F.data == "show_hint")
async def show_hint_handler(callback: CallbackQuery, state: FSMContext, api_client: APIClient):
    """Показать подсказку к вопросу"""
    state_data = await state.get_data()
    question_id = state_data.get('current_question_id')
    
    if not question_id:
        await callback.answer("❌ Вопрос не найден", show_alert=True)
        return
    
    try:
        hint = await api_client.get_question_hint(question_id)
        
        if hint:
            await callback.answer(f"💡 Подсказка: {hint}", show_alert=True)
        else:
            await callback.answer("💡 Подсказка недоступна для этого вопроса", show_alert=True)
        
    except APIClientError as e:
        logger.error(f"Error getting hint: {e}")
        await callback.answer("❌ Ошибка получения подсказки", show_alert=True)


@router.callback_query(F.data == "current_score")
async def current_score_handler(callback: CallbackQuery, state: FSMContext, api_client: APIClient):
    """Показать текущий счет"""
    user_id = callback.from_user.id
    state_data = await state.get_data()
    session_id = state_data.get('session_id')
    
    if not session_id:
        await callback.answer("❌ Сессия не найдена", show_alert=True)
        return
    
    try:
        score_data = await api_client.get_player_score(session_id, user_id)
        leaderboard = await api_client.get_session_leaderboard(session_id)
        
        # Находим позицию игрока
        position = next(
            (i + 1 for i, p in enumerate(leaderboard) if p.get('telegram_id') == user_id), 
            None
        )
        
        score_text = (
            f"📊 <b>Ваш текущий счет</b>\n\n"
            f"<b>Очки:</b> {score_data.get('score', 0)}\n"
            f"<b>Правильных ответов:</b> {score_data.get('correct_answers', 0)}\n"
            f"<b>Всего ответов:</b> {score_data.get('total_answers', 0)}\n"
        )
        
        if score_data.get('total_answers', 0) > 0:
            accuracy = round((score_data.get('correct_answers', 0) / score_data['total_answers']) * 100, 1)
            score_text += f"<b>Точность:</b> {accuracy}%\n"
        
        if position:
            score_text += f"<b>Позиция:</b> {position} из {len(leaderboard)}"
        
        await callback.answer(score_text, show_alert=True)
        
    except APIClientError as e:
        logger.error(f"Error getting score: {e}")
        await callback.answer("❌ Ошибка получения счета", show_alert=True)


@router.callback_query(F.data == "ready_next")
async def ready_next_handler(callback: CallbackQuery, state: FSMContext):
    """Готовность к следующему вопросу"""
    await callback.message.edit_text(
        "✅ <b>Готов к следующему вопросу!</b>\n\n"
        "Ожидание других игроков и администратора...",
        parse_mode="HTML",
        reply_markup=GamePlayKeyboard.get_waiting_next_question()
    )
    
    await state.set_state(GamePlayStates.WAITING_NEXT_QUESTION)
    await callback.answer("Готов к следующему вопросу!")


@router.callback_query(F.data == "celebrate")
async def celebrate_handler(callback: CallbackQuery):
    """Празднование правильного ответа"""
    celebrations = [
        "🎉 Отлично!",
        "🌟 Великолепно!",
        "🔥 Потрясающе!",
        "⭐ Блестяще!",
        "🎯 В точку!",
        "💪 Сила!",
        "🚀 Космос!"
    ]
    
    import random
    celebration = random.choice(celebrations)
    
    await callback.answer(celebration, show_alert=False)


@router.callback_query(F.data == "other_players")
async def other_players_handler(callback: CallbackQuery, state: FSMContext, api_client: APIClient):
    """Показать других игроков"""
    user_id = callback.from_user.id
    state_data = await state.get_data()
    session_id = state_data.get('session_id')
    
    if not session_id:
        await callback.answer("❌ Сессия не найдена", show_alert=True)
        return
    
    try:
        players = await api_client.get_session_players(session_id)
        other_players = [p for p in players if p.get('telegram_id') != user_id]
        
        if not other_players:
            await callback.answer("👥 Вы единственный игрок в сессии", show_alert=True)
            return
        
        players_text = f"👥 Другие игроки ({len(other_players)}):\n\n"
        
        for i, player in enumerate(other_players[:10], 1):
            status_emoji = "🟢" if player.get('is_online', True) else "🔴"
            score = player.get('score', 0)
            players_text += f"{i}. {status_emoji} {player['name']} - {score} очков\n"
        
        if len(other_players) > 10:
            players_text += f"\n... и еще {len(other_players) - 10} игроков"
        
        await callback.answer(players_text, show_alert=True)
        
    except APIClientError as e:
        logger.error(f"Error getting other players: {e}")
        await callback.answer("❌ Ошибка получения списка игроков", show_alert=True)


@router.callback_query(F.data.startswith("confirm_answer:"))
async def confirm_answer_handler(callback: CallbackQuery, state: FSMContext):
    """Подтверждение отправки ответа"""
    question_id = callback.data.split(":", 1)[1]
    
    await callback.message.edit_text(
        "✅ <b>Ответ подтвержден!</b>\n\n"
        "Ваш ответ отправлен на проверку.",
        parse_mode="HTML",
        reply_markup=QuestionKeyboard.get_waiting_validation()
    )
    
    await state.set_state(GamePlayStates.WAITING_NEXT_QUESTION)
    await callback.answer("Ответ отправлен!")


@router.callback_query(F.data.startswith("edit_answer:"))
async def edit_answer_handler(callback: CallbackQuery, state: FSMContext):
    """Редактирование ответа"""
    await callback.message.edit_text(
        "✏️ <b>Редактирование ответа</b>\n\n"
        "Введите новый ответ:",
        parse_mode="HTML",
        reply_markup=QuestionKeyboard.get_text_input_prompt()
    )
    
    await state.set_state(QuestionStates.TEXT_INPUT)
    await callback.answer("Введите новый ответ")


# Обработчик для Family Feud (100 к одному)
@router.callback_query(F.data.startswith("ff_"))
async def family_feud_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчики для игры 100 к одному"""
    action = callback.data.split("_", 1)[1]
    
    if action == "hint":
        await callback.answer(
            "💡 Подумайте о самых популярных ответах на этот вопрос. "
            "Что бы ответило большинство людей?",
            show_alert=True
        )
    elif action == "text_input":
        await callback.message.edit_text(
            "📝 <b>Введите ваш ответ</b>\n\n"
            "Напишите то, что, по вашему мнению, "
            "ответило бы большинство людей:",
            parse_mode="HTML",
            reply_markup=QuestionKeyboard.get_text_input_prompt()
        )
        await state.set_state(QuestionStates.FAMILY_FEUD)
    elif action == "skip":
        await skip_question_handler(callback, state, callback.bot.get("api_client"))
    
    await callback.answer()


@router.message(F.text, QuestionStates.FAMILY_FEUD)
async def family_feud_answer_handler(message: Message, state: FSMContext, api_client: APIClient):
    """Обработчик ответов для Family Feud"""
    # Используем тот же обработчик, что и для обычных текстовых ответов
    await text_answer_handler(message, state, api_client)