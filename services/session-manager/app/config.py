"""
Session Manager Service Configuration
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8002
    DEBUG: bool = False
    
    # Database Configuration
    DATABASE_URL: str = "postgresql://gameuser:gamepass@localhost:5432/gamedb"
    
    # Redis Configuration
    REDIS_URL: str = "redis://redis:6379"
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""
    
    # Session Configuration
    SESSION_EXPIRE_SECONDS: int = 3600  # 1 hour
    SESSION_CODE_LENGTH: int = 6
    MAX_PLAYERS_PER_SESSION: int = 50
    
    # WebSocket Configuration
    WS_HEARTBEAT_INTERVAL: int = 30
    WS_MAX_CONNECTIONS: int = 1000
    
    # Game Configuration
    DEFAULT_QUESTION_TIME_LIMIT: int = 30
    MAX_STRIKES_PER_ROUND: int = 3
    
    # CORS Configuration
    ALLOWED_ORIGINS: List[str] = ["*"]
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 10
    
    # Environment
    ENVIRONMENT: str = "development"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
