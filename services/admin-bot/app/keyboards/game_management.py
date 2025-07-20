"""
Game Management Keyboards for Admin Bot
"""

from typing import List, Dict, Any
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


class GameManagementKeyboard:
    """Клавиатуры для управления играми"""
    
    @staticmethod
    def get_games_list(games: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
        """Список игр администратора"""
        builder = InlineKeyboardBuilder()
        
        for game in games:
            builder.row(
                InlineKeyboardButton(
                    text=f"🎮 {game['title']} ({game['game_type']})",
                    callback_data=f"game_details:{game['id']}"
                )
            )
        
        if not games:
            builder.row(
                InlineKeyboardButton(
                    text="➕ Создать первую игру",
                    callback_data="create_game"
                )
            )
        else:
            builder.row(
                InlineKeyboardButton(
                    text="➕ Создать новую игру",
                    callback_data="create_game"
                )
            )
        
        builder.row(
            InlineKeyboardButton(
                text="🔙 Главное меню",
                callback_data="back_to_main"
            )
        )
        
        return builder.as_markup()
    
    @staticmethod
    def get_game_details(game_id: str, has_active_session: bool = False) -> InlineKeyboardMarkup:
        """Детали игры и доступные действия"""
        builder = InlineKeyboardBuilder()
        
        if not has_active_session:
            builder.row(
                InlineKeyboardButton(
                    text="🚀 Запустить сессию",
                    callback_data=f"start_session:{game_id}"
                )
            )
        else:
            builder.row(
                InlineKeyboardButton(
                    text="⚡ Управлять сессией",
                    callback_data=f"manage_session:{game_id}"
                )
            )
        
        builder.row(
            InlineKeyboardButton(
                text="✏️ Редактировать",
                callback_data=f"edit_game:{game_id}"
            ),
            InlineKeyboardButton(
                text="📊 Статистика",
                callback_data=f"game_stats:{game_id}"
            )
        )
        
        builder.row(
            InlineKeyboardButton(
                text="🗑️ Удалить игру",
                callback_data=f"delete_game:{game_id}"
            )
        )
        
        builder.row(
            InlineKeyboardButton(
                text="🔙 К списку игр",
                callback_data="my_games"
            )
        )
        
        return builder.as_markup()
    
    @staticmethod
    def get_game_creation_options() -> InlineKeyboardMarkup:
        """Опции создания игры"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(
                text="📁 Загрузить игровой пак",
                callback_data="upload_game_pack"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="✏️ Создать вручную",
                callback_data="create_manual"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="📋 Использовать шаблон",
                callback_data="use_template"
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
    def get_game_templates() -> InlineKeyboardMarkup:
        """Доступные шаблоны игр"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(
                text="❓ Викторина - История",
                callback_data="template:quiz_history"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="❓ Викторина - География",
                callback_data="template:quiz_geography"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="💯 100 к одному - Семья",
                callback_data="template:family_feud_family"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="🔙 Назад",
                callback_data="create_game"
            )
        )
        
        return builder.as_markup()
    
    @staticmethod
    def get_upload_confirmation(filename: str) -> InlineKeyboardMarkup:
        """Подтверждение загрузки файла"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(
                text="✅ Создать игру",
                callback_data=f"confirm_upload:{filename}"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="❌ Отмена",
                callback_data="cancel_upload"
            )
        )
        
        return builder.as_markup()