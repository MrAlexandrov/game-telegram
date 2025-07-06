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
    
    # Настройки игр
    session_code_length: int = 6
    max_players_per_session: int = 50
    session_timeout_minutes: int = 60
    
    # Пути
    game_packs_dir: str = "./game_packs"
    temp_dir: str = "./temp"
    qr_codes_dir: str = "./temp/qr_codes"
    logs_dir: str = "./logs"
    
    # Логирование
    log_level: str = "INFO"
    log_file: str = "./logs/bot.log"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_max_file_size_mb: int = 10
    log_backup_count: int = 5
    
    # Окружение
    environment: str = "production"
    
    # Настройки очистки
    qr_codes_max_age_hours: int = 24
    finished_sessions_max_age_hours: int = 24
    cleanup_interval_minutes: int = 5
    
    # Настройки безопасности
    rate_limit_requests_per_minute: int = 30
    max_session_duration_hours: int = 4
    
    # Настройки уведомлений
    send_game_start_notifications: bool = True
    send_game_end_notifications: bool = True
    send_player_join_notifications: bool = False
    
    # Настройки игр по умолчанию
    game_defaults: Dict[str, Any] = {}
    
    model_config = {"env_file": ".env", "case_sensitive": False}
    
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
        if "session_code_length" in game_config:
            self.session_code_length = game_config["session_code_length"]
        if "max_players_per_session" in game_config:
            self.max_players_per_session = game_config["max_players_per_session"]
        if "session_timeout_minutes" in game_config:
            self.session_timeout_minutes = game_config["session_timeout_minutes"]
        
        # Пути
        paths_config = self._config.get("paths", {})
        if "game_packs_dir" in paths_config:
            self.game_packs_dir = paths_config["game_packs_dir"]
        if "temp_dir" in paths_config:
            self.temp_dir = paths_config["temp_dir"]
        if "qr_codes_dir" in paths_config:
            self.qr_codes_dir = paths_config["qr_codes_dir"]
        if "logs_dir" in paths_config:
            self.logs_dir = paths_config["logs_dir"]
        
        # Логирование
        logging_config = self._config.get("logging", {})
        if "level" in logging_config:
            self.log_level = logging_config["level"]
        if "file" in logging_config:
            self.log_file = logging_config["file"]
        if "format" in logging_config:
            self.log_format = logging_config["format"]
        if "max_file_size_mb" in logging_config:
            self.log_max_file_size_mb = logging_config["max_file_size_mb"]
        if "backup_count" in logging_config:
            self.log_backup_count = logging_config["backup_count"]
        
        # Окружение
        if "environment" in self._config:
            self.environment = self._config["environment"]
        
        # Настройки очистки
        cleanup_config = self._config.get("cleanup", {})
        if "qr_codes_max_age_hours" in cleanup_config:
            self.qr_codes_max_age_hours = cleanup_config["qr_codes_max_age_hours"]
        if "finished_sessions_max_age_hours" in cleanup_config:
            self.finished_sessions_max_age_hours = cleanup_config["finished_sessions_max_age_hours"]
        if "cleanup_interval_minutes" in cleanup_config:
            self.cleanup_interval_minutes = cleanup_config["cleanup_interval_minutes"]
        
        # Настройки безопасности
        security_config = self._config.get("security", {})
        if "rate_limit_requests_per_minute" in security_config:
            self.rate_limit_requests_per_minute = security_config["rate_limit_requests_per_minute"]
        if "max_session_duration_hours" in security_config:
            self.max_session_duration_hours = security_config["max_session_duration_hours"]
        
        # Настройки уведомлений
        notifications_config = self._config.get("notifications", {})
        if "send_game_start_notifications" in notifications_config:
            self.send_game_start_notifications = notifications_config["send_game_start_notifications"]
        if "send_game_end_notifications" in notifications_config:
            self.send_game_end_notifications = notifications_config["send_game_end_notifications"]
        if "send_player_join_notifications" in notifications_config:
            self.send_player_join_notifications = notifications_config["send_player_join_notifications"]
        
        # Настройки игр по умолчанию
        if "game_defaults" in self._config:
            self.game_defaults = self._config["game_defaults"]
    
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
        # f"{settings.game_packs_dir}/hundred_to_one"
    ]
    
    for directory in directories:
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)


def load_settings_for_mode(mode: str) -> Settings:
    """Загрузка настроек для конкретного режима"""
    os.environ["MODE"] = mode
    return Settings()



