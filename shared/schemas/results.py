"""
Shared schemas for game results and statistics
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field


class GameType(str, Enum):
    """Game type enumeration"""
    QUIZ = "quiz"
    FAMILY_FEUD = "family_feud"
    TRIVIA = "trivia"
    CUSTOM = "custom"


class ResultStatus(str, Enum):
    """Result status enumeration"""
    COMPLETED = "completed"
    ABANDONED = "abandoned"
    DISQUALIFIED = "disqualified"
    IN_PROGRESS = "in_progress"


class AchievementType(str, Enum):
    """Achievement type enumeration"""
    SPEED = "speed"
    ACCURACY = "accuracy"
    PARTICIPATION = "participation"
    STREAK = "streak"
    MILESTONE = "milestone"
    SPECIAL = "special"


class QuestionResult(BaseModel):
    """Individual question result"""
    question_id: str
    question_text: str
    correct_answer: str
    player_answer: Optional[str] = None
    is_correct: bool
    time_taken: float = Field(..., description="Time taken in seconds")
    points_earned: int = 0
    category: Optional[str] = None


class PlayerGameResult(BaseModel):
    """Player's result in a specific game"""
    player_id: str
    player_name: str
    total_score: int
    correct_answers: int
    total_questions: int
    accuracy_percentage: float
    total_time: float = Field(..., description="Total time in seconds")
    average_time_per_question: float
    position: Optional[int] = None
    question_results: List[QuestionResult] = []
    bonus_points: int = 0
    penalty_points: int = 0


class GameResult(BaseModel):
    """Complete game session result"""
    session_id: str
    game_type: GameType
    game_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None  # in seconds
    status: ResultStatus
    total_players: int
    completed_players: int
    player_results: List[PlayerGameResult] = []
    game_config: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}


class PlayerStats(BaseModel):
    """Player's overall statistics"""
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
    total_time_played: float  # in seconds
    average_game_duration: float
    fastest_game: Optional[float] = None
    games_by_type: Dict[GameType, int] = {}
    achievements_earned: List[str] = []
    current_streak: int = 0
    best_streak: int = 0
    last_played: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class Achievement(BaseModel):
    """Achievement definition"""
    id: str
    name: str
    description: str
    type: AchievementType
    icon: Optional[str] = None
    criteria: Dict[str, Any]
    points: int = 0
    is_hidden: bool = False
    created_at: datetime


class PlayerAchievement(BaseModel):
    """Player's earned achievement"""
    player_id: str
    achievement_id: str
    earned_at: datetime
    progress: Dict[str, Any] = {}


class LeaderboardEntry(BaseModel):
    """Leaderboard entry"""
    position: int
    player_id: str
    player_name: str
    score: int
    games_played: int
    accuracy: float
    achievements_count: int


class Leaderboard(BaseModel):
    """Leaderboard data"""
    type: str  # "global", "weekly", "monthly", "game_type"
    period: Optional[str] = None
    game_type: Optional[GameType] = None
    entries: List[LeaderboardEntry]
    total_players: int
    last_updated: datetime


class SessionAnalytics(BaseModel):
    """Analytics for a game session"""
    session_id: str
    game_type: GameType
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    players_joined: int
    players_completed: int
    completion_rate: float
    average_score: float
    highest_score: int
    lowest_score: int
    average_accuracy: float
    average_time_per_question: float
    question_analytics: List[Dict[str, Any]] = []
    difficulty_rating: Optional[float] = None


class GameAnalytics(BaseModel):
    """Analytics for a specific game"""
    game_name: str
    game_type: GameType
    total_sessions: int
    total_players: int
    average_players_per_session: float
    completion_rate: float
    average_score: float
    average_duration: float
    difficulty_rating: float
    popularity_score: float
    last_played: Optional[datetime] = None


class SystemMetrics(BaseModel):
    """System-wide metrics"""
    total_games: int
    total_players: int
    total_sessions: int
    active_sessions: int
    games_today: int
    players_today: int
    average_session_duration: float
    most_popular_game: Optional[str] = None
    peak_concurrent_players: int
    system_uptime: float
    last_updated: datetime


# Request/Response schemas for API

class RecordResultRequest(BaseModel):
    """Request to record game result"""
    session_id: str
    game_result: GameResult


class RecordResultResponse(BaseModel):
    """Response after recording result"""
    success: bool
    message: str
    result_id: Optional[str] = None


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
