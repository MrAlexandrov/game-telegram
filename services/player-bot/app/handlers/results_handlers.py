"""
Results handlers for displaying game results and player statistics
"""
import asyncio
from datetime import datetime
from typing import Dict, Any, List
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import structlog

from ..services.api_client import APIClient
from ..keyboards.main_menu import get_main_menu_keyboard
from ..states import PlayerStates

logger = structlog.get_logger()
router = Router()


@router.message(Command("stats"))
async def show_player_stats(message: Message, state: FSMContext):
    """Show player statistics"""
    try:
        user_data = await state.get_data()
        player_id = str(message.from_user.id)
        
        # Get player statistics from analytics service
        api_client = APIClient()
        stats_response = await api_client.get_player_stats(player_id)
        
        if not stats_response or not stats_response.get("stats"):
            await message.answer(
                "📊 У вас пока нет статистики игр.\n"
                "Сыграйте несколько игр, чтобы увидеть свои результаты!",
                reply_markup=get_main_menu_keyboard()
            )
            return
        
        stats = stats_response["stats"]
        recent_games = stats_response.get("recent_games", [])
        achievements = stats_response.get("achievements", [])
        
        # Format statistics message
        stats_text = format_player_stats(stats, recent_games, achievements)
        
        # Create inline keyboard for detailed stats
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📈 Детальная статистика", callback_data="detailed_stats"),
                InlineKeyboardButton(text="🏆 Достижения", callback_data="show_achievements")
            ],
            [
                InlineKeyboardButton(text="📊 Сравнить с другими", callback_data="compare_stats"),
                InlineKeyboardButton(text="📋 История игр", callback_data="game_history")
            ],
            [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
        ])
        
        await message.answer(stats_text, reply_markup=keyboard, parse_mode="HTML")
        
    except Exception as e:
        logger.error("Failed to show player stats", error=str(e), user_id=message.from_user.id)
        await message.answer(
            "❌ Произошла ошибка при получении статистики. Попробуйте позже.",
            reply_markup=get_main_menu_keyboard()
        )


@router.callback_query(F.data == "show_game_results")
async def show_game_results(callback: CallbackQuery, state: FSMContext):
    """Show results after game completion"""
    try:
        user_data = await state.get_data()
        session_id = user_data.get("current_session_id")
        
        if not session_id:
            await callback.answer("Сессия не найдена")
            return
        
        # Get session results from analytics service
        api_client = APIClient()
        results = await api_client.get_session_results(session_id)
        
        if not results:
            await callback.answer("Результаты не найдены")
            return
        
        # Format results message
        results_text = format_game_results(results, str(callback.from_user.id))
        
        # Create keyboard for result actions
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Моя статистика", callback_data="detailed_stats"),
                InlineKeyboardButton(text="🏆 Таблица лидеров", callback_data="show_leaderboard")
            ],
            [
                InlineKeyboardButton(text="🎮 Играть еще", callback_data="play_again"),
                InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")
            ]
        ])
        
        await callback.message.edit_text(results_text, reply_markup=keyboard, parse_mode="HTML")
        
    except Exception as e:
        logger.error("Failed to show game results", error=str(e), user_id=callback.from_user.id)
        await callback.answer("Ошибка при получении результатов")


@router.callback_query(F.data == "detailed_stats")
async def show_detailed_stats(callback: CallbackQuery, state: FSMContext):
    """Show detailed player statistics"""
    try:
        player_id = str(callback.from_user.id)
        
        # Get detailed statistics
        api_client = APIClient()
        stats_response = await api_client.get_player_stats(player_id, include_recent_games=True)
        
        if not stats_response:
            await callback.answer("Статистика не найдена")
            return
        
        stats = stats_response["stats"]
        recent_games = stats_response.get("recent_games", [])
        
        # Format detailed statistics
        detailed_text = format_detailed_stats(stats, recent_games)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📈 График прогресса", callback_data="progress_chart"),
                InlineKeyboardButton(text="🎯 По категориям", callback_data="category_stats")
            ],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="show_stats")]
        ])
        
        await callback.message.edit_text(detailed_text, reply_markup=keyboard, parse_mode="HTML")
        
    except Exception as e:
        logger.error("Failed to show detailed stats", error=str(e), user_id=callback.from_user.id)
        await callback.answer("Ошибка при получении детальной статистики")


@router.callback_query(F.data == "show_achievements")
async def show_achievements(callback: CallbackQuery, state: FSMContext):
    """Show player achievements"""
    try:
        player_id = str(callback.from_user.id)
        
        # Get player achievements
        api_client = APIClient()
        achievements = await api_client.get_player_achievements(player_id)
        
        if not achievements:
            await callback.message.edit_text(
                "🏆 <b>Достижения</b>\n\n"
                "У вас пока нет достижений.\n"
                "Играйте больше, чтобы получить награды!",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Назад", callback_data="show_stats")]
                ]),
                parse_mode="HTML"
            )
            return
        
        # Format achievements
        achievements_text = format_achievements(achievements)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🎯 Доступные достижения", callback_data="available_achievements"),
                InlineKeyboardButton(text="📊 Прогресс", callback_data="achievement_progress")
            ],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="show_stats")]
        ])
        
        await callback.message.edit_text(achievements_text, reply_markup=keyboard, parse_mode="HTML")
        
    except Exception as e:
        logger.error("Failed to show achievements", error=str(e), user_id=callback.from_user.id)
        await callback.answer("Ошибка при получении достижений")


@router.callback_query(F.data == "show_leaderboard")
async def show_leaderboard(callback: CallbackQuery, state: FSMContext):
    """Show global leaderboard"""
    try:
        # Get leaderboard data
        api_client = APIClient()
        leaderboard = await api_client.get_leaderboard("global", limit=10)
        
        if not leaderboard:
            await callback.answer("Таблица лидеров недоступна")
            return
        
        # Format leaderboard
        leaderboard_text = format_leaderboard(leaderboard, str(callback.from_user.id))
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🏆 Топ-50", callback_data="leaderboard_top50"),
                InlineKeyboardButton(text="📅 За неделю", callback_data="leaderboard_weekly")
            ],
            [
                InlineKeyboardButton(text="🎮 По типу игры", callback_data="leaderboard_by_game"),
                InlineKeyboardButton(text="🔙 Назад", callback_data="show_game_results")
            ]
        ])
        
        await callback.message.edit_text(leaderboard_text, reply_markup=keyboard, parse_mode="HTML")
        
    except Exception as e:
        logger.error("Failed to show leaderboard", error=str(e), user_id=callback.from_user.id)
        await callback.answer("Ошибка при получении таблицы лидеров")


@router.callback_query(F.data == "game_history")
async def show_game_history(callback: CallbackQuery, state: FSMContext):
    """Show player's game history"""
    try:
        player_id = str(callback.from_user.id)
        
        # Get game history
        api_client = APIClient()
        history = await api_client.get_player_game_history(player_id, limit=10)
        
        if not history:
            await callback.message.edit_text(
                "📋 <b>История игр</b>\n\n"
                "У вас пока нет истории игр.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Назад", callback_data="show_stats")]
                ]),
                parse_mode="HTML"
            )
            return
        
        # Format game history
        history_text = format_game_history(history)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Показать больше", callback_data="more_history"),
                InlineKeyboardButton(text="🔍 Фильтры", callback_data="history_filters")
            ],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="show_stats")]
        ])
        
        await callback.message.edit_text(history_text, reply_markup=keyboard, parse_mode="HTML")
        
    except Exception as e:
        logger.error("Failed to show game history", error=str(e), user_id=callback.from_user.id)
        await callback.answer("Ошибка при получении истории игр")


def format_player_stats(stats: Dict[str, Any], recent_games: List[Dict], achievements: List[Dict]) -> str:
    """Format player statistics for display"""
    level_progress = (stats.get("experience_points", 0) % 1000) / 10  # Progress to next level
    
    text = f"""
📊 <b>Ваша статистика</b>

👤 <b>Игрок:</b> {stats.get('player_name', 'Неизвестно')}
🎯 <b>Уровень:</b> {stats.get('level', 1)} ({level_progress:.1f}% до следующего)
⭐ <b>Рейтинг:</b> {stats.get('rating', 1000)}

🎮 <b>Игры:</b>
• Всего игр: {stats.get('total_games', 0)}
• Завершено: {stats.get('games_completed', 0)}
• Побед: {stats.get('games_won', 0)}
• Процент побед: {(stats.get('games_won', 0) / max(stats.get('total_games', 1), 1) * 100):.1f}%

📈 <b>Очки:</b>
• Общий счет: {stats.get('total_score', 0):,}
• Средний счет: {stats.get('average_score', 0):.1f}
• Лучший результат: {stats.get('best_score', 0):,}

🎯 <b>Точность:</b>
• Общая точность: {stats.get('overall_accuracy', 0):.1f}%
• Правильных ответов: {stats.get('total_correct_answers', 0)}
• Всего ответов: {stats.get('total_questions_answered', 0)}

⏱️ <b>Время:</b>
• Общее время: {format_duration(stats.get('total_time_played', 0))}
• Средняя длительность игры: {format_duration(stats.get('average_game_duration', 0))}
• Самая быстрая игра: {format_duration(stats.get('fastest_game', 0)) if stats.get('fastest_game') else 'Н/Д'}

🔥 <b>Серии:</b>
• Текущая серия побед: {stats.get('current_streak', 0)}
• Лучшая серия: {stats.get('best_streak', 0)}

🏆 <b>Достижения:</b> {len(achievements)}
"""
    
    if recent_games:
        text += f"\n🕐 <b>Последняя игра:</b> {format_last_game(recent_games[0])}"
    
    return text.strip()


def format_detailed_stats(stats: Dict[str, Any], recent_games: List[Dict]) -> str:
    """Format detailed statistics"""
    text = f"""
📈 <b>Детальная статистика</b>

🎮 <b>По типам игр:</b>
"""
    
    games_by_type = stats.get('games_by_type', {})
    for game_type, count in games_by_type.items():
        text += f"• {game_type.title()}: {count} игр\n"
    
    if not games_by_type:
        text += "• Данные отсутствуют\n"
    
    text += f"""
📊 <b>Прогресс:</b>
• Опыт: {stats.get('experience_points', 0):,} XP
• Уровень: {stats.get('level', 1)}
• До следующего уровня: {1000 - (stats.get('experience_points', 0) % 1000)} XP

🎯 <b>Рекорды:</b>
• Лучший счет: {stats.get('best_score', 0):,}
• Худший счет: {stats.get('worst_score', 0):,}
• Лучшая серия: {stats.get('best_streak', 0)}
"""
    
    if recent_games:
        text += "\n📋 <b>Последние игры:</b>\n"
        for i, game in enumerate(recent_games[:5], 1):
            text += f"{i}. {format_recent_game(game)}\n"
    
    return text.strip()


def format_game_results(results: Dict[str, Any], player_id: str) -> str:
    """Format game results for display"""
    game_result = results.get("game_result", {})
    player_results = results.get("player_results", [])
    
    # Find current player's result
    player_result = None
    for result in player_results:
        if str(result.get("player_id")) == player_id:
            player_result = result
            break
    
    text = f"""
🎮 <b>Результаты игры</b>

🎯 <b>Игра:</b> {game_result.get('game_name', 'Неизвестно')}
⏱️ <b>Длительность:</b> {format_duration(game_result.get('duration', 0))}
👥 <b>Игроков:</b> {game_result.get('total_players', 0)}
✅ <b>Завершили:</b> {game_result.get('completed_players', 0)}

"""
    
    if player_result:
        text += f"""
🏆 <b>Ваш результат:</b>
• Место: {player_result.get('position', 'Н/Д')}
• Очки: {player_result.get('total_score', 0):,}
• Точность: {player_result.get('accuracy_percentage', 0):.1f}%
• Правильных ответов: {player_result.get('correct_answers', 0)}/{player_result.get('total_questions', 0)}
• Среднее время на вопрос: {player_result.get('average_time_per_question', 0):.1f}с

"""
    
    # Show top 3 players
    text += "🏅 <b>Топ-3 игроков:</b>\n"
    for i, result in enumerate(player_results[:3], 1):
        medal = ["🥇", "🥈", "🥉"][i-1]
        is_current_player = str(result.get("player_id")) == player_id
        name = result.get("player_name", "Неизвестно")
        if is_current_player:
            name = f"<b>{name} (Вы)</b>"
        
        text += f"{medal} {name}: {result.get('total_score', 0):,} очков ({result.get('accuracy_percentage', 0):.1f}%)\n"
    
    return text.strip()


def format_achievements(achievements: List[Dict]) -> str:
    """Format achievements for display"""
    text = "🏆 <b>Ваши достижения</b>\n\n"
    
    if not achievements:
        text += "У вас пока нет достижений.\nИграйте больше, чтобы получить награды!"
        return text
    
    # Group achievements by type
    by_type = {}
    for achievement in achievements:
        ach_type = achievement.get("achievement", {}).get("type", "other")
        if ach_type not in by_type:
            by_type[ach_type] = []
        by_type[ach_type].append(achievement)
    
    type_icons = {
        "speed": "⚡",
        "accuracy": "🎯",
        "participation": "🎮",
        "streak": "🔥",
        "milestone": "🏁",
        "special": "⭐"
    }
    
    for ach_type, achs in by_type.items():
        icon = type_icons.get(ach_type, "🏆")
        text += f"{icon} <b>{ach_type.title()}:</b>\n"
        
        for ach in achs:
            achievement = ach.get("achievement", {})
            earned_at = ach.get("earned_at", "")
            if earned_at:
                date_str = datetime.fromisoformat(earned_at.replace('Z', '+00:00')).strftime("%d.%m.%Y")
            else:
                date_str = "Неизвестно"
            
            text += f"• {achievement.get('name', 'Неизвестно')} ({date_str})\n"
            text += f"  <i>{achievement.get('description', '')}</i>\n"
        
        text += "\n"
    
    return text.strip()


def format_leaderboard(leaderboard: Dict[str, Any], player_id: str) -> str:
    """Format leaderboard for display"""
    entries = leaderboard.get("entries", [])
    leaderboard_type = leaderboard.get("type", "global")
    
    text = f"🏆 <b>Таблица лидеров ({leaderboard_type})</b>\n\n"
    
    if not entries:
        text += "Таблица лидеров пуста."
        return text
    
    for entry in entries:
        position = entry.get("position", 0)
        name = entry.get("player_name", "Неизвестно")
        score = entry.get("score", 0)
        games = entry.get("games_played", 0)
        accuracy = entry.get("accuracy", 0)
        
        # Highlight current player
        is_current_player = str(entry.get("player_id")) == player_id
        if is_current_player:
            name = f"<b>{name} (Вы)</b>"
        
        # Position emoji
        if position == 1:
            pos_emoji = "🥇"
        elif position == 2:
            pos_emoji = "🥈"
        elif position == 3:
            pos_emoji = "🥉"
        else:
            pos_emoji = f"{position}."
        
        text += f"{pos_emoji} {name}\n"
        text += f"   💰 {score:,} очков | 🎮 {games} игр | 🎯 {accuracy:.1f}%\n\n"
    
    return text.strip()


def format_game_history(history: List[Dict]) -> str:
    """Format game history for display"""
    text = "📋 <b>История игр</b>\n\n"
    
    if not history:
        text += "История игр пуста."
        return text
    
    for i, game in enumerate(history, 1):
        game_name = game.get("game_name", "Неизвестно")
        score = game.get("total_score", 0)
        position = game.get("position", "Н/Д")
        accuracy = game.get("accuracy_percentage", 0)
        date = game.get("created_at", "")
        
        if date:
            date_str = datetime.fromisoformat(date.replace('Z', '+00:00')).strftime("%d.%m %H:%M")
        else:
            date_str = "Неизвестно"
        
        text += f"{i}. <b>{game_name}</b> ({date_str})\n"
        text += f"   🏆 Место: {position} | 💰 {score:,} очков | 🎯 {accuracy:.1f}%\n\n"
    
    return text.strip()


def format_duration(seconds: float) -> str:
    """Format duration in human readable format"""
    if seconds < 60:
        return f"{seconds:.0f}с"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes:.0f}м {secs:.0f}с"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours:.0f}ч {minutes:.0f}м"


def format_last_game(game: Dict[str, Any]) -> str:
    """Format last game info"""
    game_name = game.get("game_name", "Неизвестно")
    score = game.get("total_score", 0)
    date = game.get("start_time", "")
    
    if date:
        date_str = datetime.fromisoformat(date.replace('Z', '+00:00')).strftime("%d.%m %H:%M")
    else:
        date_str = "Неизвестно"
    
    return f"{game_name} - {score:,} очков ({date_str})"


def format_recent_game(game: Dict[str, Any]) -> str:
    """Format recent game for detailed stats"""
    game_name = game.get("game_name", "Неизвестно")
    score = game.get("total_score", 0)
    position = game.get("position", "Н/Д")
    
    return f"{game_name}: {position} место, {score:,} очков"
