"""
Integration Tests for Telegram Bots
Тесты интеграции для проверки работы ботов
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, User, Chat, CallbackQuery

# Import bot components
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'services', 'admin-bot', 'app'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'services', 'player-bot', 'app'))

from services.admin_bot.app.handlers import admin_handlers, game_handlers, session_handlers
from services.player_bot.app.handlers import player_handlers, game_handlers as player_game_handlers
from services.admin_bot.app.services.api_client import APIClient as AdminAPIClient
from services.player_bot.app.services.api_client import APIClient as PlayerAPIClient


class TestAdminBotIntegration:
    """Тесты интеграции Admin Bot"""
    
    @pytest.fixture
    async def admin_bot_setup(self):
        """Настройка Admin Bot для тестов"""
        bot = Bot(token="TEST_TOKEN")
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)
        
        # Mock API client
        api_client = AsyncMock(spec=AdminAPIClient)
        dp["api_client"] = api_client
        
        # Include routers
        dp.include_router(admin_handlers.router)
        dp.include_router(game_handlers.router)
        dp.include_router(session_handlers.router)
        
        return bot, dp, api_client
    
    @pytest.mark.asyncio
    async def test_admin_start_command(self, admin_bot_setup):
        """Тест команды /start для администратора"""
        bot, dp, api_client = admin_bot_setup
        
        # Mock API responses
        api_client.check_admin_permissions.return_value = True
        api_client.register_user.return_value = {"id": 1, "role": "admin"}
        
        # Create test message
        user = User(id=123, is_bot=False, first_name="Admin", username="admin_user")
        chat = Chat(id=123, type="private")
        message = Message(
            message_id=1,
            date=1234567890,
            chat=chat,
            from_user=user,
            text="/start"
        )
        
        # Mock bot methods
        bot.send_message = AsyncMock()
        
        # Process message
        await dp.feed_update(bot, {"message": message})
        
        # Verify API calls
        api_client.check_admin_permissions.assert_called_once_with(123)
        api_client.register_user.assert_called_once()
        
        # Verify response
        bot.send_message.assert_called_once()
        call_args = bot.send_message.call_args
        assert "Добро пожаловать" in call_args[1]["text"]
    
    @pytest.mark.asyncio
    async def test_admin_unauthorized_access(self, admin_bot_setup):
        """Тест отказа в доступе для неавторизованного пользователя"""
        bot, dp, api_client = admin_bot_setup
        
        # Mock API responses - user is not admin
        api_client.check_admin_permissions.return_value = False
        
        # Create test message
        user = User(id=456, is_bot=False, first_name="User", username="regular_user")
        chat = Chat(id=456, type="private")
        message = Message(
            message_id=1,
            date=1234567890,
            chat=chat,
            from_user=user,
            text="/start"
        )
        
        # Mock bot methods
        bot.send_message = AsyncMock()
        
        # Process message
        await dp.feed_update(bot, {"message": message})
        
        # Verify response
        bot.send_message.assert_called_once()
        call_args = bot.send_message.call_args
        assert "нет прав администратора" in call_args[1]["text"]


class TestPlayerBotIntegration:
    """Тесты интеграции Player Bot"""
    
    @pytest.fixture
    async def player_bot_setup(self):
        """Настройка Player Bot для тестов"""
        bot = Bot(token="TEST_TOKEN")
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)
        
        # Mock API client
        api_client = AsyncMock(spec=PlayerAPIClient)
        dp["api_client"] = api_client
        
        # Include routers
        dp.include_router(player_handlers.router)
        dp.include_router(player_game_handlers.router)
        
        return bot, dp, api_client
    
    @pytest.mark.asyncio
    async def test_player_start_command(self, player_bot_setup):
        """Тест команды /start для игрока"""
        bot, dp, api_client = player_bot_setup
        
        # Mock API responses
        api_client.register_player.return_value = {"id": 1, "role": "player"}
        
        # Create test message
        user = User(id=789, is_bot=False, first_name="Player", username="player_user")
        chat = Chat(id=789, type="private")
        message = Message(
            message_id=1,
            date=1234567890,
            chat=chat,
            from_user=user,
            text="/start"
        )
        
        # Mock bot methods
        bot.send_message = AsyncMock()
        
        # Process message
        await dp.feed_update(bot, {"message": message})
        
        # Verify API calls
        api_client.register_player.assert_called_once()
        
        # Verify response
        bot.send_message.assert_called_once()
        call_args = bot.send_message.call_args
        assert "Привет" in call_args[1]["text"]
    
    @pytest.mark.asyncio
    async def test_player_join_game_with_code(self, player_bot_setup):
        """Тест подключения к игре по коду"""
        bot, dp, api_client = player_bot_setup
        
        # Mock API responses
        api_client.register_player.return_value = {"id": 1, "role": "player"}
        api_client.get_session_info.return_value = {
            "game_title": "Test Game",
            "players_count": 2,
            "status": "waiting"
        }
        
        # Create test message with session code
        user = User(id=789, is_bot=False, first_name="Player", username="player_user")
        chat = Chat(id=789, type="private")
        message = Message(
            message_id=1,
            date=1234567890,
            chat=chat,
            from_user=user,
            text="/start ABC123"
        )
        
        # Mock bot methods
        bot.send_message = AsyncMock()
        
        # Process message
        await dp.feed_update(bot, {"message": message})
        
        # Verify API calls
        api_client.get_session_info.assert_called_once_with("ABC123")
        
        # Verify response contains game info
        bot.send_message.assert_called_once()
        call_args = bot.send_message.call_args
        assert "Test Game" in call_args[1]["text"]
        assert "ABC123" in call_args[1]["text"]


class TestAPIClientIntegration:
    """Тесты интеграции API клиентов"""
    
    @pytest.mark.asyncio
    async def test_admin_api_client_user_management(self):
        """Тест управления пользователями через Admin API"""
        api_client = AdminAPIClient(
            user_manager_url="http://test-user-manager",
            game_engine_url="http://test-game-engine",
            session_manager_url="http://test-session-manager"
        )
        
        with patch('aiohttp.ClientSession.request') as mock_request:
            # Mock successful response
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {"id": 1, "role": "admin"}
            mock_request.return_value.__aenter__.return_value = mock_response
            
            # Test user registration
            result = await api_client.register_user(
                telegram_id=123,
                username="admin_user",
                first_name="Admin",
                last_name="User"
            )
            
            assert result["id"] == 1
            assert result["role"] == "admin"
    
    @pytest.mark.asyncio
    async def test_player_api_client_session_management(self):
        """Тест управления сессиями через Player API"""
        api_client = PlayerAPIClient(
            user_manager_url="http://test-user-manager",
            game_engine_url="http://test-game-engine",
            session_manager_url="http://test-session-manager"
        )
        
        with patch('aiohttp.ClientSession.request') as mock_request:
            # Mock successful response
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {
                "session_id": "sess_123",
                "game_title": "Test Game",
                "status": "joined"
            }
            mock_request.return_value.__aenter__.return_value = mock_response
            
            # Test session join
            result = await api_client.join_session(
                session_code="ABC123",
                telegram_id=789
            )
            
            assert result["session_id"] == "sess_123"
            assert result["game_title"] == "Test Game"


class TestErrorHandling:
    """Тесты обработки ошибок"""
    
    @pytest.mark.asyncio
    async def test_api_client_error_handling(self):
        """Тест обработки ошибок API клиента"""
        api_client = AdminAPIClient(
            user_manager_url="http://test-user-manager",
            game_engine_url="http://test-game-engine",
            session_manager_url="http://test-session-manager"
        )
        
        with patch('aiohttp.ClientSession.request') as mock_request:
            # Mock error response
            mock_response = AsyncMock()
            mock_response.status = 500
            mock_response.text.return_value = "Internal Server Error"
            mock_request.return_value.__aenter__.return_value = mock_response
            
            # Test error handling
            with pytest.raises(Exception):
                await api_client.register_user(
                    telegram_id=123,
                    username="test_user"
                )
    
    @pytest.mark.asyncio
    async def test_middleware_error_handling(self):
        """Тест обработки ошибок в middleware"""
        from services.admin_bot.app.middlewares.error_handler_middleware import ErrorHandlerMiddleware
        
        middleware = ErrorHandlerMiddleware()
        
        # Mock handler that raises exception
        async def failing_handler(event, data):
            raise ValueError("Test error")
        
        # Mock event
        user = User(id=123, is_bot=False, first_name="Test")
        chat = Chat(id=123, type="private")
        message = Message(
            message_id=1,
            date=1234567890,
            chat=chat,
            from_user=user,
            text="test"
        )
        
        # Mock bot
        bot = AsyncMock()
        data = {"bot": bot}
        
        # Test error handling
        with pytest.raises(ValueError):
            await middleware(failing_handler, message, data)
        
        # Verify error message was sent
        bot.send_message.assert_called_once()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])