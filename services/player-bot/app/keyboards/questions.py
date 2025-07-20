"""
Question Keyboards for Player Bot
"""

from typing import List, Dict, Any
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


class QuestionKeyboard:
    """Клавиатуры для ответов на вопросы"""
    
    @staticmethod
    def get_multiple_choice(options: List[str], question_id: str) -> InlineKeyboardMarkup:
        """Клавиатура для вопросов с вариантами ответов"""
        builder = InlineKeyboardBuilder()
        
        for i, option in enumerate(options):
            builder.row(
                InlineKeyboardButton(
                    text=f"{chr(65 + i)}. {option}",  # A, B, C, D...
                    callback_data=f"answer:{question_id}:{i}:{option[:50]}"
                )
            )
        
        return builder.as_markup()
    
    @staticmethod
    def get_true_false(question_id: str) -> InlineKeyboardMarkup:
        """Клавиатура для вопросов Правда/Ложь"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(
                text="✅ Правда",
                callback_data=f"answer:{question_id}:true:Правда"
            ),
            InlineKeyboardButton(
                text="❌ Ложь",
                callback_data=f"answer:{question_id}:false:Ложь"
            )
        )
        
        return builder.as_markup()
    
    @staticmethod
    def get_text_input_prompt() -> InlineKeyboardMarkup:
        """Подсказка для текстового ввода"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(
                text="💡 Подсказка",
                callback_data="show_hint"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="⏭️ Пропустить",
                callback_data="skip_question"
            )
        )
        
        return builder.as_markup()
    
    @staticmethod
    def get_answer_confirmation(answer_text: str, question_id: str) -> InlineKeyboardMarkup:
        """Подтверждение ответа"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(
                text="✅ Отправить ответ",
                callback_data=f"confirm_answer:{question_id}"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="✏️ Изменить ответ",
                callback_data=f"edit_answer:{question_id}"
            )
        )
        
        return builder.as_markup()
    
    @staticmethod
    def get_waiting_validation() -> InlineKeyboardMarkup:
        """Ожидание валидации ответа"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(
                text="📊 Мой счет",
                callback_data="current_score"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="👥 Другие игроки",
                callback_data="other_players"
            )
        )
        
        return builder.as_markup()
    
    @staticmethod
    def get_answer_result(is_correct: bool, points: int = 0) -> InlineKeyboardMarkup:
        """Результат ответа"""
        builder = InlineKeyboardBuilder()
        
        if is_correct:
            builder.row(
                InlineKeyboardButton(
                    text=f"🎉 +{points} очков!",
                    callback_data="celebrate"
                )
            )
        
        builder.row(
            InlineKeyboardButton(
                text="📊 Текущий счет",
                callback_data="current_score"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="⏭️ Готов к следующему",
                callback_data="ready_next"
            )
        )
        
        return builder.as_markup()
    
    @staticmethod
    def get_family_feud_options() -> InlineKeyboardMarkup:
        """Опции для игры 100 к одному"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(
                text="💡 Подсказка",
                callback_data="ff_hint"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="📝 Ввести ответ",
                callback_data="ff_text_input"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="⏭️ Пропустить ход",
                callback_data="ff_skip"
            )
        )
        
        return builder.as_markup()
    
    @staticmethod
    def get_time_warning(seconds_left: int) -> InlineKeyboardMarkup:
        """Предупреждение о времени"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(
                text=f"⏰ Осталось {seconds_left} сек",
                callback_data="time_warning"
            )
        )
        
        return builder.as_markup()
    
    @staticmethod
    def get_question_info(question_num: int, total_questions: int) -> InlineKeyboardMarkup:
        """Информация о вопросе"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(
                text=f"📊 Вопрос {question_num}/{total_questions}",
                callback_data="question_progress"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="🏆 Таблица лидеров",
                callback_data="leaderboard"
            )
        )
        
        return builder.as_markup()