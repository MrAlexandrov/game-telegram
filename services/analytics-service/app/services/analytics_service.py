"""
Analytics service for generating and retrieving analytics data
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import structlog
import json

from ..models import GameResult, PlayerGameResult, SessionAnalytics, GameAnalytics, SystemMetrics

logger = structlog.get_logger()


class AnalyticsService:
    """Service for analytics operations"""
    
    def __init__(self, db: AsyncSession, redis_client=None):
        self.db = db
        self.redis = redis_client
    
    async def get_session_analytics(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get analytics for a session"""
        try:
            # Check cache first
            if self.redis:
                cache_key = f"session_analytics:{session_id}"
                cached = await self.redis.get(cache_key)
                if cached:
                    return json.loads(cached)
            
            # Query from database
            stmt = select(SessionAnalytics).where(SessionAnalytics.session_id == session_id)
            result = await self.db.execute(stmt)
            analytics = result.scalar_one_or_none()
            
            if analytics:
                data = {
                    "session_id": analytics.session_id,
                    "game_type": analytics.game_type,
                    "duration": analytics.duration,
                    "players_joined": analytics.players_joined,
                    "players_completed": analytics.players_completed,
                    "completion_rate": analytics.completion_rate,
                    "average_score": analytics.average_score,
                    "highest_score": analytics.highest_score,
                    "lowest_score": analytics.lowest_score,
                    "average_accuracy": analytics.average_accuracy,
                    "difficulty_rating": analytics.difficulty_rating
                }
                
                # Cache the result
                if self.redis:
                    await self.redis.setex(cache_key, 3600, json.dumps(data))
                
                return data
            
            return None
            
        except Exception as e:
            logger.error("Failed to get session analytics", error=str(e))
            raise
    
    async def generate_session_analytics(self, session_id: str) -> Dict[str, Any]:
        """Generate analytics for a session"""
        try:
            # Get game result
            stmt = select(GameResult).where(GameResult.session_id == session_id)
            result = await self.db.execute(stmt)
            game_result = result.scalar_one_or_none()
            
            if not game_result:
                raise ValueError(f"Game result not found for session {session_id}")
            
            # Get player results
            stmt = select(PlayerGameResult).where(PlayerGameResult.game_result_id == game_result.id)
            result = await self.db.execute(stmt)
            player_results = result.scalars().all()
            
            if not player_results:
                raise ValueError(f"No player results found for session {session_id}")
            
            # Calculate analytics
            total_players = len(player_results)
            completed_players = len([p for p in player_results if p.total_questions > 0])
            completion_rate = (completed_players / total_players) * 100 if total_players > 0 else 0
            
            scores = [p.total_score for p in player_results if p.total_score > 0]
            average_score = sum(scores) / len(scores) if scores else 0
            highest_score = max(scores) if scores else 0
            lowest_score = min(scores) if scores else 0
            
            accuracies = [p.accuracy_percentage for p in player_results if p.accuracy_percentage > 0]
            average_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0
            
            # Calculate difficulty rating based on average accuracy
            if average_accuracy >= 80:
                difficulty_rating = 2.0  # Easy
            elif average_accuracy >= 60:
                difficulty_rating = 5.0  # Medium
            else:
                difficulty_rating = 8.0  # Hard
            
            # Create or update session analytics
            stmt = select(SessionAnalytics).where(SessionAnalytics.session_id == session_id)
            result = await self.db.execute(stmt)
            analytics = result.scalar_one_or_none()
            
            if not analytics:
                analytics = SessionAnalytics(
                    session_id=session_id,
                    game_type=game_result.game_type,
                    start_time=game_result.start_time,
                    end_time=game_result.end_time,
                    duration=game_result.duration
                )
                self.db.add(analytics)
            
            # Update analytics data
            analytics.players_joined = total_players
            analytics.players_completed = completed_players
            analytics.completion_rate = completion_rate
            analytics.average_score = average_score
            analytics.highest_score = highest_score
            analytics.lowest_score = lowest_score
            analytics.average_accuracy = average_accuracy
            analytics.difficulty_rating = difficulty_rating
            analytics.updated_at = datetime.utcnow()
            
            await self.db.commit()
            
            # Clear cache
            if self.redis:
                cache_key = f"session_analytics:{session_id}"
                await self.redis.delete(cache_key)
            
            logger.info("Session analytics generated", session_id=session_id)
            
            return {
                "session_id": session_id,
                "analytics": analytics
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error("Failed to generate session analytics", error=str(e))
            raise
    
    async def get_game_analytics(self, game_name: str, game_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get analytics for a specific game"""
        try:
            stmt = select(GameAnalytics).where(GameAnalytics.game_name == game_name)
            if game_type:
                stmt = stmt.where(GameAnalytics.game_type == game_type)
            
            result = await self.db.execute(stmt)
            analytics = result.scalar_one_or_none()
            
            if analytics:
                return {
                    "game_name": analytics.game_name,
                    "game_type": analytics.game_type,
                    "total_sessions": analytics.total_sessions,
                    "total_players": analytics.total_players,
                    "average_players_per_session": analytics.average_players_per_session,
                    "completion_rate": analytics.completion_rate,
                    "average_score": analytics.average_score,
                    "difficulty_rating": analytics.difficulty_rating,
                    "popularity_score": analytics.popularity_score
                }
            
            return None
            
        except Exception as e:
            logger.error("Failed to get game analytics", error=str(e))
            raise
    
    async def get_system_metrics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get system-wide metrics"""
        try:
            # Get latest system metrics
            stmt = (
                select(SystemMetrics)
                .where(SystemMetrics.metric_date.between(start_date, end_date))
                .order_by(SystemMetrics.metric_date.desc())
                .limit(1)
            )
            result = await self.db.execute(stmt)
            latest_metrics = result.scalar_one_or_none()
            
            if latest_metrics:
                return {
                    "total_games": latest_metrics.total_games,
                    "total_players": latest_metrics.total_players,
                    "total_sessions": latest_metrics.total_sessions,
                    "active_sessions": latest_metrics.active_sessions,
                    "games_today": latest_metrics.games_today,
                    "players_today": latest_metrics.players_today,
                    "average_session_duration": latest_metrics.average_session_duration,
                    "most_popular_game": latest_metrics.most_popular_game,
                    "peak_concurrent_players": latest_metrics.peak_concurrent_players,
                    "system_uptime": latest_metrics.system_uptime,
                    "last_updated": latest_metrics.created_at
                }
            
            # If no metrics found, return basic stats from game results
            stmt = select(func.count(GameResult.id)).where(
                GameResult.start_time.between(start_date, end_date)
            )
            result = await self.db.execute(stmt)
            total_games = result.scalar() or 0
            
            return {
                "total_games": total_games,
                "total_players": 0,
                "total_sessions": total_games,
                "active_sessions": 0,
                "games_today": 0,
                "players_today": 0,
                "average_session_duration": 0,
                "most_popular_game": None,
                "peak_concurrent_players": 0,
                "system_uptime": 0,
                "last_updated": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error("Failed to get system metrics", error=str(e))
            raise
