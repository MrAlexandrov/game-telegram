"""
Validation Keyboards for Admin Bot
"""

from typing import List, Dict, Any
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


class ValidationKeyboard:
    """Клавиатуры для валидации ответов игроков"""
    
    @staticmethod
    def get_answer_validation(answer_id: str, question_text: str = None) -> InlineKeyboardMarkup:
        """Валидация конкретного ответа"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(
                text="✅ Правильно",
                callback_data=f"validate:{answer_id}:correct"
            ),
            InlineKeyboardButton(
                text="❌ Неправильно",
                callback_data=f"validate:{answer_id}:incorrect"
            )
        )
        
        builder.row(
            InlineKeyboardButton(
                text="⚠️ Частично правильно",
                callback_data=f"validate:{answer_id}:partial"
            )
        )
        
        builder.row(
            InlineKeyboardButton(
                text="🔍 Показать вопрос",
                callback_data=f"show_question:{answer_id}"
            )
        )
        
        builder.row(
            InlineKeyboardButton(
                text="⏭️ Пропустить",
                callback_data=f"skip_validation:{answer_id}"
            )
        )
        
        return builder.as_markup()
    
    @staticmethod
    def get_pending_validations(answers: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
        """Список ответов, ожидающих валидации"""
        builder = InlineKeyboardBuilder()
        
        for answer in answers[:10]:  # Показываем только первые 10
            player_name = answer.get('player_name', 'Неизвестный')
            answer_text = answer.get('answer_text', '')[:30]  # Обрезаем длинные ответы
            
            builder.row(
                InlineKeyboardButton(
                    text=f"👤 {player_name}: {answer_text}...",
                    callback_data=f"validate_answer:{answer['id']}"
                )
            )
        
        if len(answers) > 10:
            builder.row(
                InlineKeyboardButton(
                    text=f"... и еще {len(answers) - 10} ответов",
                    callback_data="show_all_validations"
                )
            )
        
        builder.row(
            InlineKeyboardButton(
                text="✅ Принять все",
                callback_data="validate_all:correct"
            ),
            InlineKeyboardButton(
                text="❌ Отклонить все",
                callback_data="validate_all:incorrect"
            )
        )
        
        builder.row(
            InlineKeyboardButton(
                text="🔙 Назад",
                callback_data="back_to_session"
            )
        )
        
        return builder.as_markup()
    
    @staticmethod
    def get_partial_score_options(answer_id: str) -> InlineKeyboardMarkup:
        """Выбор частичных очков"""
        builder = InlineKeyboardBuilder()
        
        # Варианты частичных очков
        for percentage in [25, 50, 75]:
            builder.row(
                InlineKeyboardButton(
                    text=f"{percentage}% очков",
                    callback_data=f"partial_score:{answer_id}:{percentage}"
                )
            )
        
        builder.row(
            InlineKeyboardButton(
                text="✏️ Указать вручную",
                callback_data=f"custom_score:{answer_id}"
            )
        )
        
        builder.row(
            InlineKeyboardButton(
                text="🔙 Назад к валидации",
                callback_data=f"validate_answer:{answer_id}"
            )
        )
        
        return builder.as_markup()
    
    @staticmethod
    def get_validation_confirmation(answer_id: str, validation_type: str, score: int = None) -> InlineKeyboardMarkup:
        """Подтверждение валидации"""
        builder = InlineKeyboardBuilder()
        
        confirm_data = f"confirm_validation:{answer_id}:{validation_type}"
        if score is not None:
            confirm_data += f":{score}"
        
        builder.row(
            InlineKeyboardButton(
                text="✅ Подтвердить",
                callback_data=confirm_data
            ),
            InlineKeyboardButton(
                text="❌ Отмена",
                callback_data=f"validate_answer:{answer_id}"
            )
        )
        
        return builder.as_markup()
    
    @staticmethod
    def get_batch_validation_options(session_id: str) -> InlineKeyboardMarkup:
        """Опции массовой валидации"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(
                text="✅ Принять все текстовые ответы",
                callback_data=f"batch_validate:{session_id}:accept_all"
            )
        )
        
        builder.row(
            InlineKeyboardButton(
                text="❌ Отклонить все текстовые ответы",
                callback_data=f"batch_validate:{session_id}:reject_all"
            )
        )
        
        builder.row(
            InlineKeyboardButton(
                text="🎯 Автоматическая проверка",
                callback_data=f"batch_validate:{session_id}:auto_check"
            )
        )
        
        builder.row(
            InlineKeyboardButton(
                text="🔙 К списку ответов",
                callback_data=f"pending_validations:{session_id}"
            )
        )
        
        return builder.as_markup()
    
    @staticmethod
    def get_question_context(question_id: str, answer_id: str) -> InlineKeyboardMarkup:
        """Контекст вопроса для валидации"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(
                text="✅ Правильно",
                callback_data=f"validate:{answer_id}:correct"
            ),
            InlineKeyboardButton(
                text="❌ Неправильно",
                callback_data=f"validate:{answer_id}:incorrect"
            )
        )
        
        builder.row(
            InlineKeyboardButton(
                text="📝 Показать правильные ответы",
                callback_data=f"show_correct_answers:{question_id}"
            )
        )
        
        builder.row(
            InlineKeyboardButton(
                text="🔙 К валидации",
                callback_data=f"validate_answer:{answer_id}"
            )
        )
        
        return builder.as_markup()