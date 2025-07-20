"""
Main Menu Keyboards for Admin Bot
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


class MainMenuKeyboard:
    """Главное меню администратора"""
    
    @staticmethod
    def get_main_menu() -> InlineKeyboardMarkup:
        """Основное меню администратора"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(
                text="🎮 Создать игру",
                callback_data="create_game"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="📋 Мои игры",
                callback_data="my_games"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="🚀 Запустить сессию",
                callback_data="start_session"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="⚡ Активные сессии",
                callback_data="active_sessions"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="📊 Статистика",
                callback_data="statistics"
            )
        )
        
        return builder.as_markup()
    
    @staticmethod
    def get_game_types() -> InlineKeyboardMarkup:
        """Выбор типа игры"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(
                text="❓ Викторина",
                callback_data="game_type:quiz"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="💯 100 к одному",
                callback_data="game_type:family_feud"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="🔙 Назад",
                callback_data="back_to_main"
            )
        )
        
        return builder.as_markup()
    
    @staticmethod
    def get_confirmation(action: str, item_id: str = None) -> InlineKeyboardMarkup:
        """Клавиатура подтверждения действия"""
        builder = InlineKeyboardBuilder()
        
        confirm_data = f"confirm:{action}"
        cancel_data = f"cancel:{action}"
        
        if item_id:
            confirm_data += f":{item_id}"
            cancel_data += f":{item_id}"
        
        builder.row(
            InlineKeyboardButton(
                text="✅ Подтвердить",
                callback_data=confirm_data
            ),
            InlineKeyboardButton(
                text="❌ Отмена",
                callback_data=cancel_data
            )
        )
        
        return builder.as_markup()
    
    @staticmethod
    def get_back_button(callback_data: str = "back_to_main") -> InlineKeyboardMarkup:
        """Кнопка возврата"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(
                text="🔙 Назад",
                callback_data=callback_data
            )
        )
        
        return builder.as_markup()