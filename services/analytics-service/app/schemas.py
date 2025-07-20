"""
Pydantic schemas for analytics service
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator
from enum import Enum

# Import shared schemas
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'shared'))
from schemas.results import (
    GameType, ResultStatus, AchievementType,
    QuestionResult, PlayerGameResult, GameResult,
    PlayerStats, Achievement, PlayerAchievement,
    LeaderboardEntry, Leaderboard, SessionAnalytics,
    GameAnalytics, SystemMetrics
)


# Database model schemas
class GameResultDB(BaseModel):
    """Database model for game results"""
    id: str
    session_id: str
    game_type: GameType
    game_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    status: ResultStatus
    total_players: int
    completed_players: int
    game_config: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PlayerGameResultDB(BaseModel):
    """Database model for player game results"""
    id: str
    game_result_id: str
    player_id: str
    player_name: str
    total_score: int
    correct_answers: int
    total_questions: int
    accuracy_percentage: float
    total_time: float
    average_time_per_question: float
    position: Optional[int] = None
    bonus_points: int = 0
    penalty_points: int = 0
    created_at: datetime
    
    class Config:
        from_attributes = True


class QuestionResultDB(BaseModel):
    """Database model for question results"""
    id: str
    player_result_id: str
    question_id: str
    question_text: str
    correct_answer: str
    player_answer: Optional[str] = None
    is_correct: bool
    time_taken: float
    points_earned: int
    category: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class PlayerStatsDB(BaseModel):
    """Database model for player statistics"""
    id: str
    player_id: str
    player_name: str
    total_games: int
    games_completed: int
    games_won: int
    total_score: int
    average_score: float
    best_score: int
    worst_score: int
    total_correct_answers: int
    total_questions_answered: int
    overall_accuracy: float
    total_time_played: float
    average_game_duration: float
    fastest_game: Optional[float] = None
    games_by_type: Dict[str, int] = {}
    current_streak: int = 0
    best_streak: int = 0
    last_played: Optional[datetime] = None
    rating: int = 1000
    level: int = 1
    experience_points: int = 0
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AchievementDB(BaseModel):
    """Database model for achievements"""
    id: str
    name: str
    description: str
    type: AchievementType
    icon: Optional[str] = None
    criteria: Dict[str, Any]
    points: int = 0
    is_hidden: bool = False
    is_active: bool = True
    created_at: datetime
    
    class Config:
        from_attributes = True


class PlayerAchievementDB(BaseModel):
    """Database model for player achievements"""
    id: str
    player_id: str
    achievement_id: str
    earned_at: datetime
    progress: Dict[str, Any] = {}
    
    class Config:
        from_attributes = True


# API Request/Response schemas
class RecordResultRequest(BaseModel):
    """Request to record game result"""
    session_id: str
    game_result: GameResult
    
    @validator('game_result')
    def validate_game_result(cls, v):
        if not v.player_results:
            raise ValueError("Game result must have at least one player result")
        return v


class RecordResultResponse(BaseModel):
    """Response after recording result"""
    success: bool
    message: str
    result_id: Optional[str] = None
    analytics_generated: bool = False


class GetPlayerStatsRequest(BaseModel):
    """Request to get player statistics"""
    player_id: str
    include_achievements: bool = True
    include_recent_games: bool = True
    recent_games_limit: int = 10


class GetPlayerStatsResponse(BaseModel):
    """Response with player statistics"""
    stats: PlayerStats
    recent_games: List[GameResult] = []
    achievements: List[Achievement] = []


class GetLeaderboardRequest(BaseModel):
    """Request to get leaderboard"""
    type: str = "global"  # "global", "weekly", "monthly", "game_type"
    game_type: Optional[GameType] = None
    limit: int = 50
    offset: int = 0


class GetLeaderboardResponse(BaseModel):
    """Response with leaderboard data"""
    leaderboard: Leaderboard


class GetAnalyticsRequest(BaseModel):
    """Request to get analytics"""
    type: str  # "session", "game", "system"
    session_id: Optional[str] = None
    game_name: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class GetAnalyticsResponse(BaseModel):
    """Response with analytics data"""
    analytics: Dict[str, Any]


# Achievement management schemas
class CreateAchievementRequest(BaseModel):
    """Request to create achievement"""
    id: str
    name: str
    description: str
    type: AchievementType
    icon: Optional[str] = None
    criteria: Dict[str, Any]
    points: int = 0
    is_hidden: bool = False


class UpdateAchievementRequest(BaseModel):
    """Request to update achievement"""
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    criteria: Optional[Dict[str, Any]] = None
    points: Optional[int] = None
    is_hidden: Optional[bool] = None
    is_active: Optional[bool] = None


class AchievementProgressUpdate(BaseModel):
    """Achievement progress update"""
    player_id: str
    achievement_id: str
    progress: Dict[str, Any]
    completed: bool = False


# Export schemas
class ExportFormat(str, Enum):
    """Export format enumeration"""
    JSON = "json"
    CSV = "csv"
    XLSX = "xlsx"


class ExportRequest(BaseModel):
    """Request to export data"""
    type: str  # "results", "stats", "analytics"
    format: ExportFormat
    session_id: Optional[str] = None
    player_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    filters: Dict[str, Any] = {}


class ExportResponse(BaseModel):
    """Response with export data"""
    success: bool
    download_url: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    message: str


# Metrics and monitoring schemas
class MetricsRequest(BaseModel):
    """Request for metrics data"""
    metric_type: str  # "system", "performance", "usage"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    granularity: str = "hour"  # "minute", "hour", "day", "week"


class MetricsResponse(BaseModel):
    """Response with metrics data"""
    metrics: Dict[str, Any]
    period: Dict[str, datetime]
    granularity: str


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    version: str
    database_status: str
    redis_status: Optional[str] = None
    uptime: float


# Batch processing schemas
class BatchRecordRequest(BaseModel):
    """Request to record multiple results"""
    results: List[GameResult]
    
    @validator('results')
    def validate_results(cls, v):
        if not v:
            raise ValueError("At least one result must be provided")
        if len(v) > 100:
            raise ValueError("Maximum 100 results per batch")
        return v


class BatchRecordResponse(BaseModel):
    """Response after batch recording"""
    success: bool
    processed_count: int
    failed_count: int
    errors: List[str] = []
    result_ids: List[str] = []


# Real-time analytics schemas
class LiveSessionUpdate(BaseModel):
    """Live session update"""
    session_id: str
    event_type: str  # "player_joined", "question_answered", "game_completed"
    player_id: Optional[str] = None
    data: Dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class LiveAnalyticsResponse(BaseModel):
    """Live analytics response"""
    session_id: str
    current_players: int
    questions_answered: int
    average_score: float
    completion_rate: float
    last_updated: datetime


# Rating system schemas
class RatingUpdate(BaseModel):
    """Rating system update"""
    player_id: str
    old_rating: int
    new_rating: int
    rating_change: int
    game_result: str  # "win", "loss", "draw"
    opponent_rating: Optional[int] = None


class RatingHistoryRequest(BaseModel):
    """Request for rating history"""
    player_id: str
    limit: int = 50
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class RatingHistoryResponse(BaseModel):
    """Response with rating history"""
    player_id: str
    current_rating: int
    history: List[RatingUpdate]
    peak_rating: int
    lowest_rating: int


# Comparison schemas
class PlayerComparisonRequest(BaseModel):
    """Request to compare players"""
    player_ids: List[str]
    metrics: List[str] = ["total_score", "accuracy", "games_played"]
    
    @validator('player_ids')
    def validate_player_ids(cls, v):
        if len(v) < 2:
            raise ValueError("At least 2 players required for comparison")
        if len(v) > 10:
            raise ValueError("Maximum 10 players can be compared")
        return v


class PlayerComparisonResponse(BaseModel):
    """Response with player comparison"""
    players: List[PlayerStats]
    comparison_metrics: Dict[str, Dict[str, Any]]
    rankings: Dict[str, List[str]]  # metric -> ordered player_ids
