"""
Leaderboard API endpoints
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
import structlog

from ..models import PlayerStats, PlayerGameResult, GameResult
from ..schemas import GetLeaderboardRequest, GetLeaderboardResponse
from ..services.leaderboard_service import LeaderboardService
from ..main import get_db, get_redis

logger = structlog.get_logger()
router = APIRouter()


@router.get("/global")
async def get_global_leaderboard(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    redis_client = Depends(get_redis)
):
    """Get global leaderboard"""
    try:
        leaderboard_service = LeaderboardService(db, redis_client)
        leaderboard = await leaderboard_service.get_global_leaderboard(limit, offset)
        
        return leaderboard
        
    except Exception as e:
        logger.error("Failed to get global leaderboard", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/weekly")
async def get_weekly_leaderboard(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """Get weekly leaderboard"""
    try:
        # Get start of current week
        now = datetime.utcnow()
        start_of_week = now - timedelta(days=now.weekday())
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Query weekly stats
        stmt = (
            select(
                PlayerGameResult.player_id,
                PlayerGameResult.player_name,
                func.sum(PlayerGameResult.total_score).label('total_score'),
                func.count(PlayerGameResult.id).label('games_played'),
                func.avg(PlayerGameResult.accuracy_percentage).label('avg_accuracy'),
                func.count(PlayerGameResult.id).label('achievements_count')  # Placeholder
            )
            .join(GameResult)
            .where(GameResult.start_time >= start_of_week)
            .group_by(PlayerGameResult.player_id, PlayerGameResult.player_name)
            .order_by(desc(func.sum(PlayerGameResult.total_score)))
            .limit(limit)
            .offset(offset)
        )
        
        result = await db.execute(stmt)
        players = result.all()
        
        entries = []
        for i, player in enumerate(players, start=offset + 1):
            entries.append({
                "position": i,
                "player_id": player.player_id,
                "player_name": player.player_name,
                "score": player.total_score,
                "games_played": player.games_played,
                "accuracy": float(player.avg_accuracy) if player.avg_accuracy else 0,
                "achievements_count": 0  # Will be implemented with achievements
            })
        
        return {
            "type": "weekly",
            "period": f"Week of {start_of_week.strftime('%Y-%m-%d')}",
            "entries": entries,
            "total_players": len(entries),
            "last_updated": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error("Failed to get weekly leaderboard", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/game/{game_type}")
async def get_game_type_leaderboard(
    game_type: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    period_days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """Get leaderboard for specific game type"""
    try:
        start_date = datetime.utcnow() - timedelta(days=period_days)
        
        # Query game type specific stats
        stmt = (
            select(
                PlayerGameResult.player_id,
                PlayerGameResult.player_name,
                func.sum(PlayerGameResult.total_score).label('total_score'),
                func.count(PlayerGameResult.id).label('games_played'),
                func.avg(PlayerGameResult.accuracy_percentage).label('avg_accuracy'),
                func.max(PlayerGameResult.total_score).label('best_score')
            )
            .join(GameResult)
            .where(
                and_(
                    GameResult.game_type == game_type,
                    GameResult.start_time >= start_date
                )
            )
            .group_by(PlayerGameResult.player_id, PlayerGameResult.player_name)
            .order_by(desc(func.sum(PlayerGameResult.total_score)))
            .limit(limit)
            .offset(offset)
        )
        
        result = await db.execute(stmt)
        players = result.all()
        
        entries = []
        for i, player in enumerate(players, start=offset + 1):
            entries.append({
                "position": i,
                "player_id": player.player_id,
                "player_name": player.player_name,
                "score": player.total_score,
                "games_played": player.games_played,
                "accuracy": float(player.avg_accuracy) if player.avg_accuracy else 0,
                "best_score": player.best_score,
                "achievements_count": 0
            })
        
        return {
            "type": "game_type",
            "game_type": game_type,
            "period": f"Last {period_days} days",
            "entries": entries,
            "total_players": len(entries),
            "last_updated": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error("Failed to get game type leaderboard", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
