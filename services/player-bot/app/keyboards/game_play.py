"""
Game Play Keyboards for Player Bot
"""

from typing import List, Dict, Any
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


class GamePlayKeyboard:
    """Клавиатуры для игрового процесса"""
    
    @staticmethod
    def get_game_status() -> InlineKeyboardMarkup:
        """Статус игры"""
        builder = InlineKeyboardBuilder()
        
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
                text="ℹ️ Информация об игре",
                callback_data="game_info"
            )
        )
        
        return builder.as_markup()
    
    @staticmethod
    def get_leaderboard(players: List[Dict[str, Any]], current_user_id: int) -> InlineKeyboardMarkup:
        """Таблица лидеров"""
        builder = InlineKeyboardBuilder()
        
        # Показываем топ-5 игроков
        for i, player in enumerate(players[:5], 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            is_current = player.get('user_id') == current_user_id
            name = f"👤 {player['name']}" if is_current else player['name']
            
            builder.row(
                InlineKeyboardButton(
                    text=f"{medal} {name} - {player['score']} очков",
                    callback_data=f"player_details:{player['id']}"
                )
            )
        
        if len(players) > 5:
            builder.row(
                InlineKeyboardButton(
                    text=f"... и еще {len(players) - 5} игроков",
                    callback_data="full_leaderboard"
                )
            )
        
        builder.row(
            InlineKeyboardButton(
                text="🔄 Обновить",
                callback_data="refresh_leaderboard"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="🔙 Назад",
                callback_data="game_status"
            )
        )
        
        return builder.as_markup()
    
    @staticmethod
    def get_score_details(score: int, correct_answers: int, total_answers: int) -> InlineKeyboardMarkup:
        """Детали счета игрока"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(
                text="📈 Статистика ответов",
                callback_data="answer_stats"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="🏆 Сравнить с лидерами",
                callback_data="compare_leaders"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="🔙 Назад",
                callback_data="game_status"
            )
        )
        
        return builder.as_markup()
    
    @staticmethod
    def get_game_paused() -> InlineKeyboardMarkup:
        """Игра на паузе"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(
                text="⏸️ Игра на паузе",
                callback_data="pause_info"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="📊 Текущие результаты",
                callback_data="current_results"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="💬 Чат с игроками",
                callback_data="player_chat"
            )
        )
        
        return builder.as_markup()
    
    @staticmethod
    def get_final_results(final_position: int, total_players: int) -> InlineKeyboardMarkup:
        """Финальные результаты"""
        builder = InlineKeyboardBuilder()
        
        if final_position <= 3:
            builder.row(
                InlineKeyboardButton(
                    text="🎉 Поздравляем!",
                    callback_data="celebration"
                )
            )
        
        builder.row(
            InlineKeyboardButton(
                text="🏆 Полная таблица результатов",
                callback_data="full_results"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="📊 Моя статистика",
                callback_data="my_game_stats"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="🎮 Играть еще раз",
                callback_data="play_again"
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
    def get_game_info(game_type: str, questions_total: int, current_question: int = 0) -> InlineKeyboardMarkup:
        """Информация об игре"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(
                text="📋 Правила игры",
                callback_data=f"rules:{game_type}"
            )
        )
        
        if current_question > 0:
            builder.row(
                InlineKeyboardButton(
                    text=f"📊 Прогресс: {current_question}/{questions_total}",
                    callback_data="game_progress"
                )
            )
        
        builder.row(
            InlineKeyboardButton(
                text="👥 Список игроков",
                callback_data="players_list"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="🔙 Назад",
                callback_data="game_status"
            )
        )
        
        return builder.as_markup()
    
    @staticmethod
    def get_waiting_next_question() -> InlineKeyboardMarkup:
        """Ожидание следующего вопроса"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(
                text="⏳ Ожидание следующего вопроса...",
                callback_data="waiting_status"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="📊 Промежуточные результаты",
                callback_data="interim_results"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="💬 Обсудить с игроками",
                callback_data="player_discussion"
            )
        )
        
        return builder.as_markup()
    
    @staticmethod
    def get_answer_stats(correct: int, incorrect: int, skipped: int) -> InlineKeyboardMarkup:
        """Статистика ответов"""
        builder = InlineKeyboardBuilder()
        
        total = correct + incorrect + skipped
        if total > 0:
            accuracy = round((correct / total) * 100, 1)
            builder.row(
                InlineKeyboardButton(
                    text=f"🎯 Точность: {accuracy}%",
                    callback_data="accuracy_details"
                )
            )
        
        builder.row(
            InlineKeyboardButton(
                text="📈 Динамика по вопросам",
                callback_data="question_dynamics"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="🔙 К счету",
                callback_data="my_score"
            )
        )
        
        return builder.as_markup()
    
    @staticmethod
    def get_celebration(achievement: str = None) -> InlineKeyboardMarkup:
        """Поздравление с достижением"""
        builder = InlineKeyboardBuilder()
        
        if achievement:
            builder.row(
                InlineKeyboardButton(
                    text=f"🏆 {achievement}",
                    callback_data="achievement_details"
                )
            )
        
        builder.row(
            InlineKeyboardButton(
                text="📸 Поделиться результатом",
                callback_data="share_result"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="🎮 Играть еще",
                callback_data="play_again"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="🏠 Главное меню",
                callback_data="back_to_main"
            )
        )
        
        return builder.as_markup()