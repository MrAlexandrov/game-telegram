import pytest
import asyncio
from unittest.mock import AsyncMock
from telegram import Update, Message, Chat, User, CallbackQuery
from telegram.ext import CallbackContext
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base
from queries import DatabaseConnector
from admin_flow import AdminFlow

# -------------------------------
# Фикстуры для моков Telegram API
# -------------------------------
@pytest.fixture
def mock_user():
    """Создаёт мок-пользователя Telegram."""
    return User(id=500261451, first_name="Admin", is_bot=False)

@pytest.fixture
def mock_chat(mock_user):
    """Создаёт мок-чат Telegram."""
    return Chat(id=mock_user.id, type="private")

@pytest.fixture
def mock_message(mock_user, mock_chat):
    """Создаёт мок-сообщение Telegram."""
    return Message(
        message_id=1,
        chat=mock_chat,
        from_user=mock_user,
        text="/start",
        date=None
    )

@pytest.fixture
def mock_update(mock_message):
    """Создаёт мок Update с Message."""
    update = AsyncMock(spec=Update)
    update.message.text = None
    update.effective_user.id = 500261451
    update.callback_query.edit_message_reply_markup = 0
    return update

@pytest.fixture
def mock_context():
    # context = AsyncMock(spec=CallbackContext)
    context = AsyncMock()
    context.bot = AsyncMock()
    context.bot.edit_message_reply_markup = AsyncMock()
    return context

@pytest.fixture
def mock_callback_query(mock_user, mock_chat):
    """Создаёт мок CallbackQuery."""
    return CallbackQuery(
        id="123456",
        from_user=mock_user,
        message=Message(
            message_id=2,
            chat=mock_chat,
            from_user=mock_user,
            text="Кнопка нажата",
            date=None
        ),
        data="mock_callback_data"
    )

@pytest.fixture
def mock_callback_update(mock_callback_query):
    """Создаёт мок Update с CallbackQuery."""
    update = AsyncMock(spec=Update)
    update.callback_query = mock_callback_query
    return update

# -------------------------------
# Фикстуры для тестовой БД
# -------------------------------
@pytest.fixture
def test_db():
    """Создаёт тестовую базу данных в памяти."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    return session

@pytest.fixture
def db_connector(test_db):
    """Создаёт экземпляр DatabaseConnector с тестовой БД."""
    return DatabaseConnector(test_db)

@pytest.fixture
def admin_flow(db_connector):
    """Создаёт экземпляр AdminFlow с тестовой БД."""
    return AdminFlow(db_connector)
