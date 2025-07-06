"""
Менеджер игровых сессий
"""
import asyncio
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import logging

from src.models.session import Session, SessionInfo
from src.models.enums import SessionStatus, GameType
from src.storage.session_storage import session_storage
from src.storage.pack_storage import pack_storage
from src.storage.user_storage import user_storage
from src.games.engine import game_engine
from src.utils.code_generator import generate_session_code
from src.utils.qr_generator import generate_session_qr_code
from src.settings import settings


class SessionManager:
    """Менеджер для управления игровыми сессиями"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Фоновая задача очистки (будет запущена позже)
        self._cleanup_task = None
        self._cleanup_started = False
    
    async def create_session(self, pack_id: str, admin_id: int,
                           max_players: Optional[int] = None) -> Optional[Session]:
        """
        Создание новой игровой сессии
        
        Args:
            pack_id: ID игрового пака
            admin_id: ID администратора
            max_players: Максимальное количество игроков
            
        Returns:
            Созданная сессия или None при ошибке
        """
        # Запускаем задачу очистки при первом использовании
        self._start_cleanup_task()
        
        try:
            # Проверяем, что пользователь является администратором
            if not user_storage.is_admin(admin_id):
                self.logger.warning(f"Пользователь {admin_id} не является администратором")
                return None
            
            # Загружаем игровой пак
            pack = await pack_storage.load_pack(pack_id)
            if not pack:
                self.logger.error(f"Игровой пак {pack_id} не найден")
                return None
            
            # Генерируем уникальный код сессии
            session_code = generate_session_code()
            
            # Создаем сессию
            session = Session(
                id=f"session_{session_code}_{int(datetime.now().timestamp())}",
                code=session_code,
                admin_id=admin_id,
                game_pack_id=pack_id,
                game_type=GameType(pack.type),
                status=SessionStatus.WAITING,
                players=[],
                max_players=max_players or settings.max_players_per_session,
                expires_at=datetime.now() + timedelta(minutes=settings.session_timeout_minutes)
            )
            
            # Сохраняем сессию
            session_id = await session_storage.create_session(session)
            if not session_id:
                self.logger.error("Не удалось сохранить сессию")
                return None
            
            self.logger.info(f"Создана сессия {session_id} с кодом {session_code}")
            return session
            
        except Exception as e:
            self.logger.error(f"Ошибка создания сессии: {e}")
            return None
    
    async def join_session(self, session_code: str, user_id: int) -> bool:
        """
        Подключение игрока к сессии
        
        Args:
            session_code: Код сессии
            user_id: ID пользователя
            
        Returns:
            True если игрок успешно подключился
        """
        # Запускаем задачу очистки при первом использовании
        self._start_cleanup_task()
        
        try:
            # Нормализуем код
            session_code = session_code.upper().strip()
            
            # Находим сессию
            session = await session_storage.get_session_by_code(session_code)
            if not session:
                self.logger.warning(f"Сессия с кодом {session_code} не найдена")
                return False
            
            # Проверяем, можно ли подключиться
            if not session.can_join:
                self.logger.warning(f"К сессии {session.id} нельзя подключиться (статус: {session.status})")
                return False
            
            # Проверяем, не подключен ли уже игрок
            if user_id in session.players:
                self.logger.info(f"Игрок {user_id} уже подключен к сессии {session.id}")
                return True
            
            # Регистрируем пользователя если не зарегистрирован
            if not user_storage.user_exists(user_id):
                await user_storage.register_user(user_id)
            
            # Добавляем игрока в сессию
            success = session.add_player(user_id)
            if not success:
                return False
            
            # Обновляем сессию в хранилище
            await session_storage.update_session(session.id, {"players": session.players})
            
            # Добавляем пользовательскую сессию
            await user_storage.add_user_session(user_id, session.id)
            
            self.logger.info(f"Игрок {user_id} подключился к сессии {session.id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка подключения игрока {user_id} к сессии {session_code}: {e}")
            return False
    
    async def leave_session(self, session_id: str, user_id: int) -> bool:
        """
        Отключение игрока от сессии
        
        Args:
            session_id: ID сессии
            user_id: ID пользователя
            
        Returns:
            True если игрок отключился
        """
        # Запускаем задачу очистки при первом использовании
        self._start_cleanup_task()
        
        try:
            session = await session_storage.get_session(session_id)
            if not session:
                return False
            
            # Удаляем игрока из сессии
            success = session.remove_player(user_id)
            if not success:
                return False
            
            # Обновляем сессию в хранилище
            await session_storage.update_session(session_id, {"players": session.players})
            
            # Удаляем игрока из игры если она активна
            if session.status == SessionStatus.ACTIVE:
                game_engine.remove_player_from_game(session_id, user_id)
            
            # Завершаем пользовательскую сессию
            await user_storage.finish_user_session(user_id, session_id)
            
            self.logger.info(f"Игрок {user_id} отключился от сессии {session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка отключения игрока {user_id} от сессии {session_id}: {e}")
            return False
    
    async def start_session(self, session_id: str, admin_id: int) -> bool:
        """
        Запуск игровой сессии
        
        Args:
            session_id: ID сессии
            admin_id: ID администратора
            
        Returns:
            True если сессия запущена
        """
        # Запускаем задачу очистки при первом использовании
        self._start_cleanup_task()
        
        try:
            session = await session_storage.get_session(session_id)
            if not session:
                self.logger.error(f"Сессия {session_id} не найдена")
                return False
            
            # Проверяем права администратора
            if session.admin_id != admin_id:
                self.logger.warning(f"Пользователь {admin_id} не является администратором сессии {session_id}")
                return False
            
            # Проверяем статус сессии
            if session.status != SessionStatus.WAITING:
                self.logger.warning(f"Сессия {session_id} не в состоянии ожидания")
                return False
            
            # Проверяем, есть ли игроки
            if len(session.players) == 0:
                self.logger.warning(f"В сессии {session_id} нет игроков")
                return False
            
            # Загружаем игровой пак
            pack = await pack_storage.load_pack(session.game_pack_id)
            if not pack:
                self.logger.error(f"Игровой пак {session.game_pack_id} не найден")
                return False
            
            # Инициализируем игру
            game_initialized = await game_engine.initialize_game(
                session_id, session.game_type, pack.dict()
            )
            if not game_initialized:
                self.logger.error(f"Не удалось инициализировать игру для сессии {session_id}")
                return False
            
            # Добавляем игроков в игру
            for player_id in session.players:
                game_engine.add_player_to_game(session_id, player_id)
            
            # Запускаем игру
            game_started = await game_engine.start_game(session_id)
            if not game_started:
                self.logger.error(f"Не удалось запустить игру для сессии {session_id}")
                return False
            
            # Обновляем статус сессии
            success = session.start_session()
            if not success:
                return False
            
            await session_storage.update_session(session_id, {
                "status": session.status,
                "started_at": session.started_at
            })
            
            self.logger.info(f"Сессия {session_id} запущена с {len(session.players)} игроками")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка запуска сессии {session_id}: {e}")
            return False
    
    async def end_session(self, session_id: str, admin_id: int) -> Optional[Dict]:
        """
        Завершение игровой сессии
        
        Args:
            session_id: ID сессии
            admin_id: ID администратора
            
        Returns:
            Результаты игры или None
        """
        try:
            session = await session_storage.get_session(session_id)
            if not session:
                return None
            
            # Проверяем права администратора
            if session.admin_id != admin_id:
                self.logger.warning(f"Пользователь {admin_id} не является администратором сессии {session_id}")
                return None
            
            # Получаем результаты игры
            results = await game_engine.finish_game(session_id)
            
            # Обновляем статистику игроков
            if results and results.players_results:
                winner_id = results.winner
                for player_id, score in results.players_results:
                    won = player_id == winner_id
                    await user_storage.add_game_result(player_id, won, score)
                    await user_storage.finish_user_session(player_id, session_id)
            
            # Завершаем сессию
            session.finish_session(results.dict() if results else None)
            
            await session_storage.update_session(session_id, {
                "status": session.status,
                "ended_at": session.ended_at,
                "results": session.results
            })
            
            # Очищаем игру из памяти
            await game_engine.cleanup_game(session_id)
            
            self.logger.info(f"Сессия {session_id} завершена")
            return session.results
            
        except Exception as e:
            self.logger.error(f"Ошибка завершения сессии {session_id}: {e}")
            return None
    
    async def cancel_session(self, session_id: str, admin_id: int) -> bool:
        """
        Отмена игровой сессии
        
        Args:
            session_id: ID сессии
            admin_id: ID администратора
            
        Returns:
            True если сессия отменена
        """
        # Запускаем задачу очистки при первом использовании
        self._start_cleanup_task()
        
        try:
            session = await session_storage.get_session(session_id)
            if not session:
                return False
            
            # Проверяем права администратора
            if session.admin_id != admin_id:
                return False
            
            # Отменяем сессию
            session.cancel_session()
            
            await session_storage.update_session(session_id, {
                "status": session.status,
                "ended_at": session.ended_at
            })
            
            # Очищаем игру из памяти
            await game_engine.cleanup_game(session_id)
            
            # Завершаем пользовательские сессии
            for player_id in session.players:
                await user_storage.finish_user_session(player_id, session_id)
            
            self.logger.info(f"Сессия {session_id} отменена")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка отмены сессии {session_id}: {e}")
            return False
    
    async def get_session_info(self, session_id: str) -> Optional[SessionInfo]:
        """
        Получение информации о сессии
        
        Args:
            session_id: ID сессии
            
        Returns:
            Информация о сессии
        """
        # Запускаем задачу очистки при первом использовании
        self._start_cleanup_task()
        
        return await session_storage.get_session_info(session_id)
    
    async def get_session_by_code(self, session_code: str) -> Optional[Session]:
        """
        Получение сессии по коду
        
        Args:
            session_code: Код сессии
            
        Returns:
            Сессия или None
        """
        # Запускаем задачу очистки при первом использовании
        self._start_cleanup_task()
        
        return await session_storage.get_session_by_code(session_code)
    
    async def generate_qr_code(self, session_code: str) -> bytes:
        """
        Генерация QR-кода для сессии
        
        Args:
            session_code: Код сессии
            
        Returns:
            QR-код в виде байтов
        """
        try:
            bot_username = settings.player_bot_username
            return generate_session_qr_code(session_code, bot_username)
        except Exception as e:
            self.logger.error(f"Ошибка генерации QR-кода для сессии {session_code}: {e}")
            raise
    
    async def get_admin_sessions(self, admin_id: int) -> List[Session]:
        """
        Получение сессий администратора
        
        Args:
            admin_id: ID администратора
            
        Returns:
            Список сессий администратора
        """
        # Запускаем задачу очистки при первом использовании
        self._start_cleanup_task()
        
        return await session_storage.get_sessions_by_admin(admin_id)
    
    async def get_player_sessions(self, player_id: int) -> List[Session]:
        """
        Получение сессий игрока
        
        Args:
            player_id: ID игрока
            
        Returns:
            Список сессий игрока
        """
        # Запускаем задачу очистки при первом использовании
        self._start_cleanup_task()
        
        return await session_storage.get_sessions_by_player(player_id)
    
    async def get_active_sessions(self) -> List[Session]:
        """
        Получение активных сессий
        
        Returns:
            Список активных сессий
        """
        # Запускаем задачу очистки при первом использовании
        self._start_cleanup_task()
        
        return await session_storage.get_active_sessions()
    
    async def cleanup_expired_sessions(self) -> int:
        """
        Очистка истекших сессий
        
        Returns:
            Количество очищенных сессий
        """
        try:
            timeout = timedelta(minutes=settings.session_timeout_minutes)
            cutoff_time = datetime.now() - timeout
            
            expired_sessions = await session_storage.get_expired_sessions(cutoff_time)
            cleaned_count = 0
            
            for session in expired_sessions:
                # Завершаем игру если активна
                if session.status == SessionStatus.ACTIVE:
                    await game_engine.cleanup_game(session.id)
                
                # Отменяем сессию
                session.cancel_session()
                await session_storage.update_session(session.id, {
                    "status": session.status,
                    "ended_at": session.ended_at
                })
                
                # Завершаем пользовательские сессии
                for player_id in session.players:
                    await user_storage.finish_user_session(player_id, session.id)
                
                cleaned_count += 1
            
            # Очищаем старые завершенные сессии
            finished_cleaned = await session_storage.cleanup_finished_sessions(24)
            
            total_cleaned = cleaned_count + finished_cleaned
            if total_cleaned > 0:
                self.logger.info(f"Очищено {total_cleaned} сессий ({cleaned_count} истекших, {finished_cleaned} завершенных)")
            
            return total_cleaned
            
        except Exception as e:
            self.logger.error(f"Ошибка очистки истекших сессий: {e}")
            return 0
    
    def _start_cleanup_task(self):
        """Запуск фоновой задачи очистки"""
        if self._cleanup_started:
            return
            
        try:
            # Проверяем, есть ли запущенный event loop
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # Нет запущенного event loop, отложим запуск
            return
            
        async def cleanup_loop():
            while True:
                try:
                    await asyncio.sleep(300)  # Каждые 5 минут
                    await self.cleanup_expired_sessions()
                except Exception as e:
                    self.logger.error(f"Ошибка в фоновой задаче очистки: {e}")
        
        self._cleanup_task = asyncio.create_task(cleanup_loop())
        self._cleanup_started = True
    
    async def stop_cleanup_task(self):
        """Остановка фоновой задачи очистки"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass


# Глобальный экземпляр менеджера сессий
session_manager = SessionManager()