"""
Database models for analytics service
"""
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, JSON,
    ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()


class GameResult(Base):
    """Game session results"""
    __tablename__ = "game_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(50), nullable=False, index=True)
    game_type = Column(String(50), nullable=False)
    game_name = Column(String(200), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    duration = Column(Float)  # in seconds
    status = Column(String(20), nullable=False, default="in_progress")
    total_players = Column(Integer, default=0)
    completed_players = Column(Integer, default=0)
    game_config = Column(JSON, default={})
    metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    player_results = relationship("PlayerGameResult", back_populates="game_result", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_game_results_session', 'session_id'),
        Index('idx_game_results_type', 'game_type'),
        Index('idx_game_results_start_time', 'start_time'),
        Index('idx_game_results_status', 'status'),
    )


class PlayerGameResult(Base):
    """Individual player results in a game"""
    __tablename__ = "player_game_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    game_result_id = Column(UUID(as_uuid=True), ForeignKey("game_results.id"), nullable=False)
    player_id = Column(String(100), nullable=False)
    player_name = Column(String(200), nullable=False)
    total_score = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    total_questions = Column(Integer, default=0)
    accuracy_percentage = Column(Float, default=0.0)
    total_time = Column(Float, default=0.0)  # in seconds
    average_time_per_question = Column(Float, default=0.0)
    position = Column(Integer)
    bonus_points = Column(Integer, default=0)
    penalty_points = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    game_result = relationship("GameResult", back_populates="player_results")
    question_results = relationship("QuestionResult", back_populates="player_result", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_player_game_results_player', 'player_id'),
        Index('idx_player_game_results_game', 'game_result_id'),
        Index('idx_player_game_results_score', 'total_score'),
        UniqueConstraint('game_result_id', 'player_id', name='uq_game_player'),
    )


class QuestionResult(Base):
    """Individual question results"""
    __tablename__ = "question_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_result_id = Column(UUID(as_uuid=True), ForeignKey("player_game_results.id"), nullable=False)
    question_id = Column(String(100), nullable=False)
    question_text = Column(Text, nullable=False)
    correct_answer = Column(Text, nullable=False)
    player_answer = Column(Text)
    is_correct = Column(Boolean, default=False)
    time_taken = Column(Float, default=0.0)  # in seconds
    points_earned = Column(Integer, default=0)
    category = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    player_result = relationship("PlayerGameResult", back_populates="question_results")
    
    # Indexes
    __table_args__ = (
        Index('idx_question_results_player', 'player_result_id'),
        Index('idx_question_results_question', 'question_id'),
        Index('idx_question_results_correct', 'is_correct'),
    )


class PlayerStats(Base):
    """Player overall statistics"""
    __tablename__ = "player_stats"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id = Column(String(100), nullable=False, unique=True)
    player_name = Column(String(200), nullable=False)
    total_games = Column(Integer, default=0)
    games_completed = Column(Integer, default=0)
    games_won = Column(Integer, default=0)
    total_score = Column(Integer, default=0)
    average_score = Column(Float, default=0.0)
    best_score = Column(Integer, default=0)
    worst_score = Column(Integer, default=0)
    total_correct_answers = Column(Integer, default=0)
    total_questions_answered = Column(Integer, default=0)
    overall_accuracy = Column(Float, default=0.0)
    total_time_played = Column(Float, default=0.0)  # in seconds
    average_game_duration = Column(Float, default=0.0)
    fastest_game = Column(Float)
    games_by_type = Column(JSON, default={})
    current_streak = Column(Integer, default=0)
    best_streak = Column(Integer, default=0)
    last_played = Column(DateTime)
    rating = Column(Integer, default=1000)  # ELO-style rating
    level = Column(Integer, default=1)
    experience_points = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    achievements = relationship("PlayerAchievement", back_populates="player_stats", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_player_stats_player', 'player_id'),
        Index('idx_player_stats_rating', 'rating'),
        Index('idx_player_stats_level', 'level'),
        Index('idx_player_stats_total_score', 'total_score'),
    )


class Achievement(Base):
    """Achievement definitions"""
    __tablename__ = "achievements"
    
    id = Column(String(100), primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    type = Column(String(50), nullable=False)
    icon = Column(String(200))
    criteria = Column(JSON, nullable=False)
    points = Column(Integer, default=0)
    is_hidden = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    player_achievements = relationship("PlayerAchievement", back_populates="achievement", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_achievements_type', 'type'),
        Index('idx_achievements_active', 'is_active'),
    )


class PlayerAchievement(Base):
    """Player earned achievements"""
    __tablename__ = "player_achievements"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id = Column(String(100), ForeignKey("player_stats.player_id"), nullable=False)
    achievement_id = Column(String(100), ForeignKey("achievements.id"), nullable=False)
    earned_at = Column(DateTime, default=datetime.utcnow)
    progress = Column(JSON, default={})
    
    # Relationships
    player_stats = relationship("PlayerStats", back_populates="achievements")
    achievement = relationship("Achievement", back_populates="player_achievements")
    
    # Indexes
    __table_args__ = (
        Index('idx_player_achievements_player', 'player_id'),
        Index('idx_player_achievements_achievement', 'achievement_id'),
        UniqueConstraint('player_id', 'achievement_id', name='uq_player_achievement'),
    )


class SessionAnalytics(Base):
    """Session analytics data"""
    __tablename__ = "session_analytics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(50), nullable=False, unique=True)
    game_type = Column(String(50), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    duration = Column(Float)
    players_joined = Column(Integer, default=0)
    players_completed = Column(Integer, default=0)
    completion_rate = Column(Float, default=0.0)
    average_score = Column(Float, default=0.0)
    highest_score = Column(Integer, default=0)
    lowest_score = Column(Integer, default=0)
    average_accuracy = Column(Float, default=0.0)
    average_time_per_question = Column(Float, default=0.0)
    question_analytics = Column(JSON, default=[])
    difficulty_rating = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_session_analytics_session', 'session_id'),
        Index('idx_session_analytics_type', 'game_type'),
        Index('idx_session_analytics_start_time', 'start_time'),
    )


class GameAnalytics(Base):
    """Game analytics data"""
    __tablename__ = "game_analytics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    game_name = Column(String(200), nullable=False)
    game_type = Column(String(50), nullable=False)
    total_sessions = Column(Integer, default=0)
    total_players = Column(Integer, default=0)
    unique_players = Column(Integer, default=0)
    average_players_per_session = Column(Float, default=0.0)
    completion_rate = Column(Float, default=0.0)
    average_score = Column(Float, default=0.0)
    average_duration = Column(Float, default=0.0)
    difficulty_rating = Column(Float, default=0.0)
    popularity_score = Column(Float, default=0.0)
    last_played = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_game_analytics_name', 'game_name'),
        Index('idx_game_analytics_type', 'game_type'),
        Index('idx_game_analytics_popularity', 'popularity_score'),
        UniqueConstraint('game_name', 'game_type', name='uq_game_analytics'),
    )


class SystemMetrics(Base):
    """System-wide metrics"""
    __tablename__ = "system_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_date = Column(DateTime, nullable=False)
    total_games = Column(Integer, default=0)
    total_players = Column(Integer, default=0)
    total_sessions = Column(Integer, default=0)
    active_sessions = Column(Integer, default=0)
    games_today = Column(Integer, default=0)
    players_today = Column(Integer, default=0)
    new_players_today = Column(Integer, default=0)
    average_session_duration = Column(Float, default=0.0)
    most_popular_game = Column(String(200))
    peak_concurrent_players = Column(Integer, default=0)
    system_uptime = Column(Float, default=0.0)
    error_rate = Column(Float, default=0.0)
    response_time = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_system_metrics_date', 'metric_date'),
    )


class LeaderboardCache(Base):
    """Cached leaderboard data"""
    __tablename__ = "leaderboard_cache"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    leaderboard_type = Column(String(50), nullable=False)
    game_type = Column(String(50))
    period = Column(String(50))
    data = Column(JSON, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_leaderboard_cache_type', 'leaderboard_type'),
        Index('idx_leaderboard_cache_expires', 'expires_at'),
        UniqueConstraint('leaderboard_type', 'game_type', 'period', name='uq_leaderboard_cache'),
    )
