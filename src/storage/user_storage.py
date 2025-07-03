"""
Хранилище пользователей
"""
import json
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

from src.models.user import User, UserStats, UserSession
from src.models.enums import UserRole
from src.settings import settings


class UserStorage:
    """Хранилище пользователей в памяти с возможностью персистентности"""
    
    def __init__(self):
        self.users: Dict[int, User] = {}
        self.user_sessions: Dict[int, List[UserSession]] = {}
        self.logger = logging.getLogger(__name__)
        
        # Путь для сохранения пользователей
        self.users_file = os.path.join(settings.temp_dir, "users.json")
        
        # Загружаем сохраненных пользователей при инициализации
        self._load_users()
    
    async def register_user(self, telegram_id: int, username: Optional[str] = None, 
                          first_name: Optional[str] = None, last_name: Optional[str] = None) -> User:
        """
        Регистрация или обновление пользователя
        
        Args:
            telegram_id: ID пользователя в Telegram
            username: Username пользователя
            first_name: Имя пользователя
            last_name: Фамилия пользователя
            
        Returns:
            Объект пользователя
        """
        try:
            # Проверяем, существует ли пользователь
            existing_user = self.users.get(telegram_id)
            
            if existing_user:
                # Обновляем информацию
                existing_user.username = username
                existing_user.first_name = first_name
                existing_user.last_name = last_name
                existing_user.update_activity()
                
                user = existing_user
            else:
                # Создаем нового пользователя
                is_admin = telegram_id == settings.root_id
                role = UserRole.ADMIN if is_admin else UserRole.PLAYER
                
                user = User(
                    telegram_id=telegram_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    role=role,
                    is_admin=is_admin
                )
                
                self.users[telegram_id] = user
                self.user_sessions[telegram_id] = []
            
            # Сохраняем на диск
            await self._save_users()
            
            self.logger.info(f"Пользователь {telegram_id} зарегистрирован/обновлен")
            return user
            
        except Exception as e:
            self.logger.error(f"Ошибка регистрации пользователя {telegram_id}: {e}")
            raise
    
    async def get_user(self, telegram_id: int) -> Optional[User]:
        """
        Получение пользователя по ID
        
        Args:
            telegram_id: ID пользователя в Telegram
            
        Returns:
            Объект пользователя или None
        """
        user = self.users.get(telegram_id)
        if user:
            user.update_activity()
            await self._save_users()
        return user
    
    async def update_user(self, telegram_id: int, updates: Dict) -> bool:
        """
        Обновление пользователя
        
        Args:
            telegram_id: ID пользователя
            updates: Словарь с обновлениями
            
        Returns:
            True если пользователь обновлен
        """
        try:
            user = self.users.get(telegram_id)
            if not user:
                return False
            
            # Обновляем поля
            for key, value in updates.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            
            user.update_activity()
            
            # Сохраняем на диск
            await self._save_users()
            
            self.logger.debug(f"Пользователь {telegram_id} обновлен")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка обновления пользователя {telegram_id}: {e}")
            return False
    
    async def delete_user(self, telegram_id: int) -> bool:
        """
        Удаление пользователя
        
        Args:
            telegram_id: ID пользователя
            
        Returns:
            True если пользователь удален
        """
        try:
            if telegram_id in self.users:
                del self.users[telegram_id]
                self.user_sessions.pop(telegram_id, None)
                
                # Сохраняем на диск
                await self._save_users()
                
                self.logger.info(f"Пользователь {telegram_id} удален")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Ошибка удаления пользователя {telegram_id}: {e}")
            return False
    
    def is_admin(self, telegram_id: int) -> bool:
        """
        Проверка, является ли пользователь администратором
        
        Args:
            telegram_id: ID пользователя
            
        Returns:
            True если пользователь администратор
        """
        user = self.users.get(telegram_id)
        return user is not None and user.is_admin
    
    def user_exists(self, telegram_id: int) -> bool:
        """
        Проверка существования пользователя
        
        Args:
            telegram_id: ID пользователя
            
        Returns:
            True если пользователь существует
        """
        return telegram_id in self.users
    
    async def get_all_users(self) -> List[User]:
        """
        Получение всех пользователей
        
        Returns:
            Список всех пользователей
        """
        return list(self.users.values())
    
    async def get_admins(self) -> List[User]:
        """
        Получение списка администраторов
        
        Returns:
            Список администраторов
        """
        return [user for user in self.users.values() if user.is_admin]
    
    async def get_players(self) -> List[User]:
        """
        Получение списка игроков
        
        Returns:
            Список игроков
        """
        return [user for user in self.users.values() if not user.is_admin]
    
    async def add_game_result(self, telegram_id: int, won: bool, score: int) -> bool:
        """
        Добавление результата игры для пользователя
        
        Args:
            telegram_id: ID пользователя
            won: Выиграл ли игру
            score: Набранные очки
            
        Returns:
            True если результат добавлен
        """
        try:
            user = self.users.get(telegram_id)
            if not user:
                return False
            
            user.add_game_result(won, score)
            
            # Сохраняем на диск
            await self._save_users()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка добавления результата игры для пользователя {telegram_id}: {e}")
            return False
    
    async def get_user_stats(self, telegram_id: int) -> Optional[UserStats]:
        """
        Получение статистики пользователя
        
        Args:
            telegram_id: ID пользователя
            
        Returns:
            Статистика пользователя
        """
        user = self.users.get(telegram_id)
        if not user:
            return None
        
        # Находим лучший результат из сессий
        user_sessions = self.user_sessions.get(telegram_id, [])
        best_score = max([session.current_score for session in user_sessions], default=0)
        last_game_date = max([session.joined_at for session in user_sessions], default=None)
        
        return UserStats(
            user_id=telegram_id,
            games_played=user.games_played,
            games_won=user.games_won,
            total_score=user.total_score,
            average_score=user.total_score / user.games_played if user.games_played > 0 else 0,
            win_rate=user.win_rate,
            best_score=best_score,
            last_game_date=last_game_date
        )
    
    async def add_user_session(self, telegram_id: int, session_id: str) -> UserSession:
        """
        Добавление пользователя в сессию
        
        Args:
            telegram_id: ID пользователя
            session_id: ID сессии
            
        Returns:
            Объект пользовательской сессии
        """
        user_session = UserSession(
            user_id=telegram_id,
            session_id=session_id
        )
        
        if telegram_id not in self.user_sessions:
            self.user_sessions[telegram_id] = []
        
        self.user_sessions[telegram_id].append(user_session)
        
        return user_session
    
    async def update_user_session(self, telegram_id: int, session_id: str, 
                                score: int, correct_answer: bool = False) -> bool:
        """
        Обновление пользовательской сессии
        
        Args:
            telegram_id: ID пользователя
            session_id: ID сессии
            score: Добавляемые очки
            correct_answer: Правильный ли ответ
            
        Returns:
            True если сессия обновлена
        """
        try:
            user_sessions = self.user_sessions.get(telegram_id, [])
            
            for user_session in user_sessions:
                if user_session.session_id == session_id and user_session.is_active:
                    user_session.current_score += score
                    user_session.answers_count += 1
                    if correct_answer:
                        user_session.correct_answers += 1
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Ошибка обновления пользовательской сессии {telegram_id}/{session_id}: {e}")
            return False
    
    async def finish_user_session(self, telegram_id: int, session_id: str) -> bool:
        """
        Завершение пользовательской сессии
        
        Args:
            telegram_id: ID пользователя
            session_id: ID сессии
            
        Returns:
            True если сессия завершена
        """
        try:
            user_sessions = self.user_sessions.get(telegram_id, [])
            
            for user_session in user_sessions:
                if user_session.session_id == session_id and user_session.is_active:
                    user_session.is_active = False
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Ошибка завершения пользовательской сессии {telegram_id}/{session_id}: {e}")
            return False
    
    async def get_leaderboard(self, limit: int = 10) -> List[User]:
        """
        Получение таблицы лидеров
        
        Args:
            limit: Количество пользователей в топе
            
        Returns:
            Список лучших игроков
        """
        players = await self.get_players()
        
        # Сортируем по общему счету, затем по проценту побед
        leaderboard = sorted(
            players,
            key=lambda user: (user.total_score, user.win_rate, user.games_played),
            reverse=True
        )
        
        return leaderboard[:limit]
    
    async def get_user_statistics(self) -> Dict:
        """
        Получение общей статистики пользователей
        
        Returns:
            Статистика пользователей
        """
        try:
            total_users = len(self.users)
            admins_count = len([u for u in self.users.values() if u.is_admin])
            players_count = total_users - admins_count
            
            # Активные пользователи (играли в последние 7 дней)
            week_ago = datetime.now() - datetime.timedelta(days=7)
            active_users = len([
                u for u in self.users.values() 
                if u.last_active and u.last_active > week_ago
            ])
            
            # Статистика игр
            total_games = sum(u.games_played for u in self.users.values())
            total_score = sum(u.total_score for u in self.users.values())
            
            return {
                "total_users": total_users,
                "admins_count": admins_count,
                "players_count": players_count,
                "active_users": active_users,
                "total_games_played": total_games,
                "total_score": total_score,
                "average_games_per_user": total_games / players_count if players_count > 0 else 0,
                "average_score_per_user": total_score / players_count if players_count > 0 else 0
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка получения статистики пользователей: {e}")
            return {}
    
    def _load_users(self) -> None:
        """Загрузка пользователей из файла"""
        try:
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for user_data in data.get("users", []):
                    user = User(**user_data)
                    self.users[user.telegram_id] = user
                
                # Загружаем пользовательские сессии
                for telegram_id, sessions_data in data.get("user_sessions", {}).items():
                    telegram_id = int(telegram_id)
                    self.user_sessions[telegram_id] = [
                        UserSession(**session_data) for session_data in sessions_data
                    ]
                
                self.logger.info(f"Загружено {len(self.users)} пользователей из файла")
                
        except Exception as e:
            self.logger.error(f"Ошибка загрузки пользователей из файла: {e}")
    
    async def _save_users(self) -> None:
        """Сохранение пользователей в файл"""
        try:
            data = {
                "users": [user.dict() for user in self.users.values()],
                "user_sessions": {
                    str(telegram_id): [session.dict() for session in sessions]
                    for telegram_id, sessions in self.user_sessions.items()
                },
                "saved_at": datetime.now().isoformat()
            }
            
            # Создаем директорию если не существует
            os.makedirs(os.path.dirname(self.users_file), exist_ok=True)
            
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
                
        except Exception as e:
            self.logger.error(f"Ошибка сохранения пользователей в файл: {e}")
    
    def get_users_count(self) -> int:
        """Получение общего количества пользователей"""
        return len(self.users)


# Глобальный экземпляр хранилища пользователей
user_storage = UserStorage()
