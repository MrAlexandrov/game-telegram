"""
API Client for Admin Bot
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
    
    # User Manager API
    async def check_admin_permissions(self, telegram_id: int) -> bool:
        """Проверить права администратора"""
        try:
            url = f"{self.user_manager_url}/api/users/{telegram_id}/permissions"
            result = await self._make_request("GET", url)
            return result.get("is_admin", False)
        except APIClientError:
            return False
    
    async def register_user(self, telegram_id: int, username: str = None, 
                          first_name: str = None, last_name: str = None) -> Dict[str, Any]:
        """Регистрация пользователя"""
        url = f"{self.user_manager_url}/api/users"
        data = {
            "telegram_id": telegram_id,
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "role": "admin"
        }
        return await self._make_request("POST", url, json=data)
    
    async def get_user_info(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Получить информацию о пользователе"""
        try:
            url = f"{self.user_manager_url}/api/users/{telegram_id}"
            return await self._make_request("GET", url)
        except APIClientError:
            return None
    
    async def update_user_activity(self, telegram_id: int) -> bool:
        """Обновить активность пользователя"""
        try:
            url = f"{self.user_manager_url}/api/users/{telegram_id}/activity"
            await self._make_request("PUT", url)
            return True
        except APIClientError:
            return False
    
    async def get_user_stats(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Получить статистику пользователя"""
        try:
            url = f"{self.user_manager_url}/api/users/{telegram_id}/stats"
            return await self._make_request("GET", url)
        except APIClientError:
            return None
    
    # Game Management API
    async def create_game(self, title: str, description: str, game_type: str, 
                         config: Dict[str, Any], questions: List[Dict[str, Any]], 
                         created_by: int) -> Dict[str, Any]:
        """Создать игру"""
        url = f"{self.user_manager_url}/api/games"
        data = {
            "title": title,
            "description": description,
            "game_type": game_type,
            "config": config,
            "questions": questions,
            "created_by": created_by
        }
        return await self._make_request("POST", url, json=data)
    
    async def get_user_games(self, user_id: int) -> List[Dict[str, Any]]:
        """Получить игры пользователя"""
        url = f"{self.user_manager_url}/api/users/{user_id}/games"
        result = await self._make_request("GET", url)
        return result.get("games", [])
    
    async def get_game_details(self, game_id: str) -> Optional[Dict[str, Any]]:
        """Получить детали игры"""
        try:
            url = f"{self.user_manager_url}/api/games/{game_id}"
            return await self._make_request("GET", url)
        except APIClientError:
            return None
    
    async def delete_game(self, game_id: str) -> bool:
        """Удалить игру"""
        try:
            url = f"{self.user_manager_url}/api/games/{game_id}"
            await self._make_request("DELETE", url)
            return True
        except APIClientError:
            return False
    
    # Session Management API
    async def create_session(self, game_id: str, admin_id: int) -> Dict[str, Any]:
        """Создать игровую сессию"""
        url = f"{self.session_manager_url}/api/sessions"
        data = {
            "game_id": game_id,
            "admin_id": admin_id
        }
        return await self._make_request("POST", url, json=data)
    
    async def get_user_sessions(self, user_id: int, status: str = None) -> List[Dict[str, Any]]:
        """Получить сессии пользователя"""
        url = f"{self.session_manager_url}/api/users/{user_id}/sessions"
        params = {}
        if status:
            params["status"] = status
        
        result = await self._make_request("GET", url, params=params)
        return result.get("sessions", [])
    
    async def get_session_details(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Получить детали сессии"""
        try:
            url = f"{self.session_manager_url}/api/sessions/{session_id}"
            return await self._make_request("GET", url)
        except APIClientError:
            return None
    
    async def update_session_status(self, session_id: str, status: str) -> bool:
        """Обновить статус сессии"""
        try:
            url = f"{self.session_manager_url}/api/sessions/{session_id}/status"
            data = {"status": status}
            await self._make_request("PUT", url, json=data)
            return True
        except APIClientError:
            return False
    
    async def get_session_players(self, session_id: str) -> List[Dict[str, Any]]:
        """Получить игроков сессии"""
        url = f"{self.session_manager_url}/api/sessions/{session_id}/players"
        result = await self._make_request("GET", url)
        return result.get("players", [])
    
    async def delete_session(self, session_id: str) -> bool:
        """Удалить сессию"""
        try:
            url = f"{self.session_manager_url}/api/sessions/{session_id}"
            await self._make_request("DELETE", url)
            return True
        except APIClientError:
            return False
    
    # Game Engine API
    async def start_game(self, session_id: str) -> Dict[str, Any]:
        """Запустить игру"""
        url = f"{self.game_engine_url}/api/engine/start-game"
        data = {"session_id": session_id}
        return await self._make_request("POST", url, json=data)
    
    async def next_question(self, session_id: str) -> Dict[str, Any]:
        """Перейти к следующему вопросу"""
        url = f"{self.game_engine_url}/api/engine/next-question"
        data = {"session_id": session_id}
        return await self._make_request("POST", url, json=data)
    
    async def get_current_question(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Получить текущий вопрос"""
        try:
            url = f"{self.game_engine_url}/api/engine/current-question/{session_id}"
            return await self._make_request("GET", url)
        except APIClientError:
            return None
    
    async def get_pending_answers(self, session_id: str) -> List[Dict[str, Any]]:
        """Получить ответы, ожидающие валидации"""
        url = f"{self.game_engine_url}/api/engine/pending-answers/{session_id}"
        result = await self._make_request("GET", url)
        return result.get("answers", [])
    
    async def validate_answer(self, answer_id: str, is_correct: bool, 
                            points: int = None) -> bool:
        """Валидировать ответ игрока"""
        try:
            url = f"{self.game_engine_url}/api/engine/validate-answer"
            data = {
                "answer_id": answer_id,
                "is_correct": is_correct
            }
            if points is not None:
                data["points"] = points
            
            await self._make_request("POST", url, json=data)
            return True
        except APIClientError:
            return False
    
    async def finish_game(self, session_id: str) -> Dict[str, Any]:
        """Завершить игру"""
        url = f"{self.game_engine_url}/api/engine/finish-game"
        data = {"session_id": session_id}
        return await self._make_request("POST", url, json=data)
    
    async def get_game_results(self, session_id: str) -> Dict[str, Any]:
        """Получить результаты игры"""
        url = f"{self.game_engine_url}/api/engine/results/{session_id}"
        return await self._make_request("GET", url)
    
    async def pause_game(self, session_id: str) -> bool:
        """Поставить игру на паузу"""
        try:
            url = f"{self.game_engine_url}/api/engine/pause-game"
            data = {"session_id": session_id}
            await self._make_request("POST", url, json=data)
            return True
        except APIClientError:
            return False
    
    async def resume_game(self, session_id: str) -> bool:
        """Возобновить игру"""
        try:
            url = f"{self.game_engine_url}/api/engine/resume-game"
            data = {"session_id": session_id}
            await self._make_request("POST", url, json=data)
            return True
        except APIClientError:
            return False
