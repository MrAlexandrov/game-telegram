"""
Game Engine Service Configuration
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8001
    DEBUG: bool = False
    
    # Database Configuration
    DATABASE_URL: str = "postgresql://gameuser:gamepass@localhost:5432/gamedb"
    
    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379"
    
    # Game Configuration
    GAME_MODULES_PATH: str = "../../game-modules"
    GAME_PACKS_PATH: str = "../../game-packs"
    
    # File Upload Configuration
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: List[str] = [".json", ".jpg", ".jpeg", ".png", ".gif", ".mp4", ".mp3"]
    
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