"""
Player Bot Connection Keyboards
Enhanced keyboards for connection system with QR codes and deep links
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import Optional, List, Dict, Any


class ConnectionKeyboards:
    """Enhanced keyboards for connection system"""
    
    @staticmethod
    def get_connection_methods() -> InlineKeyboardMarkup:
        """Get connection methods selection keyboard"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(
                text="🔤 Ввести код",
                callback_data="connect_by_code"
            )
        )
        
        builder.row(
            InlineKeyboardButton(
                text="📱 QR-код (инструкция)",
                callback_data="connect_by_qr_info"
            )
        )
        
        builder.row(
            InlineKeyboardButton(
                text="🔗 Ссылка-приглашение",
                callback_data="connect_by_invite"
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
    def get_enhanced_join_confirmation(
        game_code: str, 
        game_title: str,
        session_info: Optional[Dict[str, Any]] = None
    ) -> InlineKeyboardMarkup:
        """Enhanced join confirmation keyboard with more options"""
        builder = InlineKeyboardBuilder()
        
        # Main join button
        builder.row(
            InlineKeyboardButton(
                text="✅ Присоединиться",
                callback_data=f"confirm_join:{game_code}"
            )
        )
        
        # Additional info buttons
        if session_info:
            builder.row(
                InlineKeyboardButton(
                    text="ℹ️ Подробнее об игре",
                    callback_data=f"game_details:{game_code}"
                ),
                InlineKeyboardButton(
                    text="👥 Список игроков",
                    callback_data=f"show_players:{game_code}"
                )
            )
        
        # Navigation buttons
        builder.row(
            InlineKeyboardButton(
                text="🔄 Обновить",
                callback_data=f"refresh_game_info:{game_code}"
            ),
            InlineKeyboardButton(
                text="❌ Отмена",
                callback_data="back_to_main"
            )
        )
        
        return builder.as_markup()
    
    @staticmethod
    def get_qr_info_keyboard() -> InlineKeyboardMarkup:
        """QR code information keyboard"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(
                text="🔤 Ввести код вручную",
                callback_data="connect_by_code"
            )
        )
        
        builder.row(
            InlineKeyboardButton(
                text="📖 Как использовать QR-код",
                callback_data="qr_usage_guide"
            )
        )
        
        builder.row(
            InlineKeyboardButton(
                text="🔙 Назад",
                callback_data="join_game_enhanced"
            )
        )
        
        return builder.as_markup()
    
    @staticmethod
    def get_waiting_enhanced(
        game_code: Optional[str] = None,
        show_refresh: bool = True
    ) -> InlineKeyboardMarkup:
        """Enhanced waiting keyboard with more options"""
        builder = InlineKeyboardBuilder()
        
        # Status and info buttons
        builder.row(
            InlineKeyboardButton(
                text="👥 Игроки",
                callback_data="show_players"
            ),
            InlineKeyboardButton(
                text="ℹ️ Об игре",
                callback_data="game_info"
            )
        )
        
        # Refresh and share buttons
        if show_refresh:
            builder.row(
                InlineKeyboardButton(
                    text="🔄 Обновить",
                    callback_data="refresh_session_info"
                ),
                InlineKeyboardButton(
                    text="📤 Поделиться",
                    callback_data=f"share_game:{game_code}" if game_code else "share_game"
                )
            )
        
        # Settings and leave buttons
        builder.row(
            InlineKeyboardButton(
                text="⚙️ Настройки",
                callback_data="player_settings"
            ),
            InlineKeyboardButton(
                text="🚪 Покинуть",
                callback_data="leave_game"
            )
        )
        
        return builder.as_markup()
    
    @staticmethod
    def get_connection_error_keyboard(
        error_code: str,
        game_code: Optional[str] = None
    ) -> InlineKeyboardMarkup:
        """Error handling keyboard with context-specific options"""
        builder = InlineKeyboardBuilder()
        
        # Context-specific retry options
        if error_code in ["CODE_NOT_FOUND", "INVALID_CODE"]:
            builder.row(
                InlineKeyboardButton(
                    text="🔤 Ввести код заново",
                    callback_data="connect_by_code"
                )
            )
        elif error_code in ["CODE_EXPIRED", "CODE_DISABLED"]:
            builder.row(
                InlineKeyboardButton(
                    text="🔄 Попробовать другой код",
                    callback_data="connect_by_code"
                )
            )
        elif error_code == "SESSION_FULL":
            builder.row(
                InlineKeyboardButton(
                    text="⏳ Попробовать позже",
                    callback_data=f"retry_join:{game_code}" if game_code else "connect_by_code"
                )
            )
        elif error_code == "ALREADY_CONNECTED":
            builder.row(
                InlineKeyboardButton(
                    text="🔄 Переподключиться",
                    callback_data=f"reconnect:{game_code}" if game_code else "connect_by_code"
                )
            )
        else:
            # Generic retry
            builder.row(
                InlineKeyboardButton(
                    text="🔄 Попробовать снова",
                    callback_data="connect_by_code"
                )
            )
        
        # Help and support options
        builder.row(
            InlineKeyboardButton(
                text="❓ Помощь",
                callback_data="connection_help"
            ),
            InlineKeyboardButton(
                text="🏠 Главное меню",
                callback_data="back_to_main"
            )
        )
        
        return builder.as_markup()
    
    @staticmethod
    def get_player_settings() -> InlineKeyboardMarkup:
        """Player settings keyboard"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(
                text="👤 Изменить имя",
                callback_data="change_display_name"
            )
        )
        
        builder.row(
            InlineKeyboardButton(
                text="🔔 Уведомления",
                callback_data="notification_settings"
            ),
            InlineKeyboardButton(
                text="🎵 Звуки",
                callback_data="sound_settings"
            )
        )
        
        builder.row(
            InlineKeyboardButton(
                text="🌐 Язык",
                callback_data="language_settings"
            ),
            InlineKeyboardButton(
                text="🎨 Тема",
                callback_data="theme_settings"
            )
        )
        
        builder.row(
            InlineKeyboardButton(
                text="🔙 Назад",
                callback_data="back_to_waiting"
            )
        )
        
        return builder.as_markup()
    
    @staticmethod
    def get_share_options(game_code: str, game_title: str) -> InlineKeyboardMarkup:
        """Share game options keyboard"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(
                text="📋 Скопировать код",
                callback_data=f"copy_code:{game_code}"
            )
        )
        
        builder.row(
            InlineKeyboardButton(
                text="🔗 Поделиться ссылкой",
                callback_data=f"share_link:{game_code}"
            )
        )
        
        builder.row(
            InlineKeyboardButton(
                text="📱 QR-код",
                callback_data=f"show_qr:{game_code}"
            )
        )
        
        builder.row(
            InlineKeyboardButton(
                text="🔙 Назад",
                callback_data="back_to_waiting"
            )
        )
        
        return builder.as_markup()
    
    @staticmethod
    def get_connection_help() -> InlineKeyboardMarkup:
        """Connection help keyboard"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(
                text="🎯 Как подключиться",
                callback_data="help_how_to_connect"
            )
        )
        
        builder.row(
            InlineKeyboardButton(
                text="❓ Частые вопросы",
                callback_data="help_faq"
            ),
            InlineKeyboardButton(
                text="🐛 Проблемы",
                callback_data="help_troubleshooting"
            )
        )
        
        builder.row(
            InlineKeyboardButton(
                text="📱 QR-коды",
                callback_data="help_qr_codes"
            ),
            InlineKeyboardButton(
                text="🔗 Ссылки",
                callback_data="help_deep_links"
            )
        )
        
        builder.row(
            InlineKeyboardButton(
                text="💬 Поддержка",
                callback_data="contact_support"
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
    def get_reconnection_options(game_code: str) -> InlineKeyboardMarkup:
        """Reconnection options keyboard"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(
                text="🔄 Переподключиться",
                callback_data=f"force_reconnect:{game_code}"
            )
        )
        
        builder.row(
            InlineKeyboardButton(
                text="🆕 Новое подключение",
                callback_data=f"new_connection:{game_code}"
            )
        )
        
        builder.row(
            InlineKeyboardButton(
                text="ℹ️ Статус игры",
                callback_data=f"check_game_status:{game_code}"
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
    def get_game_details_keyboard(game_code: str) -> InlineKeyboardMarkup:
        """Game details keyboard"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(
                text="👥 Игроки",
                callback_data=f"show_players:{game_code}"
            ),
            InlineKeyboardButton(
                text="📊 Статистика",
                callback_data=f"game_stats:{game_code}"
            )
        )
        
        builder.row(
            InlineKeyboardButton(
                text="⚙️ Настройки игры",
                callback_data=f"game_settings:{game_code}"
            )
        )
        
        builder.row(
            InlineKeyboardButton(
                text="🔙 Назад к подключению",
                callback_data=f"back_to_join:{game_code}"
            )
        )
        
        return builder.as_markup()
    
    @staticmethod
    def get_players_list_keyboard(
        game_code: str,
        players: List[Dict[str, Any]],
        current_user_id: Optional[int] = None
    ) -> InlineKeyboardMarkup:
        """Players list keyboard with interactive options"""
        builder = InlineKeyboardBuilder()
        
        # Show player actions if there are players
        if players:
            builder.row(
                InlineKeyboardButton(
                    text="🔄 Обновить список",
                    callback_data=f"refresh_players:{game_code}"
                )
            )
            
            # If current user is in the list, show additional options
            if current_user_id and any(p.get("user_id") == current_user_id for p in players):
                builder.row(
                    InlineKeyboardButton(
                        text="📊 Моя статистика",
                        callback_data=f"my_stats:{game_code}"
                    )
                )
        
        builder.row(
            InlineKeyboardButton(
                text="🔙 Назад",
                callback_data="back_to_waiting"
            )
        )
        
        return builder.as_markup()


# Extend existing GameJoinKeyboard with new methods
class EnhancedGameJoinKeyboard:
    """Enhanced version of GameJoinKeyboard with connection features"""
    
    @staticmethod
    def get_connection_methods() -> InlineKeyboardMarkup:
        """Get connection methods keyboard"""
        return ConnectionKeyboards.get_connection_methods()
    
    @staticmethod
    def get_join_confirmation(
        game_code: str, 
        game_title: str,
        session_info: Optional[Dict[str, Any]] = None
    ) -> InlineKeyboardMarkup:
        """Enhanced join confirmation"""
        return ConnectionKeyboards.get_enhanced_join_confirmation(
            game_code, game_title, session_info
        )
    
    @staticmethod
    def get_qr_info_keyboard() -> InlineKeyboardMarkup:
        """QR info keyboard"""
        return ConnectionKeyboards.get_qr_info_keyboard()
    
    @staticmethod
    def get_waiting_game_start(
        game_code: Optional[str] = None
    ) -> InlineKeyboardMarkup:
        """Enhanced waiting keyboard"""
        return ConnectionKeyboards.get_waiting_enhanced(game_code)
    
    @staticmethod
    def get_connection_error(
        error_code: str,
        game_code: Optional[str] = None
    ) -> InlineKeyboardMarkup:
        """Connection error keyboard"""
        return ConnectionKeyboards.get_connection_error_keyboard(error_code, game_code)
    
    @staticmethod
    def get_share_game(game_code: str, game_title: str) -> InlineKeyboardMarkup:
        """Share game keyboard"""
        return ConnectionKeyboards.get_share_options(game_code, game_title)