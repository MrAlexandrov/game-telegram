"""
Game Join Keyboards for Player Bot
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


class GameJoinKeyboard:
    """Клавиатуры для подключения к игре"""
    
    @staticmethod
    def get_join_options() -> InlineKeyboardMarkup:
        """Варианты подключения к игре"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(
                text="🔤 Ввести код игры",
                callback_data="enter_game_code"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="📱 Сканировать QR-код",
                callback_data="scan_qr_info"
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
    def get_join_confirmation(session_code: str, game_title: str) -> InlineKeyboardMarkup:
        """Подтверждение подключения к игре"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(
                text="✅ Присоединиться",
                callback_data=f"confirm_join:{session_code}"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="❌ Отмена",
                callback_data="join_game"
            )
        )
        
        return builder.as_markup()
    
    @staticmethod
    def get_waiting_game_start() -> InlineKeyboardMarkup:
        """Ожидание начала игры"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(
                text="👥 Список игроков",
                callback_data="show_players"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="📊 Информация об игре",
                callback_data="game_info"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="🚪 Покинуть игру",
                callback_data="leave_game"
            )
        )
        
        return builder.as_markup()
    
    @staticmethod
    def get_leave_confirmation() -> InlineKeyboardMarkup:
        """Подтверждение выхода из игры"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(
                text="✅ Да, покинуть",
                callback_data="confirm_leave"
            ),
            InlineKeyboardButton(
                text="❌ Остаться",
                callback_data="cancel_leave"
            )
        )
        
        return builder.as_markup()
    
    @staticmethod
    def get_reconnect_options(session_code: str) -> InlineKeyboardMarkup:
        """Опции переподключения"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(
                text="🔄 Переподключиться",
                callback_data=f"reconnect:{session_code}"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="🏠 Главное меню",
                callback_data="back_to_main"
            )
        )
        
        return builder.as_markup()
    
    @staticmethod
    def get_qr_scan_info() -> InlineKeyboardMarkup:
        """Информация о сканировании QR-кода"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(
                text="🔤 Ввести код вручную",
                callback_data="enter_game_code"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="🔙 Назад",
                callback_data="join_game"
            )
        )
        
        return builder.as_markup()