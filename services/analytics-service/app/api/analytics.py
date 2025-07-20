"""
Analytics API endpoints
"""
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
import structlog

from ..models import GameResult, PlayerGameResult, SessionAnalytics, GameAnalytics, SystemMetrics
from ..schemas import GetAnalyticsRequest, GetAnalyticsResponse
from ..services.analytics_service import AnalyticsService
from ..main import get_db, get_redis

logger = structlog.get_logger()
router = APIRouter()


@router.get("/session/{session_id}")
async def get_session_analytics(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    redis_client = Depends(get_redis)
):
    """Get analytics for a specific session"""
    try:
        analytics_service = AnalyticsService(db, redis_client)
        analytics = await analytics_service.get_session_analytics(session_id)
        
        if not analytics:
            raise HTTPException(status_code=404, detail="Session analytics not found")
        
        return analytics
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get session analytics", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/game/{game_name}")
async def get_game_analytics(
    game_name: str,
    game_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    redis_client = Depends(get_redis)
):
    """Get analytics for a specific game"""
    try:
        analytics_service = AnalyticsService(db, redis_client)
        analytics = await analytics_service.get_game_analytics(game_name, game_type)
        
        if not analytics:
            raise HTTPException(status_code=404, detail="Game analytics not found")
        
        return analytics
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get game analytics", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system")
async def get_system_metrics(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
    redis_client = Depends(get_redis)
):
    """Get system-wide metrics"""
    try:
        analytics_service = AnalyticsService(db, redis_client)
        
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=7)
        if not end_date:
            end_date = datetime.utcnow()
        
        metrics = await analytics_service.get_system_metrics(start_date, end_date)
        
        return {
            "metrics": metrics,
            "period": {
                "start": start_date,
                "end": end_date
            }
        }
        
    except Exception as e:
        logger.error("Failed to get system metrics", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/games/popular")
async def get_popular_games(
    limit: int = Query(10, ge=1, le=50),
    period_days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """Get most popular games"""
    try:
        start_date = datetime.utcnow() - timedelta(days=period_days)
        
        # Query popular games by session count
        stmt = (
            select(
                GameResult.game_name,
                GameResult.game_type,
                func.count(GameResult.id).label('session_count'),
                func.count(func.distinct(PlayerGameResult.player_id)).label('unique_players'),
                func.avg(PlayerGameResult.total_score).label('avg_score'),
                func.avg(GameResult.duration).label('avg_duration')
            )
            .join(PlayerGameResult)
            .where(GameResult.start_time >= start_date)
            .group_by(GameResult.game_name, GameResult.game_type)
            .order_by(func.count(GameResult.id).desc())
            .limit(limit)
        )
        
        result = await db.execute(stmt)
        games = result.all()
        
        return {
            "popular_games": [
                {
                    "game_name": game.game_name,
                    "game_type": game.game_type,
                    "session_count": game.session_count,
                    "unique_players": game.unique_players,
                    "avg_score": float(game.avg_score) if game.avg_score else 0,
                    "avg_duration": float(game.avg_duration) if game.avg_duration else 0
                }
                for game in games
            ],
            "period_days": period_days,
            "total_games": len(games)
        }
        
    except Exception as e:
        logger.error("Failed to get popular games", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/players/active")
async def get_active_players(
    period_days: int = Query(7, ge=1, le=365),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    """Get most active players"""
    try:
        start_date = datetime.utcnow() - timedelta(days=period_days)
        
        # Query active players
        stmt = (
            select(
                PlayerGameResult.player_id,
                PlayerGameResult.player_name,
                func.count(PlayerGameResult.id).label('games_played'),
                func.sum(PlayerGameResult.total_score).label('total_score'),
                func.avg(PlayerGameResult.accuracy_percentage).label('avg_accuracy'),
                func.max(GameResult.start_time).label('last_played')
            )
            .join(GameResult)
            .where(GameResult.start_time >= start_date)
            .group_by(PlayerGameResult.player_id, PlayerGameResult.player_name)
            .order_by(func.count(PlayerGameResult.id).desc())
            .limit(limit)
        )
        
        result = await db.execute(stmt)
        players = result.all()
        
        return {
            "active_players": [
                {
                    "player_id": player.player_id,
                    "player_name": player.player_name,
                    "games_played": player.games_played,
                    "total_score": player.total_score,
                    "avg_accuracy": float(player.avg_accuracy) if player.avg_accuracy else 0,
                    "last_played": player.last_played
                }
                for player in players
            ],
            "period_days": period_days,
            "total_players": len(players)
        }
        
    except Exception as e:
        logger.error("Failed to get active players", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trends/daily")
async def get_daily_trends(
    days: int = Query(30, ge=1, le=90),
    db: AsyncSession = Depends(get_db)
):
    """Get daily activity trends"""
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Query daily statistics
        stmt = (
            select(
                func.date(GameResult.start_time).label('date'),
                func.count(GameResult.id).label('games'),
                func.count(func.distinct(PlayerGameResult.player_id)).label('unique_players'),
                func.avg(PlayerGameResult.total_score).label('avg_score'),
                func.avg(GameResult.duration).label('avg_duration')
            )
            .join(PlayerGameResult)
            .where(GameResult.start_time >= start_date)
            .group_by(func.date(GameResult.start_time))
            .order_by(func.date(GameResult.start_time))
        )
        
        result = await db.execute(stmt)
        trends = result.all()
        
        return {
            "daily_trends": [
                {
                    "date": trend.date,
                    "games": trend.games,
                    "unique_players": trend.unique_players,
                    "avg_score": float(trend.avg_score) if trend.avg_score else 0,
                    "avg_duration": float(trend.avg_duration) if trend.avg_duration else 0
                }
                for trend in trends
            ],
            "period_days": days,
            "total_days": len(trends)
        }
        
    except Exception as e:
        logger.error("Failed to get daily trends", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance")
async def get_performance_analytics(
    game_type: Optional[str] = Query(None),
    period_days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """Get performance analytics"""
    try:
        start_date = datetime.utcnow() - timedelta(days=period_days)
        
        # Base query
        stmt = (
            select(
                func.avg(PlayerGameResult.accuracy_percentage).label('avg_accuracy'),
                func.avg(PlayerGameResult.total_score).label('avg_score'),
                func.avg(PlayerGameResult.average_time_per_question).label('avg_time_per_question'),
                func.count(PlayerGameResult.id).label('total_attempts'),
                func.count(func.distinct(PlayerGameResult.player_id)).label('unique_players')
            )
            .join(GameResult)
            .where(GameResult.start_time >= start_date)
        )
        
        if game_type:
            stmt = stmt.where(GameResult.game_type == game_type)
        
        result = await db.execute(stmt)
        performance = result.first()
        
        # Get difficulty distribution
        difficulty_stmt = (
            select(
                GameResult.game_name,
                func.avg(PlayerGameResult.accuracy_percentage).label('avg_accuracy'),
                func.count(PlayerGameResult.id).label('attempts')
            )
            .join(PlayerGameResult)
            .where(GameResult.start_time >= start_date)
            .group_by(GameResult.game_name)
            .having(func.count(PlayerGameResult.id) >= 5)  # Minimum attempts for reliable data
        )
        
        if game_type:
            difficulty_stmt = difficulty_stmt.where(GameResult.game_type == game_type)
        
        result = await db.execute(difficulty_stmt)
        difficulty_data = result.all()
        
        return {
            "overall_performance": {
                "avg_accuracy": float(performance.avg_accuracy) if performance.avg_accuracy else 0,
                "avg_score": float(performance.avg_score) if performance.avg_score else 0,
                "avg_time_per_question": float(performance.avg_time_per_question) if performance.avg_time_per_question else 0,
                "total_attempts": performance.total_attempts,
                "unique_players": performance.unique_players
            },
            "game_difficulty": [
                {
                    "game_name": game.game_name,
                    "avg_accuracy": float(game.avg_accuracy),
                    "attempts": game.attempts,
                    "difficulty_level": "easy" if game.avg_accuracy > 80 else "medium" if game.avg_accuracy > 60 else "hard"
                }
                for game in difficulty_data
            ],
            "period_days": period_days,
            "game_type": game_type
        }
        
    except Exception as e:
        logger.error("Failed to get performance analytics", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate/{session_id}")
async def generate_session_analytics(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    redis_client = Depends(get_redis)
):
    """Manually trigger analytics generation for a session"""
    try:
        analytics_service = AnalyticsService(db, redis_client)
        analytics = await analytics_service.generate_session_analytics(session_id)
        
        logger.info("Session analytics generated", session_id=session_id)
        
        return {
            "message": "Analytics generated successfully",
            "session_id": session_id,
            "analytics": analytics
        }
        
    except Exception as e:
        logger.error("Failed to generate session analytics", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
