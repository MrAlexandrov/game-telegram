"""
Main Menu Keyboards for Player Bot
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


class MainMenuKeyboard:
    """Главное меню игрока"""
    
    @staticmethod
    def get_main_menu() -> InlineKeyboardMarkup:
        """Основное меню игрока"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(
                text="🎮 Присоединиться к игре",
                callback_data="join_game"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="📊 Мой счет",
                callback_data="my_score"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="🏆 Таблица лидеров",
                callback_data="leaderboard"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="ℹ️ Помощь",
                callback_data="help"
            )
        )
        
        return builder.as_markup()
    
    @staticmethod
    def get_quick_join_keyboard() -> ReplyKeyboardMarkup:
        """Быстрое подключение через reply клавиатуру"""
        builder = ReplyKeyboardBuilder()
        
        builder.row(
            KeyboardButton(text="🎮 Ввести код игры")
        )
        builder.row(
            KeyboardButton(text="📊 Мой счет"),
            KeyboardButton(text="ℹ️ Помощь")
        )
        
        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=False
        )
    
    @staticmethod
    def get_help_menu() -> InlineKeyboardMarkup:
        """Меню помощи"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(
                text="🎯 Как играть",
                callback_data="help_how_to_play"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="🎮 Типы игр",
                callback_data="help_game_types"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="🏆 Система очков",
                callback_data="help_scoring"
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
    
    @staticmethod
    def remove_keyboard() -> ReplyKeyboardMarkup:
        """Удалить reply клавиатуру"""
        return ReplyKeyboardMarkup(
            keyboard=[],
            resize_keyboard=True,
            remove_keyboard=True
        )