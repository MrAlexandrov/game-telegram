"""
Session Control Keyboards for Admin Bot
"""

from typing import List, Dict, Any
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


class SessionControlKeyboard:
    """Клавиатуры для управления игровыми сессиями"""
    
    @staticmethod
    def get_session_control(session_id: str, status: str, players_count: int = 0) -> InlineKeyboardMarkup:
        """Основное управление сессией"""
        builder = InlineKeyboardBuilder()
        
        if status == "waiting":
            builder.row(
                InlineKeyboardButton(
                    text="▶️ Начать игру",
                    callback_data=f"start_game:{session_id}"
                )
            )
            builder.row(
                InlineKeyboardButton(
                    text="📋 QR-код для подключения",
                    callback_data=f"show_qr:{session_id}"
                )
            )
        elif status == "in_progress":
            builder.row(
                InlineKeyboardButton(
                    text="➡️ Следующий вопрос",
                    callback_data=f"next_question:{session_id}"
                ),
                InlineKeyboardButton(
                    text="⏸️ Пауза",
                    callback_data=f"pause_game:{session_id}"
                )
            )
        elif status == "paused":
            builder.row(
                InlineKeyboardButton(
                    text="▶️ Продолжить",
                    callback_data=f"resume_game:{session_id}"
                )
            )
        
        # Общие кнопки для всех состояний
        builder.row(
            InlineKeyboardButton(
                text=f"👥 Игроки ({players_count})",
                callback_data=f"show_players:{session_id}"
            )
        )
        
        if status in ["waiting", "in_progress", "paused"]:
            builder.row(
                InlineKeyboardButton(
                    text="🛑 Завершить игру",
                    callback_data=f"end_game:{session_id}"
                )
            )
        
        builder.row(
            InlineKeyboardButton(
                text="🔙 Назад",
                callback_data="active_sessions"
            )
        )
        
        return builder.as_markup()
    
    @staticmethod
    def get_active_sessions(sessions: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
        """Список активных сессий"""
        builder = InlineKeyboardBuilder()
        
        for session in sessions:
            status_emoji = {
                "waiting": "⏳",
                "in_progress": "🎮",
                "paused": "⏸️",
                "finished": "✅"
            }.get(session['status'], "❓")
            
            builder.row(
                InlineKeyboardButton(
                    text=f"{status_emoji} {session['game_title']} - {session['session_code']}",
                    callback_data=f"manage_session:{session['id']}"
                )
            )
        
        if not sessions:
            builder.row(
                InlineKeyboardButton(
                    text="🚀 Создать новую сессию",
                    callback_data="start_session"
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
    def get_question_control(session_id: str, question_num: int, total_questions: int) -> InlineKeyboardMarkup:
        """Управление текущим вопросом"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(
                text="📊 Ответы игроков",
                callback_data=f"show_answers:{session_id}"
            )
        )
        
        if question_num < total_questions:
            builder.row(
                InlineKeyboardButton(
                    text="➡️ Следующий вопрос",
                    callback_data=f"next_question:{session_id}"
                )
            )
        else:
            builder.row(
                InlineKeyboardButton(
                    text="🏁 Завершить игру",
                    callback_data=f"finish_game:{session_id}"
                )
            )
        
        builder.row(
            InlineKeyboardButton(
                text="⏸️ Пауза",
                callback_data=f"pause_game:{session_id}"
            ),
            InlineKeyboardButton(
                text="🛑 Остановить",
                callback_data=f"end_game:{session_id}"
            )
        )
        
        builder.row(
            InlineKeyboardButton(
                text="🔙 К управлению сессией",
                callback_data=f"manage_session:{session_id}"
            )
        )
        
        return builder.as_markup()
    
    @staticmethod
    def get_players_list(session_id: str, players: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
        """Список игроков в сессии"""
        builder = InlineKeyboardBuilder()
        
        # Показываем только первых 10 игроков в кнопках
        for player in players[:10]:
            score_text = f" ({player.get('score', 0)} очков)" if player.get('score') else ""
            builder.row(
                InlineKeyboardButton(
                    text=f"👤 {player['name']}{score_text}",
                    callback_data=f"player_info:{session_id}:{player['id']}"
                )
            )
        
        if len(players) > 10:
            builder.row(
                InlineKeyboardButton(
                    text=f"... и еще {len(players) - 10} игроков",
                    callback_data=f"all_players:{session_id}"
                )
            )
        
        builder.row(
            InlineKeyboardButton(
                text="🔙 К управлению сессией",
                callback_data=f"manage_session:{session_id}"
            )
        )
        
        return builder.as_markup()
    
    @staticmethod
    def get_game_results(session_id: str, show_details: bool = False) -> InlineKeyboardMarkup:
        """Результаты игры"""
        builder = InlineKeyboardBuilder()
        
        if not show_details:
            builder.row(
                InlineKeyboardButton(
                    text="📊 Подробные результаты",
                    callback_data=f"detailed_results:{session_id}"
                )
            )
        
        builder.row(
            InlineKeyboardButton(
                text="📤 Экспорт результатов",
                callback_data=f"export_results:{session_id}"
            )
        )
        
        builder.row(
            InlineKeyboardButton(
                text="🗑️ Удалить сессию",
                callback_data=f"delete_session:{session_id}"
            )
        )
        
        builder.row(
            InlineKeyboardButton(
                text="🔙 Активные сессии",
                callback_data="active_sessions"
            )
        )
        
        return builder.as_markup()