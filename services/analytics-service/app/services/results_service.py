"""
Results service for handling game results and player statistics
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
import structlog
import json

from ..models import GameResult, PlayerGameResult, QuestionResult, PlayerStats
from ..schemas import GameResult as GameResultSchema, PlayerGameResult as PlayerGameResultSchema

logger = structlog.get_logger()


class ResultsService:
    """Service for handling game results"""
    
    def __init__(self, db: AsyncSession, redis_client=None):
        self.db = db
        self.redis = redis_client
    
    async def record_game_result(self, game_result: GameResultSchema) -> str:
        """Record a complete game result"""
        try:
            # Create game result record
            db_game_result = GameResult(
                session_id=game_result.session_id,
                game_type=game_result.game_type,
                game_name=game_result.game_name,
                start_time=game_result.start_time,
                end_time=game_result.end_time,
                duration=game_result.duration,
                status=game_result.status,
                total_players=game_result.total_players,
                completed_players=game_result.completed_players,
                game_config=game_result.game_config,
                metadata=game_result.metadata
            )
            
            self.db.add(db_game_result)
            await self.db.flush()  # Get the ID
            
            # Record player results
            for player_result in game_result.player_results:
                db_player_result = PlayerGameResult(
                    game_result_id=db_game_result.id,
                    player_id=player_result.player_id,
                    player_name=player_result.player_name,
                    total_score=player_result.total_score,
                    correct_answers=player_result.correct_answers,
                    total_questions=player_result.total_questions,
                    accuracy_percentage=player_result.accuracy_percentage,
                    total_time=player_result.total_time,
                    average_time_per_question=player_result.average_time_per_question,
                    position=player_result.position,
                    bonus_points=player_result.bonus_points,
                    penalty_points=player_result.penalty_points
                )
                
                self.db.add(db_player_result)
                await self.db.flush()
                
                # Record question results
                for question_result in player_result.question_results:
                    db_question_result = QuestionResult(
                        player_result_id=db_player_result.id,
                        question_id=question_result.question_id,
                        question_text=question_result.question_text,
                        correct_answer=question_result.correct_answer,
                        player_answer=question_result.player_answer,
                        is_correct=question_result.is_correct,
                        time_taken=question_result.time_taken,
                        points_earned=question_result.points_earned,
                        category=question_result.category
                    )
                    
                    self.db.add(db_question_result)
            
            await self.db.commit()
            
            logger.info(
                "Game result recorded",
                session_id=game_result.session_id,
                result_id=str(db_game_result.id),
                players=len(game_result.player_results)
            )
            
            return str(db_game_result.id)
            
        except Exception as e:
            await self.db.rollback()
            logger.error("Failed to record game result", error=str(e))
            raise
    
    async def update_player_stats(self, player_results: List[PlayerGameResultSchema]):
        """Update player statistics based on game results"""
        try:
            for player_result in player_results:
                # Get or create player stats
                stmt = select(PlayerStats).where(PlayerStats.player_id == player_result.player_id)
                result = await self.db.execute(stmt)
                player_stats = result.scalar_one_or_none()
                
                if not player_stats:
                    # Create new player stats
                    player_stats = PlayerStats(
                        player_id=player_result.player_id,
                        player_name=player_result.player_name,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    self.db.add(player_stats)
                    await self.db.flush()
                
                # Update statistics
                player_stats.total_games += 1
                player_stats.games_completed += 1
                player_stats.total_score += player_result.total_score
                player_stats.total_correct_answers += player_result.correct_answers
                player_stats.total_questions_answered += player_result.total_questions
                player_stats.total_time_played += player_result.total_time
                
                # Update best/worst scores
                if player_result.total_score > player_stats.best_score:
                    player_stats.best_score = player_result.total_score
                
                if player_stats.worst_score == 0 or player_result.total_score < player_stats.worst_score:
                    player_stats.worst_score = player_result.total_score
                
                # Calculate averages
                if player_stats.total_games > 0:
                    player_stats.average_score = player_stats.total_score / player_stats.total_games
                    player_stats.average_game_duration = player_stats.total_time_played / player_stats.total_games
                
                if player_stats.total_questions_answered > 0:
                    player_stats.overall_accuracy = (player_stats.total_correct_answers / player_stats.total_questions_answered) * 100
                
                # Update fastest game
                if not player_stats.fastest_game or player_result.total_time < player_stats.fastest_game:
                    player_stats.fastest_game = player_result.total_time
                
                # Update win streak (assuming position 1 is a win)
                if player_result.position == 1:
                    player_stats.games_won += 1
                    player_stats.current_streak += 1
                    if player_stats.current_streak > player_stats.best_streak:
                        player_stats.best_streak = player_stats.current_streak
                else:
                    player_stats.current_streak = 0
                
                # Update last played
                player_stats.last_played = datetime.utcnow()
                player_stats.updated_at = datetime.utcnow()
                
                # Update experience points (simple formula)
                base_xp = player_result.total_score // 10
                accuracy_bonus = int(player_result.accuracy_percentage)
                time_bonus = max(0, 100 - int(player_result.average_time_per_question))
                player_stats.experience_points += base_xp + accuracy_bonus + time_bonus
                
                # Update level based on XP (simple leveling system)
                new_level = min(100, max(1, player_stats.experience_points // 1000 + 1))
                player_stats.level = new_level
            
            await self.db.commit()
            
            logger.info("Player stats updated", players=len(player_results))
            
        except Exception as e:
            await self.db.rollback()
            logger.error("Failed to update player stats", error=str(e))
            raise
    
    async def generate_session_analytics(self, session_id: str):
        """Generate analytics for a session"""
        try:
            # This would be implemented by the analytics service
            # For now, just log that it was called
            logger.info("Session analytics generation requested", session_id=session_id)
            
            # Cache session analytics if Redis is available
            if self.redis:
                cache_key = f"session_analytics:{session_id}"
                analytics_data = {
                    "session_id": session_id,
                    "generated_at": datetime.utcnow().isoformat(),
                    "status": "generated"
                }
                await self.redis.setex(cache_key, 3600, json.dumps(analytics_data))
            
        except Exception as e:
            logger.error("Failed to generate session analytics", error=str(e))
    
    async def check_achievements(self, player_results: List[PlayerGameResultSchema]):
        """Check and award achievements for players"""
        try:
            # This would be implemented by the achievement service
            # For now, just log that it was called
            logger.info("Achievement check requested", players=len(player_results))
            
            # Simple achievement examples:
            for player_result in player_results:
                achievements_earned = []
                
                # Perfect score achievement
                if player_result.accuracy_percentage == 100:
                    achievements_earned.append("perfect_score")
                
                # Speed demon achievement
                if player_result.average_time_per_question < 5:
                    achievements_earned.append("speed_demon")
                
                # High scorer achievement
                if player_result.total_score > 1000:
                    achievements_earned.append("high_scorer")
                
                if achievements_earned:
                    logger.info(
                        "Achievements earned",
                        player_id=player_result.player_id,
                        achievements=achievements_earned
                    )
            
        except Exception as e:
            logger.error("Failed to check achievements", error=str(e))
    
    async def get_player_statistics(self, player_id: str) -> Optional[PlayerStats]:
        """Get player statistics"""
        try:
            stmt = select(PlayerStats).where(PlayerStats.player_id == player_id)
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error("Failed to get player statistics", error=str(e))
            raise
    
    async def get_session_results(self, session_id: str) -> Optional[GameResult]:
        """Get complete session results"""
        try:
            stmt = select(GameResult).where(GameResult.session_id == session_id)
            result = await self.db.execute(stmt)
            game_result = result.scalar_one_or_none()
            
            if game_result:
                # Load player results
                stmt = select(PlayerGameResult).where(
                    PlayerGameResult.game_result_id == game_result.id
                ).order_by(PlayerGameResult.position.asc())
                result = await self.db.execute(stmt)
                game_result.player_results = result.scalars().all()
                
                # Load question results for each player
                for player_result in game_result.player_results:
                    stmt = select(QuestionResult).where(
                        QuestionResult.player_result_id == player_result.id
                    )
                    result = await self.db.execute(stmt)
                    player_result.question_results = result.scalars().all()
            
            return game_result
            
        except Exception as e:
            logger.error("Failed to get session results", error=str(e))
            raise
