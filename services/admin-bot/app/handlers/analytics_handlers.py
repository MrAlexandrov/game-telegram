"""
Analytics handlers for admin bot - monitoring and analytics functionality
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import structlog

from ..services.api_client import APIClient
from ..keyboards.main_menu import get_admin_menu_keyboard
from ..states import AdminStates

logger = structlog.get_logger()
router = Router()


@router.message(Command("analytics"))
async def show_analytics_menu(message: Message, state: FSMContext):
    """Show analytics main menu"""
    try:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Системная аналитика", callback_data="system_analytics"),
                InlineKeyboardButton(text="🎮 Аналитика игр", callback_data="games_analytics")
            ],
            [
                InlineKeyboardButton(text="👥 Активные игроки", callback_data="players_analytics"),
                InlineKeyboardButton(text="📈 Тренды", callback_data="trends_analytics")
            ],
            [
                InlineKeyboardButton(text="🏆 Лидерборды", callback_data="leaderboards_analytics"),
                InlineKeyboardButton(text="⚡ Live мониторинг", callback_data="live_monitoring")
            ],
            [
                InlineKeyboardButton(text="📋 Экспорт данных", callback_data="export_data"),
                InlineKeyboardButton(text="🔙 Главное меню", callback_data="admin_main_menu")
            ]
        ])
        
        await message.answer(
            "📊 <b>Панель аналитики</b>\n\n"
            "Выберите тип аналитики для просмотра:",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error("Failed to show analytics menu", error=str(e), user_id=message.from_user.id)
        await message.answer("❌ Ошибка при загрузке меню аналитики")


@router.callback_query(F.data == "system_analytics")
async def show_system_analytics(callback: CallbackQuery, state: FSMContext):
    """Show system-wide analytics"""
    try:
        # Get system metrics
        api_client = APIClient()
        metrics = await api_client.get_system_metrics()
        
        if not metrics:
            await callback.answer("Системные метрики недоступны")
            return
        
        # Format system analytics
        analytics_text = format_system_analytics(metrics)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📈 Детальные метрики", callback_data="detailed_metrics"),
                InlineKeyboardButton(text="⚠️ Алерты", callback_data="system_alerts")
            ],
            [
                InlineKeyboardButton(text="🔄 Обновить", callback_data="system_analytics"),
                InlineKeyboardButton(text="🔙 Назад", callback_data="analytics_menu")
            ]
        ])
        
        await callback.message.edit_text(analytics_text, reply_markup=keyboard, parse_mode="HTML")
        
    except Exception as e:
        logger.error("Failed to show system analytics", error=str(e), user_id=callback.from_user.id)
        await callback.answer("Ошибка при получении системной аналитики")


@router.callback_query(F.data == "games_analytics")
async def show_games_analytics(callback: CallbackQuery, state: FSMContext):
    """Show games analytics"""
    try:
        # Get popular games and performance data
        api_client = APIClient()
        popular_games = await api_client.get_popular_games(limit=10)
        performance = await api_client.get_performance_analytics()
        
        if not popular_games and not performance:
            await callback.answer("Аналитика игр недоступна")
            return
        
        # Format games analytics
        analytics_text = format_games_analytics(popular_games, performance)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🎯 По сложности", callback_data="difficulty_analytics"),
                InlineKeyboardButton(text="⏱️ По времени", callback_data="time_analytics")
            ],
            [
                InlineKeyboardButton(text="📊 Детальная статистика", callback_data="detailed_game_stats"),
                InlineKeyboardButton(text="🔙 Назад", callback_data="analytics_menu")
            ]
        ])
        
        await callback.message.edit_text(analytics_text, reply_markup=keyboard, parse_mode="HTML")
        
    except Exception as e:
        logger.error("Failed to show games analytics", error=str(e), user_id=callback.from_user.id)
        await callback.answer("Ошибка при получении аналитики игр")


@router.callback_query(F.data == "players_analytics")
async def show_players_analytics(callback: CallbackQuery, state: FSMContext):
    """Show players analytics"""
    try:
        # Get active players data
        api_client = APIClient()
        active_players = await api_client.get_active_players(period_days=7, limit=20)
        
        if not active_players:
            await callback.answer("Аналитика игроков недоступна")
            return
        
        # Format players analytics
        analytics_text = format_players_analytics(active_players)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📅 За месяц", callback_data="players_monthly"),
                InlineKeyboardButton(text="🏆 Топ игроки", callback_data="top_players")
            ],
            [
                InlineKeyboardButton(text="📊 Сегментация", callback_data="player_segments"),
                InlineKeyboardButton(text="🔙 Назад", callback_data="analytics_menu")
            ]
        ])
        
        await callback.message.edit_text(analytics_text, reply_markup=keyboard, parse_mode="HTML")
        
    except Exception as e:
        logger.error("Failed to show players analytics", error=str(e), user_id=callback.from_user.id)
        await callback.answer("Ошибка при получении аналитики игроков")


@router.callback_query(F.data == "trends_analytics")
async def show_trends_analytics(callback: CallbackQuery, state: FSMContext):
    """Show trends analytics"""
    try:
        # Get daily trends
        api_client = APIClient()
        trends = await api_client.get_daily_trends(days=30)
        
        if not trends:
            await callback.answer("Аналитика трендов недоступна")
            return
        
        # Format trends analytics
        analytics_text = format_trends_analytics(trends)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📈 7 дней", callback_data="trends_weekly"),
                InlineKeyboardButton(text="📊 90 дней", callback_data="trends_quarterly")
            ],
            [
                InlineKeyboardButton(text="🔍 Детальный анализ", callback_data="detailed_trends"),
                InlineKeyboardButton(text="🔙 Назад", callback_data="analytics_menu")
            ]
        ])
        
        await callback.message.edit_text(analytics_text, reply_markup=keyboard, parse_mode="HTML")
        
    except Exception as e:
        logger.error("Failed to show trends analytics", error=str(e), user_id=callback.from_user.id)
        await callback.answer("Ошибка при получении аналитики трендов")


@router.callback_query(F.data == "live_monitoring")
async def show_live_monitoring(callback: CallbackQuery, state: FSMContext):
    """Show live monitoring dashboard"""
    try:
        # Get real-time data
        api_client = APIClient()
        live_data = await api_client.get_live_analytics()
        
        # Format live monitoring data
        monitoring_text = format_live_monitoring(live_data)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Обновить", callback_data="live_monitoring"),
                InlineKeyboardButton(text="⚠️ Алерты", callback_data="live_alerts")
            ],
            [
                InlineKeyboardButton(text="📊 Активные сессии", callback_data="active_sessions"),
                InlineKeyboardButton(text="🔙 Назад", callback_data="analytics_menu")
            ]
        ])
        
        await callback.message.edit_text(monitoring_text, reply_markup=keyboard, parse_mode="HTML")
        
    except Exception as e:
        logger.error("Failed to show live monitoring", error=str(e), user_id=callback.from_user.id)
        await callback.answer("Ошибка при получении live мониторинга")


@router.callback_query(F.data == "export_data")
async def show_export_options(callback: CallbackQuery, state: FSMContext):
    """Show data export options"""
    try:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Результаты игр", callback_data="export_results"),
                InlineKeyboardButton(text="👥 Статистика игроков", callback_data="export_players")
            ],
            [
                InlineKeyboardButton(text="📈 Аналитика", callback_data="export_analytics"),
                InlineKeyboardButton(text="🏆 Лидерборды", callback_data="export_leaderboards")
            ],
            [
                InlineKeyboardButton(text="🔙 Назад", callback_data="analytics_menu")
            ]
        ])
        
        await callback.message.edit_text(
            "📋 <b>Экспорт данных</b>\n\n"
            "Выберите тип данных для экспорта:",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error("Failed to show export options", error=str(e), user_id=callback.from_user.id)
        await callback.answer("Ошибка при загрузке опций экспорта")


@router.callback_query(F.data.startswith("export_"))
async def handle_data_export(callback: CallbackQuery, state: FSMContext):
    """Handle data export requests"""
    try:
        export_type = callback.data.replace("export_", "")
        
        # Show export in progress
        await callback.message.edit_text(
            f"📤 <b>Экспорт данных</b>\n\n"
            f"Подготавливаем экспорт данных типа: {export_type}\n"
            f"Это может занять несколько минут...",
            parse_mode="HTML"
        )
        
        # Request export from analytics service
        api_client = APIClient()
        export_result = await api_client.export_data(export_type, format="json")
        
        if export_result and export_result.get("success"):
            download_url = export_result.get("download_url")
            if download_url:
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="📥 Скачать", url=download_url)],
                    [InlineKeyboardButton(text="🔙 Назад", callback_data="export_data")]
                ])
                
                await callback.message.edit_text(
                    f"✅ <b>Экспорт завершен</b>\n\n"
                    f"Данные готовы для скачивания.\n"
                    f"Тип: {export_type}\n"
                    f"Формат: JSON",
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
            else:
                await callback.message.edit_text(
                    f"✅ <b>Экспорт завершен</b>\n\n"
                    f"Данные подготовлены, но ссылка для скачивания недоступна.\n"
                    f"Обратитесь к администратору системы.",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🔙 Назад", callback_data="export_data")]
                    ]),
                    parse_mode="HTML"
                )
        else:
            await callback.message.edit_text(
                f"❌ <b>Ошибка экспорта</b>\n\n"
                f"Не удалось экспортировать данные типа: {export_type}\n"
                f"Попробуйте позже или обратитесь к администратору.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Назад", callback_data="export_data")]
                ]),
                parse_mode="HTML"
            )
        
    except Exception as e:
        logger.error("Failed to export data", error=str(e), user_id=callback.from_user.id)
        await callback.message.edit_text(
            "❌ <b>Ошибка экспорта</b>\n\n"
            "Произошла ошибка при экспорте данных.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="export_data")]
            ]),
            parse_mode="HTML"
        )


def format_system_analytics(metrics: Dict[str, Any]) -> str:
    """Format system analytics for display"""
    text = f"""
🖥️ <b>Системная аналитика</b>

📊 <b>Общие показатели:</b>
• Всего игр: {metrics.get('total_games', 0):,}
• Всего игроков: {metrics.get('total_players', 0):,}
• Всего сессий: {metrics.get('total_sessions', 0):,}
• Активных сессий: {metrics.get('active_sessions', 0)}

📈 <b>Сегодня:</b>
• Игр: {metrics.get('games_today', 0)}
• Игроков: {metrics.get('players_today', 0)}
• Новых игроков: {metrics.get('new_players_today', 0)}

⏱️ <b>Производительность:</b>
• Средняя длительность сессии: {format_duration(metrics.get('average_session_duration', 0))}
• Пиковое количество игроков: {metrics.get('peak_concurrent_players', 0)}
• Время работы системы: {format_duration(metrics.get('system_uptime', 0))}

🎮 <b>Популярная игра:</b> {metrics.get('most_popular_game', 'Н/Д')}

🕐 <b>Последнее обновление:</b> {format_datetime(metrics.get('last_updated'))}
"""
    return text.strip()


def format_games_analytics(popular_games: Dict[str, Any], performance: Dict[str, Any]) -> str:
    """Format games analytics for display"""
    text = "🎮 <b>Аналитика игр</b>\n\n"
    
    if popular_games and popular_games.get("popular_games"):
        text += "🏆 <b>Популярные игры:</b>\n"
        for i, game in enumerate(popular_games["popular_games"][:5], 1):
            text += f"{i}. {game.get('game_name', 'Неизвестно')} ({game.get('game_type', 'Н/Д')})\n"
            text += f"   📊 {game.get('session_count', 0)} сессий | 👥 {game.get('unique_players', 0)} игроков\n"
            text += f"   💰 Средний счет: {game.get('avg_score', 0):.1f}\n\n"
    
    if performance and performance.get("overall_performance"):
        perf = performance["overall_performance"]
        text += f"""
📈 <b>Общая производительность:</b>
• Средняя точность: {perf.get('avg_accuracy', 0):.1f}%
• Средний счет: {perf.get('avg_score', 0):.1f}
• Среднее время на вопрос: {perf.get('avg_time_per_question', 0):.1f}с
• Всего попыток: {perf.get('total_attempts', 0):,}
• Уникальных игроков: {perf.get('unique_players', 0):,}
"""
    
    return text.strip()


def format_players_analytics(active_players: Dict[str, Any]) -> str:
    """Format players analytics for display"""
    text = f"""
👥 <b>Аналитика игроков</b>

📊 <b>Активные игроки (7 дней):</b>
Всего: {active_players.get('total_players', 0)}

🏆 <b>Топ-10 активных:</b>
"""
    
    players = active_players.get("active_players", [])
    for i, player in enumerate(players[:10], 1):
        text += f"{i}. {player.get('player_name', 'Неизвестно')}\n"
        text += f"   🎮 {player.get('games_played', 0)} игр | 💰 {player.get('total_score', 0):,} очков\n"
        text += f"   🎯 {player.get('avg_accuracy', 0):.1f}% точность\n\n"
    
    return text.strip()


def format_trends_analytics(trends: Dict[str, Any]) -> str:
    """Format trends analytics for display"""
    text = f"""
📈 <b>Аналитика трендов (30 дней)</b>

📊 <b>Общая статистика:</b>
• Дней с данными: {trends.get('total_days', 0)}
• Период: {trends.get('period_days', 30)} дней

"""
    
    daily_trends = trends.get("daily_trends", [])
    if daily_trends:
        # Show last 7 days
        text += "📅 <b>Последние 7 дней:</b>\n"
        for trend in daily_trends[-7:]:
            date = trend.get('date', '')
            if date:
                date_str = datetime.fromisoformat(str(date)).strftime("%d.%m")
            else:
                date_str = "Н/Д"
            
            text += f"{date_str}: {trend.get('games', 0)} игр, {trend.get('unique_players', 0)} игроков\n"
        
        # Calculate averages
        total_games = sum(t.get('games', 0) for t in daily_trends)
        total_players = sum(t.get('unique_players', 0) for t in daily_trends)
        days_count = len(daily_trends)
        
        if days_count > 0:
            text += f"""
📊 <b>Средние показатели:</b>
• Игр в день: {total_games / days_count:.1f}
• Игроков в день: {total_players / days_count:.1f}
"""
    
    return text.strip()


def format_live_monitoring(live_data: Dict[str, Any]) -> str:
    """Format live monitoring data for display"""
    current_time = datetime.utcnow().strftime("%H:%M:%S UTC")
    
    text = f"""
⚡ <b>Live мониторинг</b>

🕐 <b>Время обновления:</b> {current_time}

📊 <b>Текущее состояние:</b>
• Активных сессий: {live_data.get('active_sessions', 0)}
• Игроков онлайн: {live_data.get('players_online', 0)}
• Игр в процессе: {live_data.get('games_in_progress', 0)}

🎮 <b>Активность:</b>
• Игр за последний час: {live_data.get('games_last_hour', 0)}
• Новых игроков за час: {live_data.get('new_players_hour', 0)}
• Завершенных игр за час: {live_data.get('completed_games_hour', 0)}

🖥️ <b>Система:</b>
• Статус: {"🟢 Работает" if live_data.get('system_status') == 'healthy' else "🔴 Проблемы"}
• Время отклика: {live_data.get('response_time', 0):.3f}с
• Использование CPU: {live_data.get('cpu_usage', 0):.1f}%
• Использование памяти: {live_data.get('memory_usage', 0):.1f}%
"""
    
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


def format_datetime(dt_str: str) -> str:
    """Format datetime string for display"""
    if not dt_str:
        return "Н/Д"
    
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt.strftime("%d.%m.%Y %H:%M")
    except:
        return "Н/Д"
