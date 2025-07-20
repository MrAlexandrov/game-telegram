"""
Configuration for Analytics Service
"""
import os
from functools import lru_cache
from typing import Optional
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application settings"""
    
    # Application settings
    app_name: str = "Game Analytics Service"
    version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8004, env="PORT")
    
    # Database settings
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:password@localhost:5432/game_analytics",
        env="DATABASE_URL"
    )
    
    # Redis settings
    redis_url: Optional[str] = Field(
        default="redis://localhost:6379/2",
        env="REDIS_URL"
    )
    
    # Cache settings
    cache_ttl: int = Field(default=300, env="CACHE_TTL")  # 5 minutes
    leaderboard_cache_ttl: int = Field(default=600, env="LEADERBOARD_CACHE_TTL")  # 10 minutes
    
    # Analytics settings
    batch_size: int = Field(default=100, env="BATCH_SIZE")
    max_export_records: int = Field(default=10000, env="MAX_EXPORT_RECORDS")
    
    # Achievement settings
    achievement_check_interval: int = Field(default=60, env="ACHIEVEMENT_CHECK_INTERVAL")  # seconds
    
    # Rating system settings
    initial_rating: int = Field(default=1000, env="INITIAL_RATING")
    k_factor: int = Field(default=32, env="K_FACTOR")  # ELO K-factor
    
    # Metrics settings
    metrics_retention_days: int = Field(default=90, env="METRICS_RETENTION_DAYS")
    
    # External service URLs
    session_manager_url: str = Field(
        default="http://session-manager:8002",
        env="SESSION_MANAGER_URL"
    )
    game_engine_url: str = Field(
        default="http://game-engine:8001",
        env="GAME_ENGINE_URL"
    )
    user_manager_url: str = Field(
        default="http://user-manager:8003",
        env="USER_MANAGER_URL"
    )
    
    # Security settings
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        env="SECRET_KEY"
    )
    
    # Logging settings
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    
    # Performance settings
    max_connections: int = Field(default=20, env="MAX_CONNECTIONS")
    connection_timeout: int = Field(default=30, env="CONNECTION_TIMEOUT")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
