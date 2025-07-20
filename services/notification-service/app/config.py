"""
Notification Service Configuration
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Service settings
    service_name: str = "notification-service"
    debug: bool = False
    
    # Redis settings
    redis_url: str = "redis://redis:6379/0"
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    
    # Notification settings
    notification_channels: list = ["telegram", "email", "push"]
    notification_workers: int = 2
    max_retry_attempts: int = 3
    retry_delay: int = 5  # seconds
    
    # Telegram Bot settings (for notifications)
    telegram_bot_token: Optional[str] = None
    
    # Email settings (if needed)
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    
    # Logging
    log_level: str = "INFO"
    
    # CORS settings
    ALLOWED_ORIGINS: list = ["*"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

