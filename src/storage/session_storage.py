"""
Хранилище игровых сессий
"""
import json
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

from src.models.session import Session, SessionInfo, ActiveSession
from src.models.enums import SessionStatus
from src.settings import settings


class SessionStorage:
    """Хранилище игровых сессий в памяти с возможностью персистентности"""
    
    def __init__(self):
        self.sessions: Dict[str, Session] = {}
        self.sessions_by_code: Dict[str, str] = {}  # code -> session_id
        self.logger = logging.getLogger(__name__)
        
        # Путь для сохранения активных сессий
        self.sessions_file = os.path.join(settings.temp_dir, "active_sessions.json")
        
        # Загружаем сохраненные сессии при инициализации
        self._load_sessions()
    
    async def create_session(self, session: Session) -> str:
        """
        Создание новой сессии
        
        Args:
            session: Объект сессии
            
        Returns:
            ID созданной сессии
        """
        try:
            # Проверяем уникальность кода
            if session.code in self.sessions_by_code:
                raise ValueError(f"Сессия с кодом {session.code} уже существует")
            
            # Сохраняем сессию
            self.sessions[session.id] = session
            self.sessions_by_code[session.code] = session.id
            
            # Сохраняем на диск
            await self._save_sessions()
            
            self.logger.info(f"Сессия {session.id} создана с кодом {session.code}")
            return session.id
            
        except Exception as e:
            self.logger.error(f"Ошибка создания сессии: {e}")
            raise
    
    async def get_session(self, session_id: str) -> Optional[Session]:
        """
        Получение сессии по ID
        
        Args:
            session_id: ID сессии
            
        Returns:
            Объект сессии или None
        """
        return self.sessions.get(session_id)
    
    async def get_session_by_code(self, code: str) -> Optional[Session]:
        """
        Получение сессии по коду
        
        Args:
            code: Код сессии
            
        Returns:
            Объект сессии или None
        """
        session_id = self.sessions_by_code.get(code.upper())
        if session_id:
            return self.sessions.get(session_id)
        return None
    
    async def update_session(self, session_id: str, updates: Dict) -> bool:
        """
        Обновление сессии
        
        Args:
            session_id: ID сессии
            updates: Словарь с обновлениями
            
        Returns:
            True если сессия обновлена
        """
        try:
            session = self.sessions.get(session_id)
            if not session:
                return False
            
            # Обновляем поля
            for key, value in updates.items():
                if hasattr(session, key):
                    setattr(session, key, value)
            
            # Сохраняем на диск
            await self._save_sessions()
            
            self.logger.debug(f"Сессия {session_id} обновлена")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка обновления сессии {session_id}: {e}")
            return False
    
    async def delete_session(self, session_id: str) -> bool:
        """
        Удаление сессии
        
        Args:
            session_id: ID сессии
            
        Returns:
            True если сессия удалена
        """
        try:
            session = self.sessions.get(session_id)
            if not session:
                return False
            
            # Удаляем из индексов
            self.sessions_by_code.pop(session.code, None)
            del self.sessions[session_id]
            
            # Сохраняем на диск
            await self._save_sessions()
            
            self.logger.info(f"Сессия {session_id} удалена")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка удаления сессии {session_id}: {e}")
            return False
    
    async def get_active_sessions(self) -> List[Session]:
        """
        Получение списка активных сессий
        
        Returns:
            Список активных сессий
        """
        return [
            session for session in self.sessions.values()
            if session.status == SessionStatus.ACTIVE
        ]
    
    async def get_waiting_sessions(self) -> List[Session]:
        """
        Получение списка сессий в ожидании
        
        Returns:
            Список сессий в ожидании
        """
        return [
            session for session in self.sessions.values()
            if session.status == SessionStatus.WAITING
        ]
    
    async def get_sessions_by_admin(self, admin_id: int) -> List[Session]:
        """
        Получение сессий администратора
        
        Args:
            admin_id: ID администратора
            
        Returns:
            Список сессий администратора
        """
        return [
            session for session in self.sessions.values()
            if session.admin_id == admin_id
        ]
    
    async def get_sessions_by_player(self, player_id: int) -> List[Session]:
        """
        Получение сессий игрока
        
        Args:
            player_id: ID игрока
            
        Returns:
            Список сессий где участвует игрок
        """
        return [
            session for session in self.sessions.values()
            if player_id in session.players
        ]
    
    async def get_expired_sessions(self, cutoff_time: datetime) -> List[Session]:
        """
        Получение истекших сессий
        
        Args:
            cutoff_time: Время отсечки
            
        Returns:
            Список истекших сессий
        """
        expired_sessions = []
        
        for session in self.sessions.values():
            # Проверяем сессии в ожидании
            if (session.status == SessionStatus.WAITING and 
                session.created_at < cutoff_time):
                expired_sessions.append(session)
            
            # Проверяем активные сессии без активности
            elif (session.status == SessionStatus.ACTIVE and
                  session.started_at and 
                  session.started_at < cutoff_time - timedelta(hours=2)):
                expired_sessions.append(session)
        
        return expired_sessions
    
    async def cleanup_finished_sessions(self, older_than_hours: int = 24) -> int:
        """
        Очистка завершенных сессий
        
        Args:
            older_than_hours: Удалять сессии старше указанного количества часов
            
        Returns:
            Количество удаленных сессий
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
            deleted_count = 0
            
            sessions_to_delete = []
            for session_id, session in self.sessions.items():
                if (session.status in [SessionStatus.FINISHED, SessionStatus.CANCELLED] and
                    session.ended_at and session.ended_at < cutoff_time):
                    sessions_to_delete.append(session_id)
            
            for session_id in sessions_to_delete:
                if await self.delete_session(session_id):
                    deleted_count += 1
            
            self.logger.info(f"Очищено {deleted_count} завершенных сессий")
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Ошибка очистки завершенных сессий: {e}")
            return 0
    
    async def get_session_stats(self) -> Dict:
        """
        Получение статистики сессий
        
        Returns:
            Статистика сессий
        """
        try:
            stats = {
                "total_sessions": len(self.sessions),
                "by_status": {},
                "by_game_type": {},
                "active_players": 0,
                "average_players_per_session": 0
            }
            
            total_players = 0
            active_sessions = 0
            
            for session in self.sessions.values():
                # По статусам
                status = session.status
                stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
                
                # По типам игр
                game_type = session.game_type
                stats["by_game_type"][game_type] = stats["by_game_type"].get(game_type, 0) + 1
                
                # Подсчет игроков
                players_count = len(session.players)
                total_players += players_count
                
                if session.status == SessionStatus.ACTIVE:
                    stats["active_players"] += players_count
                    active_sessions += 1
            
            # Средние значения
            if len(self.sessions) > 0:
                stats["average_players_per_session"] = total_players / len(self.sessions)
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Ошибка получения статистики сессий: {e}")
            return {}
    
    def _load_sessions(self) -> None:
        """Загрузка сессий из файла"""
        try:
            if os.path.exists(self.sessions_file):
                with open(self.sessions_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for session_data in data.get("sessions", []):
                    session = Session(**session_data)
                    self.sessions[session.id] = session
                    self.sessions_by_code[session.code] = session.id
                
                self.logger.info(f"Загружено {len(self.sessions)} сессий из файла")
                
        except Exception as e:
            self.logger.error(f"Ошибка загрузки сессий из файла: {e}")
    
    async def _save_sessions(self) -> None:
        """Сохранение сессий в файл"""
        try:
            # Сохраняем только активные и ожидающие сессии
            sessions_to_save = [
                session.dict() for session in self.sessions.values()
                if session.status in [SessionStatus.WAITING, SessionStatus.ACTIVE]
            ]
            
            data = {
                "sessions": sessions_to_save,
                "saved_at": datetime.now().isoformat()
            }
            
            # Создаем директорию если не существует
            os.makedirs(os.path.dirname(self.sessions_file), exist_ok=True)
            
            with open(self.sessions_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
                
        except Exception as e:
            self.logger.error(f"Ошибка сохранения сессий в файл: {e}")
    
    async def get_session_info(self, session_id: str) -> Optional[SessionInfo]:
        """
        Получение краткой информации о сессии
        
        Args:
            session_id: ID сессии
            
        Returns:
            Информация о сессии
        """
        session = await self.get_session(session_id)
        if not session:
            return None
        
        return SessionInfo(
            id=session.id,
            code=session.code,
            game_type=session.game_type,
            status=session.status,
            players_count=len(session.players),
            max_players=session.max_players,
            created_at=session.created_at,
            admin_id=session.admin_id
        )
    
    def get_sessions_count(self) -> int:
        """Получение общего количества сессий"""
        return len(self.sessions)
    
    def session_exists(self, session_id: str) -> bool:
        """Проверка существования сессии"""
        return session_id in self.sessions
    
    def code_exists(self, code: str) -> bool:
        """Проверка существования кода"""
        return code.upper() in self.sessions_by_code


# Глобальный экземпляр хранилища сессий
session_storage = SessionStorage()