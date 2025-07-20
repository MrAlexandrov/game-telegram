"""
Player Bot Service Configuration
"""

from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    """Player Bot settings"""
    
    # Bot Configuration
    BOT_TOKEN: str = "your_player_bot_token_here"
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8001
    DEBUG: bool = False
    
    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379"
    
    # Service URLs
    USER_MANAGER_URL: str = "http://user-manager:8000"
    GAME_ENGINE_URL: str = "http://game-engine:8000"
    SESSION_MANAGER_URL: str = "http://session-manager:8000"
    
    # Webhook Configuration
    WEBHOOK_URL: str = ""  # Leave empty for polling mode
    WEBHOOK_SECRET: str = "your_webhook_secret_here"
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # Game Configuration
    ANSWER_TIMEOUT_SECONDS: int = 30
    MAX_ANSWER_LENGTH: int = 500
    
    # UI Configuration
    RESULTS_PER_PAGE: int = 10
    LEADERBOARD_SIZE: int = 20
    
    # Environment
    ENVIRONMENT: str = "development"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
