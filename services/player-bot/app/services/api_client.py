"""
API Client for Player Bot
Клиент для взаимодействия с другими сервисами системы
"""

import aiohttp
import asyncio
import json
from typing import Dict, Any, List, Optional
import structlog
from ..config import settings

logger = structlog.get_logger()


class APIClientError(Exception):
    """Базовое исключение для API клиента"""
    pass


class APIClient:
    """Клиент для взаимодействия с API других сервисов"""
    
    def __init__(self, user_manager_url: str, game_engine_url: str, session_manager_url: str):
        self.user_manager_url = user_manager_url.rstrip('/')
        self.game_engine_url = game_engine_url.rstrip('/')
        self.session_manager_url = session_manager_url.rstrip('/')
        self.session = None
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Получить HTTP сессию"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    async def close(self):
        """Закрыть HTTP сессию"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def _make_request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """Выполнить HTTP запрос"""
        session = await self._get_session()
        
        try:
            async with session.request(method, url, **kwargs) as response:
                if response.status >= 400:
                    error_text = await response.text()
                    logger.error(f"API request failed: {method} {url} - {response.status}: {error_text}")
                    raise APIClientError(f"API request failed: {response.status}")
                
                return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"HTTP client error: {e}")
            raise APIClientError(f"HTTP client error: {e}")
        except asyncio.TimeoutError:
            logger.error(f"Request timeout: {method} {url}")
            raise APIClientError("Request timeout")
    
    # User Management API
    async def register_player(self, telegram_id: int, username: str = None, 
                            first_name: str = None, last_name: str = None) -> Dict[str, Any]:
        """Регистрация игрока"""
        url = f"{self.user_manager_url}/api/users"
        data = {
            "telegram_id": telegram_id,
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "role": "player"
        }
        return await self._make_request("POST", url, json=data)
    
    async def get_player_info(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Получить информацию об игроке"""
        try:
            url = f"{self.user_manager_url}/api/users/{telegram_id}"
            return await self._make_request("GET", url)
        except APIClientError:
            return None
    
    async def get_player_stats(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Получить статистику игрока"""
        try:
            url = f"{self.user_manager_url}/api/users/{telegram_id}/stats"
            return await self._make_request("GET", url)
        except APIClientError:
            return None
    
    async def update_player_activity(self, telegram_id: int) -> bool:
        """Обновить активность игрока"""
        try:
            url = f"{self.user_manager_url}/api/users/{telegram_id}/activity"
            await self._make_request("PUT", url)
            return True
        except APIClientError:
            return False
    
    # Session Management API
    async def join_session(self, session_code: str, telegram_id: int) -> Dict[str, Any]:
        """Присоединиться к игровой сессии"""
        url = f"{self.session_manager_url}/api/sessions/join"
        data = {
            "session_code": session_code,
            "telegram_id": telegram_id
        }
        return await self._make_request("POST", url, json=data)
    
    async def leave_session(self, session_id: str, telegram_id: int) -> bool:
        """Покинуть игровую сессию"""
        try:
            url = f"{self.session_manager_url}/api/sessions/{session_id}/leave"
            data = {"telegram_id": telegram_id}
            await self._make_request("POST", url, json=data)
            return True
        except APIClientError:
            return False
    
    async def get_session_info(self, session_code: str) -> Optional[Dict[str, Any]]:
        """Получить информацию о сессии по коду"""
        try:
            url = f"{self.session_manager_url}/api/sessions/by-code/{session_code}"
            return await self._make_request("GET", url)
        except APIClientError:
            return None
    
    async def get_player_session(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Получить активную сессию игрока"""
        try:
            url = f"{self.session_manager_url}/api/users/{telegram_id}/active-session"
            return await self._make_request("GET", url)
        except APIClientError:
            return None
    
    async def get_session_players(self, session_id: str) -> List[Dict[str, Any]]:
        """Получить список игроков в сессии"""
        url = f"{self.session_manager_url}/api/sessions/{session_id}/players"
        result = await self._make_request("GET", url)
        return result.get("players", [])
    
    async def get_session_leaderboard(self, session_id: str) -> List[Dict[str, Any]]:
        """Получить таблицу лидеров сессии"""
        url = f"{self.session_manager_url}/api/sessions/{session_id}/leaderboard"
        result = await self._make_request("GET", url)
        return result.get("leaderboard", [])
    
    # Game Engine API
    async def submit_answer(self, session_id: str, question_id: str, 
                          telegram_id: int, answer: str) -> Dict[str, Any]:
        """Отправить ответ на вопрос"""
        url = f"{self.game_engine_url}/api/engine/submit-answer"
        data = {
            "session_id": session_id,
            "question_id": question_id,
            "telegram_id": telegram_id,
            "answer": answer
        }
        return await self._make_request("POST", url, json=data)
    
    async def get_current_question(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Получить текущий вопрос для игрока"""
        try:
            url = f"{self.game_engine_url}/api/engine/current-question/{session_id}/player"
            return await self._make_request("GET", url)
        except APIClientError:
            return None
    
    async def get_player_score(self, session_id: str, telegram_id: int) -> Dict[str, Any]:
        """Получить счет игрока"""
        url = f"{self.game_engine_url}/api/engine/player-score"
        params = {"session_id": session_id, "telegram_id": telegram_id}
        return await self._make_request("GET", url, params=params)
    
    async def get_game_results(self, session_id: str) -> Dict[str, Any]:
        """Получить результаты игры"""
        url = f"{self.game_engine_url}/api/engine/results/{session_id}"
        return await self._make_request("GET", url)
    
    async def get_player_answer_history(self, session_id: str, telegram_id: int) -> List[Dict[str, Any]]:
        """Получить историю ответов игрока"""
        url = f"{self.game_engine_url}/api/engine/player-answers"
        params = {"session_id": session_id, "telegram_id": telegram_id}
        result = await self._make_request("GET", url, params=params)
        return result.get("answers", [])
    
    async def skip_question(self, session_id: str, question_id: str, telegram_id: int) -> bool:
        """Пропустить вопрос"""
        try:
            url = f"{self.game_engine_url}/api/engine/skip-question"
            data = {
                "session_id": session_id,
                "question_id": question_id,
                "telegram_id": telegram_id
            }
            await self._make_request("POST", url, json=data)
            return True
        except APIClientError:
            return False
    
    # Game Information API
    async def get_game_rules(self, game_type: str) -> Optional[Dict[str, Any]]:
        """Получить правила игры"""
        try:
            url = f"{self.game_engine_url}/api/engine/rules/{game_type}"
            return await self._make_request("GET", url)
        except APIClientError:
            return None
    
    async def get_question_hint(self, question_id: str) -> Optional[str]:
        """Получить подсказку к вопросу"""
        try:
            url = f"{self.game_engine_url}/api/engine/hint/{question_id}"
            result = await self._make_request("GET", url)
            return result.get("hint")
        except APIClientError:
            return None
    
    # Notification API (для получения уведомлений)
    async def mark_notification_read(self, notification_id: str, telegram_id: int) -> bool:
        """Отметить уведомление как прочитанное"""
        try:
            url = f"{self.user_manager_url}/api/notifications/{notification_id}/read"
            data = {"telegram_id": telegram_id}
            await self._make_request("POST", url, json=data)
            return True
        except APIClientError:
            return False
    
    async def get_player_notifications(self, telegram_id: int) -> List[Dict[str, Any]]:
        """Получить уведомления игрока"""
        try:
            url = f"{self.user_manager_url}/api/users/{telegram_id}/notifications"
            result = await self._make_request("GET", url)
            return result.get("notifications", [])
        except APIClientError:
            return []
    
    # Utility methods
    async def validate_session_code(self, session_code: str) -> bool:
        """Проверить валидность кода сессии"""
        session_info = await self.get_session_info(session_code)
        return session_info is not None
    
    async def check_session_status(self, session_id: str) -> Optional[str]:
        """Проверить статус сессии"""
        try:
            url = f"{self.session_manager_url}/api/sessions/{session_id}/status"
            result = await self._make_request("GET", url)
            return result.get("status")
        except APIClientError:
            return None
    
    async def ping_services(self) -> Dict[str, bool]:
        """Проверить доступность сервисов"""
        services = {
            "user_manager": self.user_manager_url,
            "game_engine": self.game_engine_url,
            "session_manager": self.session_manager_url
        }
        
        results = {}
        for service_name, service_url in services.items():
            try:
                url = f"{service_url}/health"
                await self._make_request("GET", url)
                results[service_name] = True
            except APIClientError:
                results[service_name] = False
        
        return results
