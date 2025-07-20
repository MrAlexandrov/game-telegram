"""
Global pytest configuration and fixtures for the game-telegram project.
"""
import asyncio
import os
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock
import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Test environment setup
os.environ.update({
    "ENVIRONMENT": "test",
    "DATABASE_URL": "sqlite:///./test.db",
    "REDIS_URL": "redis://localhost:6379/1",
    "ADMIN_BOT_TOKEN": "test_admin_token",
    "PLAYER_BOT_TOKEN": "test_player_token",
    "SECRET_KEY": "test_secret_key",
    "API_HOST": "localhost",
    "API_PORT": "8000",
})

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    redis_mock = AsyncMock()
    redis_mock.get.return_value = None
    redis_mock.set.return_value = True
    redis_mock.delete.return_value = True
    redis_mock.exists.return_value = False
    redis_mock.expire.return_value = True
    redis_mock.hget.return_value = None
    redis_mock.hset.return_value = True
    redis_mock.hdel.return_value = True
    redis_mock.hgetall.return_value = {}
    return redis_mock

@pytest.fixture
def mock_database():
    """Mock database session for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    def get_test_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    return get_test_db

@pytest_asyncio.fixture
async def http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """HTTP client for API testing."""
    async with httpx.AsyncClient() as client:
        yield client

@pytest.fixture
def mock_telegram_bot():
    """Mock Telegram bot for testing."""
    bot_mock = AsyncMock()
    bot_mock.send_message.return_value = MagicMock(message_id=123)
    bot_mock.send_photo.return_value = MagicMock(message_id=124)
    bot_mock.send_document.return_value = MagicMock(message_id=125)
    bot_mock.edit_message_text.return_value = True
    bot_mock.edit_message_reply_markup.return_value = True
    bot_mock.delete_message.return_value = True
    bot_mock.get_me.return_value = MagicMock(id=123456789, username="test_bot")
    return bot_mock

@pytest.fixture
def sample_game_data():
    """Sample game data for testing."""
    return {
        "id": "test-game-123",
        "title": "Test Quiz Game",
        "description": "A test quiz game for unit testing",
        "type": "quiz",
        "settings": {
            "time_limit": 30,
            "max_players": 10,
            "show_correct_answers": True
        },
        "questions": [
            {
                "id": "q1",
                "type": "single_choice",
                "question": "What is 2 + 2?",
                "options": ["3", "4", "5", "6"],
                "correct_answer": 1,
                "points": 10,
                "time_limit": 15
            },
            {
                "id": "q2",
                "type": "multiple_choice",
                "question": "Which are programming languages?",
                "options": ["Python", "JavaScript", "HTML", "CSS"],
                "correct_answers": [0, 1],
                "points": 15,
                "time_limit": 20
            }
        ]
    }

@pytest.fixture
def sample_session_data():
    """Sample session data for testing."""
    return {
        "session_id": "test-session-123",
        "game_id": "test-game-123",
        "admin_id": 123456789,
        "status": "waiting",
        "players": [],
        "current_question": None,
        "settings": {
            "max_players": 10,
            "auto_start": False
        },
        "created_at": "2024-01-01T00:00:00Z"
    }

@pytest.fixture
def sample_player_data():
    """Sample player data for testing."""
    return {
        "user_id": 987654321,
        "username": "test_player",
        "first_name": "Test",
        "last_name": "Player",
        "session_id": "test-session-123",
        "score": 0,
        "answers": [],
        "joined_at": "2024-01-01T00:00:00Z"
    }

@pytest.fixture
def api_base_urls():
    """Base URLs for different services."""
    return {
        "game_engine": "http://localhost:8001",
        "session_manager": "http://localhost:8002",
        "user_manager": "http://localhost:8003",
        "analytics": "http://localhost:8004",
        "notifications": "http://localhost:8005"
    }

@pytest.fixture
def mock_qr_generator():
    """Mock QR code generator."""
    qr_mock = MagicMock()
    qr_mock.generate_qr_code.return_value = b"fake_qr_code_data"
    return qr_mock

@pytest.fixture
def mock_file_handler():
    """Mock file handler for game pack operations."""
    file_mock = AsyncMock()
    file_mock.save_file.return_value = "/tmp/test_file.json"
    file_mock.load_file.return_value = {"test": "data"}
    file_mock.validate_file.return_value = True
    return file_mock

class MockMessage:
    """Mock Telegram message for testing."""
    def __init__(self, text="", user_id=123456789, chat_id=123456789, message_id=1):
        self.text = text
        self.message_id = message_id
        self.from_user = MagicMock()
        self.from_user.id = user_id
        self.from_user.username = "test_user"
        self.from_user.first_name = "Test"
        self.from_user.last_name = "User"
        self.chat = MagicMock()
        self.chat.id = chat_id
        self.chat.type = "private"
        self.document = None
        self.photo = None

@pytest.fixture
def mock_message():
    """Mock Telegram message."""
    return MockMessage()

class MockCallbackQuery:
    """Mock Telegram callback query for testing."""
    def __init__(self, data="", user_id=123456789, message_id=1):
        self.data = data
        self.id = "test_callback_123"
        self.from_user = MagicMock()
        self.from_user.id = user_id
        self.from_user.username = "test_user"
        self.message = MockMessage(user_id=user_id, message_id=message_id)

@pytest.fixture
def mock_callback_query():
    """Mock Telegram callback query."""
    return MockCallbackQuery()

# Performance testing fixtures
@pytest.fixture
def performance_config():
    """Configuration for performance tests."""
    return {
        "concurrent_users": 10,
        "requests_per_user": 100,
        "ramp_up_time": 5,
        "test_duration": 60
    }

# Database cleanup
@pytest.fixture(autouse=True)
def cleanup_test_data():
    """Clean up test data after each test."""
    yield
    # Cleanup logic here if needed
    pass