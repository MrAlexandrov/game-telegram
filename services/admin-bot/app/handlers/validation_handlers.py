"""
Validation Handlers for Admin Bot
Обработчики для валидации ответов игроков
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
import structlog

from ..states import ValidationStates
from ..keyboards import ValidationKeyboard, SessionControlKeyboard
from ..services.api_client import APIClient, APIClientError

logger = structlog.get_logger()
router = Router()


@router.callback_query(F.data.startswith("show_answers:"))
async def show_answers_handler(callback: CallbackQuery, api_client: APIClient):
    """Показать ответы игроков на текущий вопрос"""
    session_id = callback.data.split(":", 1)[1]
    
    try:
        pending_answers = await api_client.get_pending_answers(session_id)
        
        if not pending_answers:
            await callback.message.edit_text(
                "📊 <b>Ответы игроков</b>\n\n"
                "Пока нет ответов, требующих валидации.\n"
                "Все ответы обработаны автоматически.",
                parse_mode="HTML",
                reply_markup=SessionControlKeyboard.get_question_control(session_id, 1, 10)
            )
        else:
            answers_text = f"📊 <b>Ответы для валидации ({len(pending_answers)})</b>\n\n"
            
            for i, answer in enumerate(pending_answers[:5], 1):
                player_name = answer.get('player_name', 'Неизвестный')
                answer_text = answer.get('answer_text', '')[:50]
                answers_text += f"{i}. <b>{player_name}</b>: {answer_text}...\n"
            
            if len(pending_answers) > 5:
                answers_text += f"\n... и еще {len(pending_answers) - 5} ответов"
            
            await callback.message.edit_text(
                answers_text,
                parse_mode="HTML",
                reply_markup=ValidationKeyboard.get_pending_validations(pending_answers)
            )
        
    except APIClientError as e:
        logger.error(f"Error getting pending answers: {e}")
        await callback.answer("❌ Ошибка получения ответов", show_alert=True)
    
    await callback.answer()


@router.callback_query(F.data.startswith("validate_answer:"))
async def validate_answer_handler(callback: CallbackQuery, state: FSMContext, api_client: APIClient):
    """Валидация конкретного ответа"""
    answer_id = callback.data.split(":", 1)[1]
    
    try:
        # Получаем детали ответа (это нужно будет реализовать в API)
        # Пока используем заглушку
        answer_details = {
            'id': answer_id,
            'player_name': 'Игрок',
            'question_text': 'Вопрос',
            'answer_text': 'Ответ игрока'
        }
        
        await state.set_state(ValidationStates.REVIEWING_ANSWER)
        await state.update_data(answer_id=answer_id)
        
        validation_text = (
            f"🔍 <b>Валидация ответа</b>\n\n"
            f"<b>Игрок:</b> {answer_details['player_name']}\n"
            f"<b>Вопрос:</b> {answer_details['question_text']}\n"
            f"<b>Ответ:</b> {answer_details['answer_text']}\n\n"
            "Оцените правильность ответа:"
        )
        
        await callback.message.edit_text(
            validation_text,
            parse_mode="HTML",
            reply_markup=ValidationKeyboard.get_answer_validation(answer_id)
        )
        
    except Exception as e:
        logger.error(f"Error preparing answer validation: {e}")
        await callback.answer("❌ Ошибка подготовки валидации", show_alert=True)
    
    await callback.answer()


@router.callback_query(F.data.startswith("validate:"))
async def process_validation_handler(callback: CallbackQuery, state: FSMContext, api_client: APIClient):
    """Обработка валидации ответа"""
    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer("❌ Неверный формат данных", show_alert=True)
        return
    
    _, answer_id, validation_type = parts
    
    try:
        if validation_type == "correct":
            success = await api_client.validate_answer(answer_id, True)
            result_text = "✅ Ответ отмечен как правильный"
        elif validation_type == "incorrect":
            success = await api_client.validate_answer(answer_id, False)
            result_text = "❌ Ответ отмечен как неправильный"
        elif validation_type == "partial":
            # Переходим к выбору частичных очков
            await callback.message.edit_text(
                "⚠️ <b>Частично правильный ответ</b>\n\n"
                "Выберите количество очков для этого ответа:",
                parse_mode="HTML",
                reply_markup=ValidationKeyboard.get_partial_score_options(answer_id)
            )
            await callback.answer()
            return
        else:
            await callback.answer("❌ Неизвестный тип валидации", show_alert=True)
            return
        
        if success:
            await callback.message.edit_text(
                f"{result_text}\n\n"
                "Игрок получил уведомление о результате.",
                parse_mode="HTML",
                reply_markup=ValidationKeyboard.get_pending_validations([])
            )
            
            await state.clear()
            logger.info(f"Answer {answer_id} validated as {validation_type}")
        else:
            await callback.answer("❌ Ошибка валидации", show_alert=True)
        
    except APIClientError as e:
        logger.error(f"Error validating answer: {e}")
        await callback.answer("❌ Ошибка валидации ответа", show_alert=True)
    
    await callback.answer()


@router.callback_query(F.data.startswith("partial_score:"))
async def partial_score_handler(callback: CallbackQuery, state: FSMContext, api_client: APIClient):
    """Обработка частичных очков"""
    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer("❌ Неверный формат данных", show_alert=True)
        return
    
    _, answer_id, percentage = parts
    
    try:
        # Вычисляем очки (предполагаем, что базовые очки = 10)
        base_points = 10
        partial_points = int(base_points * int(percentage) / 100)
        
        success = await api_client.validate_answer(answer_id, True, partial_points)
        
        if success:
            await callback.message.edit_text(
                f"⚠️ <b>Ответ оценен частично</b>\n\n"
                f"Начислено очков: {partial_points} ({percentage}%)\n"
                "Игрок получил уведомление о результате.",
                parse_mode="HTML",
                reply_markup=ValidationKeyboard.get_pending_validations([])
            )
            
            await state.clear()
            logger.info(f"Answer {answer_id} validated with partial score: {partial_points}")
        else:
            await callback.answer("❌ Ошибка валидации", show_alert=True)
        
    except APIClientError as e:
        logger.error(f"Error setting partial score: {e}")
        await callback.answer("❌ Ошибка установки очков", show_alert=True)
    except ValueError:
        await callback.answer("❌ Неверное значение процентов", show_alert=True)
    
    await callback.answer()


@router.callback_query(F.data.startswith("skip_validation:"))
async def skip_validation_handler(callback: CallbackQuery, state: FSMContext):
    """Пропуск валидации ответа"""
    answer_id = callback.data.split(":", 1)[1]
    
    await callback.message.edit_text(
        "⏭️ <b>Валидация пропущена</b>\n\n"
        "Ответ оставлен без оценки.\n"
        "Вы можете вернуться к нему позже.",
        parse_mode="HTML",
        reply_markup=ValidationKeyboard.get_pending_validations([])
    )
    
    await state.clear()
    await callback.answer("Валидация пропущена")


@router.callback_query(F.data.startswith("validate_all:"))
async def validate_all_handler(callback: CallbackQuery, api_client: APIClient):
    """Массовая валидация всех ответов"""
    validation_type = callback.data.split(":", 1)[1]
    
    # Получаем session_id из состояния или контекста
    # Это упрощенная реализация
    session_id = "current_session"  # Нужно получить из состояния
    
    try:
        pending_answers = await api_client.get_pending_answers(session_id)
        
        if not pending_answers:
            await callback.answer("Нет ответов для валидации", show_alert=True)
            return
        
        success_count = 0
        is_correct = validation_type == "accept_all"
        
        for answer in pending_answers:
            try:
                success = await api_client.validate_answer(answer['id'], is_correct)
                if success:
                    success_count += 1
            except APIClientError:
                continue
        
        result_text = (
            f"✅ <b>Массовая валидация завершена</b>\n\n"
            f"Обработано ответов: {success_count}/{len(pending_answers)}\n"
            f"Результат: {'Все правильные' if is_correct else 'Все неправильные'}"
        )
        
        await callback.message.edit_text(
            result_text,
            parse_mode="HTML",
            reply_markup=ValidationKeyboard.get_pending_validations([])
        )
        
        logger.info(f"Batch validation completed: {success_count}/{len(pending_answers)}")
        
    except APIClientError as e:
        logger.error(f"Error in batch validation: {e}")
        await callback.answer("❌ Ошибка массовой валидации", show_alert=True)
    
    await callback.answer()


@router.callback_query(F.data.startswith("show_question:"))
async def show_question_context_handler(callback: CallbackQuery, api_client: APIClient):
    """Показать контекст вопроса для валидации"""
    answer_id = callback.data.split(":", 1)[1]
    
    try:
        # Получаем информацию о вопросе
        # Это нужно будет реализовать в API
        question_info = {
            'text': 'Текст вопроса',
            'correct_answers': ['Правильный ответ 1', 'Правильный ответ 2'],
            'explanation': 'Объяснение правильного ответа'
        }
        
        context_text = (
            f"❓ <b>Контекст вопроса</b>\n\n"
            f"<b>Вопрос:</b> {question_info['text']}\n\n"
            f"<b>Правильные ответы:</b>\n"
        )
        
        for answer in question_info['correct_answers']:
            context_text += f"• {answer}\n"
        
        if question_info.get('explanation'):
            context_text += f"\n<b>Объяснение:</b> {question_info['explanation']}"
        
        await callback.message.edit_text(
            context_text,
            parse_mode="HTML",
            reply_markup=ValidationKeyboard.get_question_context("question_id", answer_id)
        )
        
    except Exception as e:
        logger.error(f"Error showing question context: {e}")
        await callback.answer("❌ Ошибка получения контекста", show_alert=True)
    
    await callback.answer()


@router.callback_query(F.data.startswith("show_correct_answers:"))
async def show_correct_answers_handler(callback: CallbackQuery):
    """Показать правильные ответы на вопрос"""
    question_id = callback.data.split(":", 1)[1]
    
    # Заглушка для демонстрации
    correct_answers = [
        "Правильный ответ 1",
        "Правильный ответ 2", 
        "Альтернативный вариант"
    ]
    
    answers_text = (
        "✅ <b>Правильные ответы:</b>\n\n"
    )
    
    for i, answer in enumerate(correct_answers, 1):
        answers_text += f"{i}. {answer}\n"
    
    await callback.answer(answers_text, show_alert=True)


@router.callback_query(F.data == "back_to_session")
async def back_to_session_handler(callback: CallbackQuery, state: FSMContext):
    """Возврат к управлению сессией"""
    state_data = await state.get_data()
    session_id = state_data.get('session_id')
    
    if session_id:
        await callback.message.edit_text(
            "🔙 Возвращаемся к управлению сессией...",
            reply_markup=SessionControlKeyboard.get_session_control(session_id, "in_progress", 0)
        )
    else:
        await callback.message.edit_text(
            "🔙 Возвращаемся в главное меню...",
            reply_markup=None
        )
    
    await state.clear()
    await callback.answer()


@router.message(F.text, ValidationStates.REVIEWING_ANSWER)
async def custom_score_input_handler(message: Message, state: FSMContext, api_client: APIClient):
    """Обработка ввода пользовательских очков"""
    try:
        points = int(message.text)
        
        if points < 0 or points > 100:
            await message.answer("❌ Очки должны быть от 0 до 100")
            return
        
        state_data = await state.get_data()
        answer_id = state_data.get('answer_id')
        
        if not answer_id:
            await message.answer("❌ Ошибка: ID ответа не найден")
            return
        
        success = await api_client.validate_answer(answer_id, True, points)
        
        if success:
            await message.answer(
                f"✅ <b>Ответ оценен</b>\n\n"
                f"Начислено очков: {points}\n"
                "Игрок получил уведомление о результате.",
                parse_mode="HTML"
            )
            
            await state.clear()
            logger.info(f"Answer {answer_id} validated with custom score: {points}")
        else:
            await message.answer("❌ Ошибка валидации ответа")
        
    except ValueError:
        await message.answer("❌ Введите корректное число очков (0-100)")
    except APIClientError as e:
        logger.error(f"Error setting custom score: {e}")
        await message.answer("❌ Ошибка валидации ответа")