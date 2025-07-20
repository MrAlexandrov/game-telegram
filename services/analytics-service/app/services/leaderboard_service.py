"""
Leaderboard service for managing player rankings
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
import structlog
import json

from ..models import PlayerStats, PlayerGameResult, GameResult

logger = structlog.get_logger()


class LeaderboardService:
    """Service for leaderboard operations"""
    
    def __init__(self, db: AsyncSession, redis_client=None):
        self.db = db
        self.redis = redis_client
    
    async def get_global_leaderboard(self, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """Get global leaderboard based on total score"""
        try:
            cache_key = f"leaderboard:global:{limit}:{offset}"
            
            # Check cache first
            if self.redis:
                cached = await self.redis.get(cache_key)
                if cached:
                    return json.loads(cached)
            
            # Query from database
            stmt = (
                select(PlayerStats)
                .where(PlayerStats.total_games > 0)
                .order_by(desc(PlayerStats.total_score))
                .limit(limit)
                .offset(offset)
            )
            
            result = await self.db.execute(stmt)
            players = result.scalars().all()
            
            entries = []
            for i, player in enumerate(players, start=offset + 1):
                entries.append({
                    "position": i,
                    "player_id": player.player_id,
                    "player_name": player.player_name,
                    "score": player.total_score,
                    "games_played": player.total_games,
                    "accuracy": player.overall_accuracy,
                    "achievements_count": 0,  # Will be implemented with achievements
                    "level": player.level,
                    "rating": player.rating
                })
            
            leaderboard_data = {
                "type": "global",
                "entries": entries,
                "total_players": len(entries),
                "last_updated": datetime.utcnow()
            }
            
            # Cache the result
            if self.redis:
                await self.redis.setex(cache_key, 600, json.dumps(leaderboard_data, default=str))
            
            return leaderboard_data
            
        except Exception as e:
            logger.error("Failed to get global leaderboard", error=str(e))
            raise
