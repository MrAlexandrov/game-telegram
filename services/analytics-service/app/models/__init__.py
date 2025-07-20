"""
Analytics Service - Models Package
"""

# Import database components
from .database import Base, engine, AsyncSessionLocal, get_db

# Import models using relative imports to avoid circular imports
from .analytics import (
    GameResult,
    PlayerGameResult,
    QuestionResult,
    PlayerStats,
    Achievement,
    PlayerAchievement,
    SessionAnalytics,
    GameAnalytics,
    SystemMetrics,
    LeaderboardCache
)

__all__ = [
    "Base", "engine", "AsyncSessionLocal", "get_db",
    "GameResult",
    "PlayerGameResult",
    "QuestionResult",
    "PlayerStats",
    "Achievement",
    "PlayerAchievement",
    "SessionAnalytics",
    "GameAnalytics",
    "SystemMetrics",
    "LeaderboardCache"
]

