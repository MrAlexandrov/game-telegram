"""
Admin Bot Service Configuration
"""

from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    """Admin Bot settings"""
    
    # Bot Configuration
    BOT_TOKEN: str = "your_admin_bot_token_here"
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
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
    
    # File Upload Configuration
    MAX_FILE_SIZE: int = 10485760  # 10MB
    ALLOWED_FILE_TYPES: list = [".json", ".jpg", ".jpeg", ".png", ".gif", ".mp4", ".mp3"]
    
    # Game Configuration
    MAX_PLAYERS_PER_SESSION: int = 50
    SESSION_TIMEOUT_MINUTES: int = 60
    
    # Environment
    ENVIRONMENT: str = "development"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()