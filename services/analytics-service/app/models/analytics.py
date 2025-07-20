"""
Analytics Service - Analytics Models
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base


class GameResult(Base):
    """Game result model"""
    __tablename__ = "game_results"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, nullable=False, index=True)
    game_id = Column(Integer, nullable=False)
    total_players = Column(Integer, default=0)
    total_questions = Column(Integer, default=0)
    average_score = Column(Float, default=0.0)
    completion_rate = Column(Float, default=0.0)
    duration_minutes = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PlayerGameResult(Base):
    """Player game result model"""
    __tablename__ = "player_game_results"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    game_id = Column(Integer, nullable=False)
    final_score = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    total_answers = Column(Integer, default=0)
    accuracy_rate = Column(Float, default=0.0)
    average_response_time = Column(Float, default=0.0)
    rank = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class QuestionResult(Base):
    """Question result model"""
    __tablename__ = "question_results"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, nullable=False, index=True)
    question_id = Column(Integer, nullable=False)
    total_responses = Column(Integer, default=0)
    correct_responses = Column(Integer, default=0)
    average_response_time = Column(Float, default=0.0)
    difficulty_rating = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PlayerStats(Base):
    """Player statistics model"""
    __tablename__ = "player_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, nullable=False, index=True)
    total_games = Column(Integer, default=0)
    total_wins = Column(Integer, default=0)
    total_score = Column(Integer, default=0)
    average_score = Column(Float, default=0.0)
    best_score = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)
    favorite_game_type = Column(String(50), nullable=True)
    total_playtime_minutes = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Achievement(Base):
    """Achievement model"""
    __tablename__ = "achievements"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(255), nullable=True)
    criteria = Column(JSON, nullable=False)
    points = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PlayerAchievement(Base):
    """Player achievement model"""
    __tablename__ = "player_achievements"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    achievement_id = Column(Integer, ForeignKey("achievements.id"), nullable=False)
    earned_at = Column(DateTime(timezone=True), server_default=func.now())
    session_id = Column(Integer, nullable=True)


class SessionAnalytics(Base):
    """Session analytics model"""
    __tablename__ = "session_analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, unique=True, nullable=False, index=True)
    engagement_score = Column(Float, default=0.0)
    dropout_rate = Column(Float, default=0.0)
    peak_players = Column(Integer, default=0)
    average_session_time = Column(Float, default=0.0)
    question_skip_rate = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class GameAnalytics(Base):
    """Game analytics model"""
    __tablename__ = "game_analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, nullable=False, index=True)
    total_sessions = Column(Integer, default=0)
    total_players = Column(Integer, default=0)
    average_rating = Column(Float, default=0.0)
    difficulty_rating = Column(Float, default=0.0)
    popularity_score = Column(Float, default=0.0)
    last_played = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class SystemMetrics(Base):
    """System metrics model"""
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_type = Column(String(50), nullable=False)  # counter, gauge, histogram
    tags = Column(JSON, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())


class LeaderboardCache(Base):
    """Leaderboard cache model"""
    __tablename__ = "leaderboard_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    leaderboard_type = Column(String(50), nullable=False)  # daily, weekly, monthly, all_time
    game_type = Column(String(50), nullable=True)
    data = Column(JSON, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())