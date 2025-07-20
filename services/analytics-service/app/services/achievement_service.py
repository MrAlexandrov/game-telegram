"""
Achievement service for managing player achievements
"""
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from ..models import Achievement, PlayerAchievement, PlayerStats

logger = structlog.get_logger()


class AchievementService:
    """Service for achievement operations"""
    
    def __init__(self, db: AsyncSession, redis_client=None):
        self.db = db
        self.redis = redis_client
    
    async def check_achievements(self, player_id: str) -> List[str]:
        """Check and award achievements for a player"""
        try:
            # Get player stats
            stmt = select(PlayerStats).where(PlayerStats.player_id == player_id)
            result = await self.db.execute(stmt)
            player_stats = result.scalar_one_or_none()
            
            if not player_stats:
                return []
            
            # Get all active achievements
            stmt = select(Achievement).where(Achievement.is_active == True)
            result = await self.db.execute(stmt)
            achievements = result.scalars().all()
            
            # Get player's existing achievements
            stmt = select(PlayerAchievement).where(PlayerAchievement.player_id == player_id)
            result = await self.db.execute(stmt)
            existing_achievements = {pa.achievement_id for pa in result.scalars().all()}
            
            new_achievements = []
            
            for achievement in achievements:
                if achievement.id in existing_achievements:
                    continue
                
                # Check achievement criteria
                if self._check_achievement_criteria(achievement, player_stats):
                    # Award achievement
                    player_achievement = PlayerAchievement(
                        player_id=player_id,
                        achievement_id=achievement.id,
                        earned_at=datetime.utcnow()
                    )
                    self.db.add(player_achievement)
                    new_achievements.append(achievement.id)
                    
                    logger.info(
                        "Achievement earned",
                        player_id=player_id,
                        achievement_id=achievement.id
                    )
            
            if new_achievements:
                await self.db.commit()
            
            return new_achievements
            
        except Exception as e:
            await self.db.rollback()
            logger.error("Failed to check achievements", error=str(e))
            raise
    
    def _check_achievement_criteria(self, achievement: Achievement, player_stats: PlayerStats) -> bool:
        """Check if player meets achievement criteria"""
        criteria = achievement.criteria
        
        # Example criteria checks
        if achievement.type == "milestone":
            if "games_played" in criteria:
                return player_stats.total_games >= criteria["games_played"]
            if "total_score" in criteria:
                return player_stats.total_score >= criteria["total_score"]
        
        elif achievement.type == "accuracy":
            if "accuracy_threshold" in criteria:
                return player_stats.overall_accuracy >= criteria["accuracy_threshold"]
        
        elif achievement.type == "streak":
            if "win_streak" in criteria:
                return player_stats.current_streak >= criteria["win_streak"]
        
        return False
