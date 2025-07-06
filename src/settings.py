"""
Настройки приложения
"""
import os
import yaml
from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any


class Settings(BaseSettings):
    """Настройки приложения"""
    
    # Основные настройки из .env
    admin_bot_token: str
    player_bot_token: str
    root_id: int
    
    # Режим работы (admin/player/both)
    mode: str = "both"
    
    # Путь к конфигурационному файлу
    config_file: str = "config.yaml"
    
    # Usernames ботов (опционально, для QR-кодов)
    admin_bot_username: Optional[str] = None
    player_bot_username: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._config = self._load_config()
        self._apply_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Загрузка конфигурации из YAML файла"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            else:
                print(f"Конфигурационный файл {self.config_file} не найден, используются значения по умолчанию")
                return {}
        except Exception as e:
            print(f"Ошибка загрузки конфигурации: {e}")
            return {}
    
    def _apply_config(self):
        """Применение настроек из конфигурации"""
        # Настройки игр
        game_config = self._config.get("game", {})
        self.session_code_length = game_config.get("session_code_length", 6)
        self.max_players_per_session = game_config.get("max_players_per_session", 50)
        self.session_timeout_minutes = game_config.get("session_timeout_minutes", 60)
        
        # Пути
        paths_config = self._config.get("paths", {})
        self.game_packs_dir = paths_config.get("game_packs_dir", "./game_packs")
        self.temp_dir = paths_config.get("temp_dir", "./temp")
        self.qr_codes_dir = paths_config.get("qr_codes_dir", "./temp/qr_codes")
        self.logs_dir = paths_config.get("logs_dir", "./logs")
        
        # Логирование
        logging_config = self._config.get("logging", {})
        self.log_level = logging_config.get("level", "INFO")
        self.log_file = logging_config.get("file", "./logs/bot.log")
        self.log_format = logging_config.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        self.log_max_file_size_mb = logging_config.get("max_file_size_mb", 10)
        self.log_backup_count = logging_config.get("backup_count", 5)
        
        # Окружение
        self.environment = self._config.get("environment", "production")
        
        # Настройки очистки
        cleanup_config = self._config.get("cleanup", {})
        self.qr_codes_max_age_hours = cleanup_config.get("qr_codes_max_age_hours", 24)
        self.finished_sessions_max_age_hours = cleanup_config.get("finished_sessions_max_age_hours", 24)
        self.cleanup_interval_minutes = cleanup_config.get("cleanup_interval_minutes", 5)
        
        # Настройки безопасности
        security_config = self._config.get("security", {})
        self.rate_limit_requests_per_minute = security_config.get("rate_limit_requests_per_minute", 30)
        self.max_session_duration_hours = security_config.get("max_session_duration_hours", 4)
        
        # Настройки уведомлений
        notifications_config = self._config.get("notifications", {})
        self.send_game_start_notifications = notifications_config.get("send_game_start_notifications", True)
        self.send_game_end_notifications = notifications_config.get("send_game_end_notifications", True)
        self.send_player_join_notifications = notifications_config.get("send_player_join_notifications", False)
        
        # Настройки игр по умолчанию
        self.game_defaults = self._config.get("game_defaults", {})
    
    def get_game_defaults(self, game_type: str) -> Dict[str, Any]:
        """Получение настроек по умолчанию для типа игры"""
        return self.game_defaults.get(game_type, {})
    
    def is_admin_mode(self) -> bool:
        """Проверка, работает ли в режиме администратора"""
        return self.mode in ["admin", "both"]
    
    def is_player_mode(self) -> bool:
        """Проверка, работает ли в режиме игрока"""
        return self.mode in ["player", "both"]


# Глобальный экземпляр настроек
settings = Settings()


def ensure_directories():
    """Создание необходимых директорий"""
    directories = [
        settings.game_packs_dir,
        settings.temp_dir,
        settings.qr_codes_dir,
        settings.logs_dir,
        f"{settings.game_packs_dir}/quiz",
        f"{settings.game_packs_dir}/hundred_to_one"
    ]
    
    for directory in directories:
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)


def load_settings_for_mode(mode: str) -> Settings:
    """Загрузка настроек для конкретного режима"""
    os.environ["MODE"] = mode
    return Settings()

