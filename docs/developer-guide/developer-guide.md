# Developer Guide

## Table of Contents

1. [Getting Started](#getting-started)
2. [Architecture Overview](#architecture-overview)
3. [Development Environment](#development-environment)
4. [Code Structure](#code-structure)
5. [Adding New Features](#adding-new-features)
6. [Creating Game Modules](#creating-game-modules)
7. [Database Design](#database-design)
8. [API Development](#api-development)
9. [Bot Development](#bot-development)
10. [Testing Guidelines](#testing-guidelines)
11. [Performance Optimization](#performance-optimization)
12. [Security Considerations](#security-considerations)
13. [Deployment](#deployment)
14. [Monitoring and Logging](#monitoring-and-logging)
15. [Contributing](#contributing)

## Getting Started

### Prerequisites

- **Python 3.11+**
- **Docker & Docker Compose**
- **Redis 7.0+**
- **PostgreSQL 15+**
- **Node.js 18+** (for frontend tools)
- **Git**

### Quick Setup

```bash
# Clone the repository
git clone https://github.com/your-org/game-telegram.git
cd game-telegram

# Set up environment
cp .env.example .env
# Edit .env with your configuration

# Start services
docker-compose up -d

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start development server
python manage.py runserver
```

### Project Structure

```
game-telegram/
├── services/                 # Microservices
│   ├── admin-bot/           # Admin Telegram bot
│   ├── player-bot/          # Player Telegram bot
│   ├── game-engine/         # Game logic and management
│   ├── session-manager/     # Session and real-time management
│   ├── user-manager/        # User management and authentication
│   ├── analytics-service/   # Analytics and reporting
│   └── notification-service/ # Notifications and messaging
├── shared/                  # Shared libraries
│   ├── models/             # Common data models
│   ├── schemas/            # Pydantic schemas
│   ├── utils/              # Utility functions
│   └── exceptions/         # Custom exceptions
├── game-modules/           # Game type implementations
│   ├── base/              # Base game module
│   ├── quiz/              # Quiz game implementation
│   └── family_feud/       # Family Feud implementation
├── game-packs/            # Game content
├── tests/                 # Test suites
├── docs/                  # Documentation
├── monitoring/            # Monitoring configuration
└── scripts/              # Utility scripts
```

## Architecture Overview

### System Architecture

The system follows a **microservices architecture** with the following key principles:

- **Service Independence**: Each service can be developed, deployed, and scaled independently
- **Event-Driven Communication**: Services communicate via events and message queues
- **API-First Design**: All services expose REST APIs
- **Stateless Services**: Services don't maintain session state (stored in Redis)
- **Horizontal Scalability**: Services can be scaled horizontally

### Service Responsibilities

#### Admin Bot Service
- **Purpose**: Telegram bot for game administrators
- **Responsibilities**:
  - Game creation and management
  - Session control and monitoring
  - Analytics dashboard
  - User management
- **Technology**: Python, aiogram, FastAPI
- **Port**: 8000

#### Player Bot Service
- **Purpose**: Telegram bot for game players
- **Responsibilities**:
  - Player registration and authentication
  - Game participation
  - Answer submission
  - Results viewing
- **Technology**: Python, aiogram, FastAPI
- **Port**: 8001

#### Game Engine Service
- **Purpose**: Core game logic and content management
- **Responsibilities**:
  - Game CRUD operations
  - Game validation and processing
  - Question management
  - Game pack import/export
- **Technology**: Python, FastAPI, SQLAlchemy
- **Port**: 8002

#### Session Manager Service
- **Purpose**: Real-time session management
- **Responsibilities**:
  - Session lifecycle management
  - Player connections
  - Real-time game state
  - WebSocket connections
- **Technology**: Python, FastAPI, WebSockets, Redis
- **Port**: 8003

#### User Manager Service
- **Purpose**: User management and authentication
- **Responsibilities**:
  - User registration and profiles
  - Authentication and authorization
  - User statistics
  - Achievement system
- **Technology**: Python, FastAPI, SQLAlchemy, JWT
- **Port**: 8004

#### Analytics Service
- **Purpose**: Data analytics and reporting
- **Responsibilities**:
  - Game result processing
  - Statistical analysis
  - Leaderboards
  - Performance metrics
- **Technology**: Python, FastAPI, Pandas, SQLAlchemy
- **Port**: 8005

#### Notification Service
- **Purpose**: Centralized notification system
- **Responsibilities**:
  - Push notifications
  - Email notifications
  - Telegram message broadcasting
  - Event-driven notifications
- **Technology**: Python, FastAPI, Celery, Redis
- **Port**: 8006

### Data Flow

```mermaid
graph TD
    A[Admin Bot] --> B[Game Engine]
    B --> C[Session Manager]
    C --> D[Player Bot]
    D --> E[User Manager]
    C --> F[Analytics Service]
    F --> G[Notification Service]
    
    H[Redis] --> C
    I[PostgreSQL] --> B
    I --> E
    I --> F
    
    J[WebSocket] --> C
    K[Message Queue] --> G
```

## Development Environment

### Local Development Setup

#### 1. Environment Configuration

Create `.env` file:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/gamedb
REDIS_URL=redis://localhost:6379/0

# Telegram Bots
ADMIN_BOT_TOKEN=your_admin_bot_token
PLAYER_BOT_TOKEN=your_player_bot_token

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here

# Services
GAME_ENGINE_URL=http://localhost:8002
SESSION_MANAGER_URL=http://localhost:8003
USER_MANAGER_URL=http://localhost:8004
ANALYTICS_URL=http://localhost:8005
NOTIFICATION_URL=http://localhost:8006

# Development
DEBUG=true
LOG_LEVEL=DEBUG
```

#### 2. Database Setup

```bash
# Start PostgreSQL and Redis
docker-compose up -d postgres redis

# Create database
createdb gamedb

# Run migrations
cd services/game-engine
alembic upgrade head

cd ../user-manager
alembic upgrade head
```

#### 3. Service Development

Each service can be run independently:

```bash
# Game Engine
cd services/game-engine
uvicorn app.main:app --reload --port 8002

# Session Manager
cd services/session-manager
uvicorn app.main:app --reload --port 8003

# User Manager
cd services/user-manager
uvicorn app.main:app --reload --port 8004
```

### Development Tools

#### Code Quality

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Code formatting
black .
isort .

# Linting
flake8 .
mypy .

# Security scanning
bandit -r .
```

#### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test categories
pytest -m unit
pytest -m integration
pytest -m e2e
```

## Code Structure

### Service Structure

Each service follows this structure:

```
service-name/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration
│   ├── models.py            # Database models
│   ├── schemas.py           # Pydantic schemas
│   ├── crud.py              # Database operations
│   ├── api/                 # API endpoints
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   └── endpoints.py
│   ├── services/            # Business logic
│   │   ├── __init__.py
│   │   └── service_name.py
│   ├── utils/               # Utilities
│   └── dependencies.py     # FastAPI dependencies
├── tests/
├── alembic/                 # Database migrations
├── Dockerfile
└── requirements.txt
```

### Coding Standards

#### Python Style Guide

Follow **PEP 8** with these additions:

```python
# Import order
import os
import sys
from typing import List, Dict, Optional

import requests
from fastapi import FastAPI, Depends
from sqlalchemy import Column, Integer, String

from app.models import User
from app.schemas import UserCreate
```

#### Naming Conventions

```python
# Classes: PascalCase
class GameEngine:
    pass

# Functions and variables: snake_case
def create_game(game_data: dict) -> Game:
    user_id = game_data.get("user_id")
    return game

# Constants: UPPER_SNAKE_CASE
MAX_PLAYERS = 50
DEFAULT_TIME_LIMIT = 30

# Private methods: _snake_case
def _validate_game_data(self, data: dict) -> bool:
    pass
```

#### Type Hints

Always use type hints:

```python
from typing import List, Dict, Optional, Union
from pydantic import BaseModel

def process_answers(
    answers: List[Dict[str, Union[str, int]]], 
    correct_answers: Dict[str, int]
) -> Dict[str, float]:
    """Process player answers and calculate scores."""
    pass

class GameResult(BaseModel):
    player_id: int
    score: float
    correct_answers: int
    total_questions: int
    completion_time: Optional[int] = None
```

#### Error Handling

```python
from shared.exceptions import GameNotFoundError, ValidationError

async def get_game(game_id: str) -> Game:
    try:
        game = await game_repository.get_by_id(game_id)
        if not game:
            raise GameNotFoundError(f"Game {game_id} not found")
        return game
    except DatabaseError as e:
        logger.error(f"Database error getting game {game_id}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting game {game_id}: {e}")
        raise
```

## Adding New Features

### Feature Development Process

1. **Design Phase**
   - Create feature specification
   - Design API endpoints
   - Plan database changes
   - Consider security implications

2. **Implementation Phase**
   - Create feature branch
   - Implement core logic
   - Add API endpoints
   - Write tests
   - Update documentation

3. **Testing Phase**
   - Unit tests
   - Integration tests
   - Manual testing
   - Performance testing

4. **Review Phase**
   - Code review
   - Security review
   - Documentation review

### Example: Adding a New Game Type

#### 1. Create Game Module

```python
# game-modules/word_game/word_game_module.py
from game_modules.base.game_module import BaseGameModule
from typing import Dict, Any, List

class WordGameModule(BaseGameModule):
    """Word-based game implementation."""
    
    def __init__(self, game_data: Dict[str, Any]):
        super().__init__(game_data)
        self.game_type = "word_game"
        self.words = game_data.get("words", [])
        self.time_limit = game_data.get("settings", {}).get("time_limit", 60)
    
    def initialize(self) -> None:
        """Initialize word game state."""
        self.current_word_index = 0
        self.player_scores = {}
        self.game_state = "waiting"
    
    def get_next_question(self) -> Optional[Dict[str, Any]]:
        """Get next word challenge."""
        if self.current_word_index >= len(self.words):
            return None
            
        word_data = self.words[self.current_word_index]
        return {
            "id": f"word_{self.current_word_index}",
            "type": "word_challenge",
            "scrambled_word": self._scramble_word(word_data["word"]),
            "hint": word_data.get("hint", ""),
            "points": word_data.get("points", 10),
            "time_limit": self.time_limit
        }
    
    def process_answer(self, question_id: str, answer: str, user_id: int) -> Dict[str, Any]:
        """Process word game answer."""
        word_index = int(question_id.split("_")[1])
        correct_word = self.words[word_index]["word"].lower()
        player_answer = answer.strip().lower()
        
        is_correct = player_answer == correct_word
        points = self.words[word_index]["points"] if is_correct else 0
        
        if user_id not in self.player_scores:
            self.player_scores[user_id] = 0
        self.player_scores[user_id] += points
        
        return {
            "correct": is_correct,
            "points": points,
            "correct_answer": self.words[word_index]["word"],
            "player_score": self.player_scores[user_id]
        }
    
    def _scramble_word(self, word: str) -> str:
        """Scramble letters in a word."""
        import random
        letters = list(word)
        random.shuffle(letters)
        return ''.join(letters)
```

#### 2. Register Game Module

```python
# services/game-engine/app/services/module_loader.py
from game_modules.word_game.word_game_module import WordGameModule

GAME_MODULES = {
    "quiz": QuizModule,
    "family_feud": FamilyFeudModule,
    "word_game": WordGameModule,  # Add new module
}

def load_game_module(game_data: Dict[str, Any]) -> BaseGameModule:
    """Load appropriate game module based on game type."""
    game_type = game_data.get("type", "quiz")
    
    if game_type not in GAME_MODULES:
        raise ValueError(f"Unknown game type: {game_type}")
    
    return GAME_MODULES[game_type](game_data)
```

#### 3. Add API Endpoints

```python
# services/game-engine/app/api/v1/word_games.py
from fastapi import APIRouter, Depends, HTTPException
from app.schemas import WordGameCreate, WordGameResponse
from app.services.word_game_service import WordGameService

router = APIRouter(prefix="/word-games", tags=["word-games"])

@router.post("/", response_model=WordGameResponse)
async def create_word_game(
    game_data: WordGameCreate,
    service: WordGameService = Depends()
):
    """Create a new word game."""
    try:
        game = await service.create_word_game(game_data)
        return game
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
```

#### 4. Add Schemas

```python
# services/game-engine/app/schemas/word_game_schemas.py
from pydantic import BaseModel, validator
from typing import List, Optional

class WordData(BaseModel):
    word: str
    hint: Optional[str] = None
    points: int = 10
    
    @validator('word')
    def word_must_be_valid(cls, v):
        if not v or len(v) < 2:
            raise ValueError('Word must be at least 2 characters long')
        return v.strip()

class WordGameCreate(BaseModel):
    title: str
    description: Optional[str] = None
    words: List[WordData]
    settings: Optional[Dict[str, Any]] = {}
    
    @validator('words')
    def must_have_words(cls, v):
        if not v or len(v) < 1:
            raise ValueError('Game must have at least one word')
        return v
```

#### 5. Write Tests

```python
# tests/unit/test_word_game_module.py
import pytest
from game_modules.word_game.word_game_module import WordGameModule

class TestWordGameModule:
    
    def test_word_game_initialization(self):
        """Test word game module initialization."""
        game_data = {
            "id": "word-game-1",
            "type": "word_game",
            "words": [
                {"word": "PYTHON", "hint": "Programming language", "points": 10},
                {"word": "FASTAPI", "hint": "Web framework", "points": 15}
            ],
            "settings": {"time_limit": 45}
        }
        
        module = WordGameModule(game_data)
        module.initialize()
        
        assert module.game_type == "word_game"
        assert len(module.words) == 2
        assert module.time_limit == 45
        assert module.current_word_index == 0
    
    def test_get_next_question(self):
        """Test getting next word challenge."""
        game_data = {
            "words": [{"word": "HELLO", "points": 10}]
        }
        
        module = WordGameModule(game_data)
        module.initialize()
        
        question = module.get_next_question()
        
        assert question is not None
        assert question["type"] == "word_challenge"
        assert "scrambled_word" in question
        assert question["points"] == 10
    
    def test_process_correct_answer(self):
        """Test processing correct answer."""
        game_data = {
            "words": [{"word": "HELLO", "points": 10}]
        }
        
        module = WordGameModule(game_data)
        module.initialize()
        
        result = module.process_answer("word_0", "hello", 123)
        
        assert result["correct"] is True
        assert result["points"] == 10
        assert result["player_score"] == 10
```

## Creating Game Modules

### Base Game Module

All game modules must inherit from `BaseGameModule`:

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

class BaseGameModule(ABC):
    """Base class for all game modules."""
    
    def __init__(self, game_data: Dict[str, Any]):
        self.game_id = game_data.get("id")
        self.title = game_data.get("title")
        self.description = game_data.get("description")
        self.settings = game_data.get("settings", {})
        self.game_type = "base"
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize game state."""
        pass
    
    @abstractmethod
    def get_next_question(self) -> Optional[Dict[str, Any]]:
        """Get next question/challenge."""
        pass
    
    @abstractmethod
    def process_answer(self, question_id: str, answer: Any, user_id: int) -> Dict[str, Any]:
        """Process player answer."""
        pass
    
    @abstractmethod
    def calculate_score(self, answers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate final scores."""
        pass
    
    def is_game_complete(self) -> bool:
        """Check if game is complete."""
        return False
    
    def get_game_state(self) -> Dict[str, Any]:
        """Get current game state."""
        return {
            "game_id": self.game_id,
            "type": self.game_type,
            "status": getattr(self, "game_state", "unknown")
        }
```

### Game Module Guidelines

1. **State Management**
   - Keep game state in memory during active sessions
   - Persist important state to Redis for recovery
   - Clean up state when game ends

2. **Answer Processing**
   - Validate answer format
   - Handle edge cases (empty answers, invalid format)
   - Calculate points consistently
   - Return structured results

3. **Time Management**
   - Respect time limits
   - Handle late answers appropriately
   - Provide time bonuses if configured

4. **Error Handling**
   - Gracefully handle invalid inputs
   - Log errors for debugging
   - Return meaningful error messages

## Database Design

### Database Schema

#### Games Table

```sql
CREATE TABLE games (
    id VARCHAR(255) PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    type VARCHAR(100) NOT NULL,
    category VARCHAR(100),
    created_by INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    settings JSONB DEFAULT '{}',
    questions JSONB DEFAULT '[]',
    tags TEXT[],
    is_active BOOLEAN DEFAULT true,
    
    INDEX idx_games_type (type),
    INDEX idx_games_category (category),
    INDEX idx_games_created_by (created_by),
    INDEX idx_games_created_at (created_at)
);
```

#### Users Table

```sql
CREATE TABLE users (
    user_id BIGINT PRIMARY KEY,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    language_code VARCHAR(10) DEFAULT 'en',
    is_bot BOOLEAN DEFAULT false,
    is_premium BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    settings JSONB DEFAULT '{}',
    
    INDEX idx_users_username (username),
    INDEX idx_users_created_at (created_at),
    INDEX idx_users_last_active (last_active)
);
```

#### Game Results Table

```sql
CREATE TABLE game_results (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    user_id BIGINT NOT NULL,
    game_id VARCHAR(255) NOT NULL,
    score INTEGER NOT NULL DEFAULT 0,
    max_score INTEGER NOT NULL DEFAULT 0,
    correct_answers INTEGER NOT NULL DEFAULT 0,
    total_questions INTEGER NOT NULL DEFAULT 0,
    completion_time INTEGER, -- seconds
    answers JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (game_id) REFERENCES games(id),
    
    INDEX idx_results_session (session_id),
    INDEX idx_results_user (user_id),
    INDEX idx_results_game (game_id),
    INDEX idx_results_created_at (created_at)
);
```

### Database Migrations

Use Alembic for database migrations:

```python
# alembic/versions/001_create_games_table.py
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    op.create_table(
        'games',
        sa.Column('id', sa.String(255), primary_key=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('type', sa.String(100), nullable=False),
        sa.Column('category', sa.String(100)),
        sa.Column('created_by', sa.Integer, nullable=False),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP, server_default=sa.func.now()),
        sa.Column('settings', postgresql.JSONB, server_default='{}'),
        sa.Column('questions', postgresql.JSONB, server_default='[]'),
        sa.Column('tags', postgresql.ARRAY(sa.Text)),
        sa.Column('is_active', sa.Boolean, server_default='true'),
    )
    
    op.create_index('idx_games_type', 'games', ['type'])
    op.create_index('idx_games_category', 'games', ['category'])
    op.create_index('idx_games_created_by', 'games', ['created_by'])

def downgrade():
    op.drop_table('games')
```

### Database Best Practices

1. **Indexing Strategy**
   - Index frequently queried columns
   - Use composite indexes for multi-column queries
   - Monitor query performance

2. **JSONB Usage**
   - Use JSONB for flexible schema data
   - Index JSONB fields when needed
   - Validate JSONB structure in application

3. **Data Integrity**
   - Use foreign key constraints
   - Implement proper validation
   - Handle constraint violations gracefully

## API Development

### FastAPI Best Practices

#### Application Structure

```python
# app/main.py
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import games, sessions, users
from app.core.config import settings

app = FastAPI(
    title="Game Engine API",
    description="API for managing games and sessions",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(games.router, prefix="/api/v1")
app.include_router(sessions.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}
```

#### Dependency Injection

```python
# app/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.auth_service import AuthService

security = HTTPBearer()

async def get_current_user(
    token: str = Depends(security),
    db: Session = Depends(get_db)
):
    """Get current authenticated user."""
    try:
        auth_service = AuthService(db)
        user = await auth_service.get_user_from_token(token.credentials)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

async def get_admin_user(
    current_user = Depends(get_current_user)
):
    """Ensure current user is admin."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user
```

#### Error Handling

```python
# app/exceptions.py
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging

logger = logging.getLogger(__name__)

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "success": false,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": exc.errors()
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    )

async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": false,
            "error": {
                "code": "HTTP_ERROR",
                "message": exc.detail
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    )
```

### API Documentation

Use OpenAPI/Swagger for API documentation:

```python
from fastapi import FastAPI
from pydantic import BaseModel

class GameResponse(BaseModel):
    """Game response model."""
    id: str
    title: str
    description: Optional[str] = None
    type: str
    created_at: datetime
    
    class Config:
        schema_extra = {
            "example": {
                "id": "game_123456789",
                "title": "History Quiz",
                "description": "A quiz about world history",
                "type": "quiz",
                "created_at": "2024-01-01T12:00:00Z"
            }
        }

@app.post("/games", response_model=GameResponse, status_code=201)
async def create_game(
    game_data: GameCreate,
    current_user = Depends(get_current_user)
):
    """
    Create a new game.
    
    - **title**: Game title (required)
    - **description**: Game description (optional)
    - **type**: Game type (quiz, family_feud, etc.)
    - **questions**: List of game questions
    
    Returns the created game with generated ID.
    """
    pass
```

## Bot Development

### Telegram Bot Structure

#### Bot Application

```python
# services/admin-bot/app/main.py
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from app.config import settings
from app.handlers import register_handlers
from app.middlewares import setup_middlewares

async def main():
    """Main bot application."""
    # Initialize bot and dispatcher
    bot = Bot(token=settings.BOT_TOKEN, parse_mode="HTML")
    storage = RedisStorage2(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB
    )
    dp = Dispatcher(bot, storage=storage)
    
    # Setup middlewares
    setup_middlewares(dp)
    
    # Register handlers
    register_handlers(dp)
    
    # Start polling
    try:
        await dp.start_polling()
    finally:
        await bot.session.close()
        await storage.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
```

#### Handler Organization

```python
# app/handlers/game_handlers.py
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from app.services.api_client import APIClient
from app.keyboards.game_keyboards import get_game_menu_keyboard

class GameCreationStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_questions = State()
    waiting_for_confirmation = State()

async def start_game_creation(message: types.Message, state: FSMContext):
    """Start game creation process."""
    await message.answer(
        "🎮 <b>Создание новой игры</b>\n\n"
        "Введите название игры:",
        parse_mode="HTML"
    )
    await GameCreationStates.waiting_for_title.set()

async def process_game_title(message: types.Message, state: FSMContext):
    """Process game title input."""
    title = message.text.strip()
    
    if len(title) < 3:
        await message.answer("❌ Название должно содержать минимум 3 символа")
        return
    
    await state.update_data(title=title)
    await message.answer(
        f"✅ Название: <b>{title}</b>\n\n"
        "Теперь введите описание игры:",
        parse_mode="HTML"
    )

    await GameCreationStates.waiting_for_description.set()

async def process_game_description(message: types.Message, state: FSMContext):
    """Process game description input."""
    description = message.text.strip()
    await state.update_data(description=description)
    
    keyboard = get_game_menu_keyboard()
    await message.answer(
        f"✅ Описание сохранено\n\n"
        "Выберите тип игры:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

def register_game_handlers(dp: Dispatcher):
    """Register game-related handlers."""
    dp.register_message_handler(
        start_game_creation,
        commands=['create_game'],
        state="*"
    )
    dp.register_message_handler(
        process_game_title,
        state=GameCreationStates.waiting_for_title
    )
    dp.register_message_handler(
        process_game_description,
        state=GameCreationStates.waiting_for_description
    )
```

#### Keyboard Management

```python
# app/keyboards/game_keyboards.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_game_menu_keyboard() -> InlineKeyboardMarkup:
    """Get game menu keyboard."""
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    buttons = [
        InlineKeyboardButton("🧠 Викторина", callback_data="game_type:quiz"),
        InlineKeyboardButton("👨‍👩‍👧‍👦 Семейная вражда", callback_data="game_type:family_feud"),
        InlineKeyboardButton("📝 Словесная игра", callback_data="game_type:word_game"),
        InlineKeyboardButton("🎯 Пользовательская", callback_data="game_type:custom"),
    ]
    
    keyboard.add(*buttons)
    keyboard.add(InlineKeyboardButton("❌ Отмена", callback_data="cancel"))
    
    return keyboard

def get_admin_menu_keyboard() -> ReplyKeyboardMarkup:
    """Get admin main menu keyboard."""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    buttons = [
        KeyboardButton("🎮 Игры"),
        KeyboardButton("📊 Сессии"),
        KeyboardButton("👥 Пользователи"),
        KeyboardButton("📈 Аналитика"),
        KeyboardButton("⚙️ Настройки"),
        KeyboardButton("ℹ️ Помощь"),
    ]
    
    keyboard.add(*buttons)
    return keyboard
```

#### Middleware

```python
# app/middlewares/auth_middleware.py
from aiogram import types
from aiogram.dispatcher.middlewares import BaseMiddleware
from app.services.api_client import APIClient

class AuthMiddleware(BaseMiddleware):
    """Authentication middleware."""
    
    def __init__(self, api_client: APIClient):
        self.api_client = api_client
        super().__init__()
    
    async def on_process_message(self, message: types.Message, data: dict):
        """Process incoming message."""
        user = message.from_user
        
        # Register/update user
        user_data = {
            "user_id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "language_code": user.language_code
        }
        
        try:
            await self.api_client.register_user(user_data)
        except Exception as e:
            # Log error but don't block message processing
            logging.error(f"Failed to register user {user.id}: {e}")
        
        data['user'] = user
```

## Testing Guidelines

### Testing Strategy

#### Test Pyramid

```
    /\
   /  \     E2E Tests (Few)
  /____\    
 /      \   Integration Tests (Some)
/__________\ Unit Tests (Many)
```

#### Test Categories

1. **Unit Tests** (70%)
   - Test individual functions/methods
   - Mock external dependencies
   - Fast execution
   - High coverage

2. **Integration Tests** (20%)
   - Test service interactions
   - Use test database
   - Test API endpoints
   - Test bot handlers

3. **End-to-End Tests** (10%)
   - Test complete user flows
   - Use staging environment
   - Test critical paths
   - Slower execution

### Writing Tests

#### Unit Test Example

```python
# tests/unit/test_game_service.py
import pytest
from unittest.mock import Mock, AsyncMock
from app.services.game_service import GameService
from app.models import Game
from shared.exceptions import GameNotFoundError

class TestGameService:
    
    @pytest.fixture
    def mock_repository(self):
        """Mock game repository."""
        return Mock()
    
    @pytest.fixture
    def game_service(self, mock_repository):
        """Game service with mocked repository."""
        return GameService(repository=mock_repository)
    
    @pytest.mark.asyncio
    async def test_get_game_success(self, game_service, mock_repository):
        """Test successful game retrieval."""
        # Arrange
        game_id = "test-game-123"
        expected_game = Game(id=game_id, title="Test Game")
        mock_repository.get_by_id = AsyncMock(return_value=expected_game)
        
        # Act
        result = await game_service.get_game(game_id)
        
        # Assert
        assert result == expected_game
        mock_repository.get_by_id.assert_called_once_with(game_id)
    
    @pytest.mark.asyncio
    async def test_get_game_not_found(self, game_service, mock_repository):
        """Test game not found scenario."""
        # Arrange
        game_id = "nonexistent-game"
        mock_repository.get_by_id = AsyncMock(return_value=None)
        
        # Act & Assert
        with pytest.raises(GameNotFoundError):
            await game_service.get_game(game_id)
    
    @pytest.mark.asyncio
    async def test_create_game_validation(self, game_service):
        """Test game creation with invalid data."""
        # Arrange
        invalid_game_data = {
            "title": "",  # Invalid: empty title
            "type": "quiz"
        }
        
        # Act & Assert
        with pytest.raises(ValidationError):
            await game_service.create_game(invalid_game_data)
```

#### Integration Test Example

```python
# tests/integration/test_game_api.py
import pytest
from httpx import AsyncClient
from app.main import app

class TestGameAPI:
    
    @pytest.mark.asyncio
    async def test_create_game_endpoint(self, client: AsyncClient, auth_headers):
        """Test game creation endpoint."""
        # Arrange
        game_data = {
            "title": "Integration Test Game",
            "description": "A test game for integration testing",
            "type": "quiz",
            "questions": [
                {
                    "text": "What is 2+2?",
                    "type": "single_choice",
                    "options": ["3", "4", "5"],
                    "correct_answer": 1
                }
            ]
        }
        
        # Act
        response = await client.post(
            "/api/v1/games",
            json=game_data,
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 201
        result = response.json()
        assert result["success"] is True
        assert result["data"]["title"] == game_data["title"]
        assert "id" in result["data"]
    
    @pytest.mark.asyncio
    async def test_get_games_endpoint(self, client: AsyncClient, auth_headers):
        """Test games listing endpoint."""
        # Act
        response = await client.get(
            "/api/v1/games",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "data" in result
        assert isinstance(result["data"], list)
```

### Test Configuration

```python
# tests/conftest.py
import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import get_db, Base
from app.config import settings

# Test database
TEST_DATABASE_URL = "postgresql://test:test@localhost:5432/test_gamedb"

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_db():
    """Create test database."""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )
    
    yield TestingSessionLocal
    
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
async def client(test_db):
    """Create test client."""
    def override_get_db():
        try:
            db = test_db()
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def auth_headers():
    """Get authentication headers for tests."""
    return {"Authorization": "Bearer test-token"}
```

## Performance Optimization

### Database Optimization

#### Query Optimization

```python
# Efficient queries with proper joins
async def get_games_with_results(user_id: int) -> List[GameWithResults]:
    """Get games with user results efficiently."""
    query = (
        select(Game, GameResult)
        .outerjoin(GameResult, and_(
            Game.id == GameResult.game_id,
            GameResult.user_id == user_id
        ))
        .options(
            selectinload(Game.questions),
            selectinload(Game.tags)
        )
        .where(Game.is_active == True)
        .order_by(Game.created_at.desc())
    )
    
    result = await db.execute(query)
    return result.all()

# Use database indexes effectively
class Game(Base):
    __tablename__ = "games"
    
    id = Column(String(255), primary_key=True)
    title = Column(String(500), nullable=False)
    type = Column(String(100), nullable=False, index=True)
    category = Column(String(100), index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Composite index for common queries
    __table_args__ = (
        Index('idx_games_type_category', 'type', 'category'),
        Index('idx_games_active_created', 'is_active', 'created_at'),
    )
```

#### Connection Pooling

```python
# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False
)
```

### Caching Strategy

#### Redis Caching

```python
# app/services/cache_service.py
import json
import redis
from typing import Any, Optional
from app.config import settings

class CacheService:
    """Redis-based caching service."""
    
    def __init__(self):
        self.redis = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            value = self.redis.get(key)
            return json.loads(value) if value else None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache."""
        try:
            serialized = json.dumps(value, default=str)
            return self.redis.setex(key, ttl, serialized)
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        try:
            return bool(self.redis.delete(key))
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False

# Usage in services
class GameService:
    def __init__(self, cache: CacheService):
        self.cache = cache
    
    async def get_game(self, game_id: str) -> Game:
        """Get game with caching."""
        cache_key = f"game:{game_id}"
        
        # Try cache first
        cached_game = await self.cache.get(cache_key)
        if cached_game:
            return Game(**cached_game)
        
        # Get from database
        game = await self.repository.get_by_id(game_id)
        if game:
            # Cache for 1 hour
            await self.cache.set(cache_key, game.dict(), ttl=3600)
        
        return game
```

### API Performance

#### Response Optimization

```python
# Use response models to control serialization
from pydantic import BaseModel
from typing import List, Optional

class GameListResponse(BaseModel):
    """Optimized response for game listing."""
    id: str
    title: str
    type: str
    created_at: datetime
    # Exclude heavy fields like questions, settings

class GameDetailResponse(BaseModel):
    """Full response for game details."""
    id: str
    title: str
    description: Optional[str]
    type: str
    questions: List[dict]
    settings: dict
    created_at: datetime

@router.get("/games", response_model=List[GameListResponse])
async def list_games():
    """List games with minimal data."""
    pass

@router.get("/games/{game_id}", response_model=GameDetailResponse)
async def get_game(game_id: str):
    """Get full game details."""
    pass
```

#### Async Processing

```python
# Use background tasks for heavy operations
from fastapi import BackgroundTasks
from app.services.analytics_service import AnalyticsService

@router.post("/games/{game_id}/complete")
async def complete_game(
    game_id: str,
    results: GameResults,
    background_tasks: BackgroundTasks,
    analytics: AnalyticsService = Depends()
):
    """Complete game and process results."""
    # Save results immediately
    saved_results = await save_game_results(results)
    
    # Process analytics in background
    background_tasks.add_task(
        analytics.process_game_completion,
        game_id,
        results
    )
    
    return {"success": True, "results": saved_results}
```

## Security Considerations

### Authentication & Authorization

#### JWT Implementation

```python
# app/services/auth_service.py
import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
from app.config import settings

class AuthService:
    """Authentication service."""
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.secret_key = settings.JWT_SECRET
        self.algorithm = "HS256"
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """Create JWT access token."""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=24)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[dict]:
        """Verify JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.PyJWTError:
            return None
    
    def hash_password(self, password: str) -> str:
        """Hash password."""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password."""
        return self.pwd_context.verify(plain_password, hashed_password)
```

#### Rate Limiting

```python
# app/middlewares/rate_limit.py
import time
from collections import defaultdict
from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware."""
    
    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients = defaultdict(list)
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting."""
        client_ip = request.client.host
        now = time.time()
        
        # Clean old requests
        self.clients[client_ip] = [
            req_time for req_time in self.clients[client_ip]
            if now - req_time < self.period
        ]
        
        # Check rate limit
        if len(self.clients[client_ip]) >= self.calls:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded"
            )
        
        # Add current request
        self.clients[client_ip].append(now)
        
        response = await call_next(request)
        return response
```

### Input Validation

#### Comprehensive Validation

```python
# app/schemas/validation.py
from pydantic import BaseModel, validator, Field
from typing import List, Optional
import re

class GameCreate(BaseModel):
    """Game creation schema with validation."""
    title: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    type: str = Field(..., regex="^(quiz|family_feud|word_game)$")
    questions: List[dict] = Field(..., min_items=1, max_items=100)
    
    @validator('title')
    def title_must_be_clean(cls, v):
        """Validate title doesn't contain harmful content."""
        if re.search(r'[<>"\']', v):
            raise ValueError('Title contains invalid characters')
        return v.strip()
    
    @validator('questions')
    def questions_must_be_valid(cls, v):
        """Validate questions structure."""
        for i, question in enumerate(v):
            if not isinstance(question, dict):
                raise ValueError(f'Question {i} must be an object')
            
            if 'text' not in question or not question['text'].strip():
                raise ValueError(f'Question {i} must have text')
            
            if len(question['text']) > 500:
                raise ValueError(f'Question {i} text too long')
        
        return v

class UserInput(BaseModel):
    """User input validation."""
    answer: str = Field(..., max_length=1000)
    
    @validator('answer')
    def sanitize_answer(cls, v):
        """Sanitize user answer."""
        # Remove potentially harmful content
        sanitized = re.sub(r'[<>"\']', '', v)
        return sanitized.strip()
```

### SQL Injection Prevention

```python
# Always use parameterized queries
from sqlalchemy import text

# WRONG - vulnerable to SQL injection
async def get_user_games_wrong(user_id: str):
    query = f"SELECT * FROM games WHERE created_by = {user_id}"
    return await db.execute(query)

# CORRECT - parameterized query
async def get_user_games_correct(user_id: int):
    query = text("SELECT * FROM games WHERE created_by = :user_id")
    return await db.execute(query, {"user_id": user_id})

# BEST - use ORM
async def get_user_games_orm(user_id: int):
    return await db.query(Game).filter(Game.created_by == user_id).all()
```

## Deployment

### Docker Configuration

#### Multi-stage Dockerfile

```dockerfile
# services/game-engine/Dockerfile
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Copy Python dependencies
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
USER app

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

EXPOSE 8002

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
```

#### Docker Compose

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: gamedb
      POSTGRES_USER: gameuser
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - game-network
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    networks:
      - game-network
    restart: unless-stopped

  game-engine:
    build:
      context: ./services/game-engine
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql://gameuser:${POSTGRES_PASSWORD}@postgres:5432/gamedb
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    networks:
      - game-network
    restart: unless-stopped
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - game-engine
    networks:
      - game-network
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:

networks:
  game-network:
    driver: bridge
```

### Kubernetes Deployment

```yaml
# k8s/game-engine-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: game-engine
  labels:
    app: game-engine
spec:
  replicas: 3
  selector:
    matchLabels:
      app: game-engine
  template:
    metadata:
      labels:
        app: game-engine
    spec:
      containers:
      - name: game-engine
        image: game-telegram/game-engine:latest
        ports:
        - containerPort: 8002
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: database-url
        - name: REDIS_URL
          value: "redis://redis-service:6379/0"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8002
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8002
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: game-engine-service
spec:
  selector:
    app: game-engine
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8002
  type: ClusterIP
```

## Monitoring and Logging

### Logging Configuration

```python
# app/logging_config.py
import logging
import sys
from pythonjsonlogger import jsonlogger

def setup_logging():
    """Setup structured logging."""
    
    # Create formatter
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # File handler
    file_handler = logging.FileHandler('app.log')
    file_handler.setFormatter(formatter)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Disable noisy loggers
    logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

# Usage in application
import logging
logger = logging.getLogger(__name__)

async def create_game(game_data: dict):
    """Create game with logging."""
    logger.info("Creating game", extra={
        "game_type": game_data.get("type"),
        "user_id": game_data.get("created_by"),
        "title": game_data.get("title")
    })
    
    try:
        game = await game_service.create(game_data)
        logger.info("Game created successfully", extra={
            "game_id": game.id,
            "user_id": game_data.get("created_by")
        })
        return game
    except Exception as e:
        logger.error("Failed to create game", extra={
            "error": str(e),
            "user_id": game_data.get("created_by"),
            "game_data": game_data
        })
        raise
```

### Health Checks

```python
# app/health.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.redis_service import RedisService

router = APIRouter()

@router.get("/health")
async def health_check(
    db: Session = Depends(get_db),
    redis: RedisService = Depends()
):
    """Comprehensive health check."""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }
    
    # Database check
    try:
        db.execute("SELECT 1")
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["checks"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Redis check
    try:
        await redis.ping()
        health_status["checks"]["redis"] = "healthy"
    except Exception as e:
        health_status["checks"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # External services check
    try:
        # Check other services
        health_status["checks"]["external_services"] = "healthy"
    except Exception as e:
        health_status["checks"]["external_services"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    status_code = 200 if health_status["status"] == "healthy" else 503
    return JSONResponse(content=health_status, status_code=status_code)
```

### Metrics Collection

```python
# app/metrics.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import Request, Response
import time

# Metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

ACTIVE_GAMES = Gauge(
    'active_games_total',
    'Number of active games'
)

ACTIVE_SESSIONS = Gauge(
    'active_sessions_total',
    'Number of active sessions'
)

async def metrics_middleware(request: Request, call_next):
    """Metrics collection middleware."""
    start_time = time.time()
    
    response = await call_next(request)
    
    # Record metrics
    duration = time.time() - start_time
    REQUEST_DURATION.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    return response

@router.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint."""
    return Response(
        generate_latest(),
        media_type="text/plain"
    )
```

## Contributing

### Development Workflow

1. **Fork and Clone**
   ```bash
   git clone https://github.com/your-username/game-telegram.git
   cd game-telegram
   ```

2. **Create Feature Branch**
   ```bash
   git checkout -b feature/new-game-type
   ```

3. **Make Changes**
   - Follow coding standards
   - Write tests
   - Update documentation

4. **Test Changes**
   ```bash
   pytest
   flake8 .
   mypy .
   ```

5. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: add new word game type"
   ```

6. **Push and Create PR**
   ```bash
   git push origin feature/new-game-type
   # Create pull request on GitHub
   ```

### Code Review Guidelines

1. **Code Quality**
   - Follow PEP 8 style guide
   - Use type hints
   - Write clear docstrings
   - Handle errors appropriately

2. **Testing**
   - Write unit tests for new functions
   - Add integration tests for new endpoints
   - Ensure test coverage > 80%

3. **Documentation**
   - Update API documentation
   - Add code comments for complex logic
   - Update user guides if needed

4. **Security

**
   - Review for security vulnerabilities
   - Check input validation
   - Verify authentication/authorization
   - Test for common attacks (SQL injection, XSS)

### Pull Request Template

```markdown
## Description
Brief description of changes made.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] Performance impact assessed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Code is commented where necessary
- [ ] Documentation updated
- [ ] No new warnings introduced
```

### Release Process

1. **Version Bump**
   ```bash
   # Update version in setup.py, __init__.py, etc.
   git add .
   git commit -m "bump: version 1.2.0"
   ```

2. **Create Release Branch**
   ```bash
   git checkout -b release/1.2.0
   git push origin release/1.2.0
   ```

3. **Testing**
   - Run full test suite
   - Deploy to staging
   - Perform manual testing
   - Load testing if needed

4. **Create Release**
   ```bash
   git tag v1.2.0
   git push origin v1.2.0
   ```

5. **Deploy to Production**
   - Deploy via CI/CD pipeline
   - Monitor deployment
   - Verify functionality

## Troubleshooting

### Common Issues

#### Database Connection Issues

```python
# Check database connectivity
from sqlalchemy import create_engine

try:
    engine = create_engine(DATABASE_URL)
    connection = engine.connect()
    result = connection.execute("SELECT 1")
    print("Database connection successful")
except Exception as e:
    print(f"Database connection failed: {e}")
```

#### Redis Connection Issues

```python
# Check Redis connectivity
import redis

try:
    r = redis.Redis(host='localhost', port=6379, db=0)
    r.ping()
    print("Redis connection successful")
except Exception as e:
    print(f"Redis connection failed: {e}")
```

#### Bot Token Issues

```bash
# Test bot token
curl -X GET "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getMe"
```

#### Service Communication Issues

```python
# Test service endpoints
import httpx

async def test_service_health():
    services = [
        "http://localhost:8002/health",  # Game Engine
        "http://localhost:8003/health",  # Session Manager
        "http://localhost:8004/health",  # User Manager
    ]
    
    async with httpx.AsyncClient() as client:
        for service_url in services:
            try:
                response = await client.get(service_url)
                print(f"{service_url}: {response.status_code}")
            except Exception as e:
                print(f"{service_url}: ERROR - {e}")
```

### Debugging Tips

#### Enable Debug Logging

```python
# app/config.py
import logging

if DEBUG:
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
    logging.getLogger('aiogram').setLevel(logging.DEBUG)
```

#### Database Query Debugging

```python
# Enable SQL query logging
from sqlalchemy import create_engine

engine = create_engine(DATABASE_URL, echo=True)  # Shows all SQL queries
```

#### Bot Message Debugging

```python
# Log all incoming messages
from aiogram import types
import logging

logger = logging.getLogger(__name__)

async def log_all_messages(message: types.Message):
    """Log all incoming messages for debugging."""
    logger.debug(f"Received message: {message.text} from user {message.from_user.id}")
```

### Performance Debugging

#### Database Performance

```sql
-- Check slow queries
SELECT query, mean_time, calls, total_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

-- Check table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

#### Memory Usage

```python
# Monitor memory usage
import psutil
import os

def get_memory_usage():
    """Get current memory usage."""
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    return {
        "rss": memory_info.rss / 1024 / 1024,  # MB
        "vms": memory_info.vms / 1024 / 1024,  # MB
        "percent": process.memory_percent()
    }
```

#### API Response Times

```python
# Add timing middleware
import time
from fastapi import Request

async def timing_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response
```

## FAQ

### General Questions

**Q: How do I add a new game type?**
A: Follow the "Adding New Features" section. Create a new game module inheriting from `BaseGameModule`, register it in the module loader, and add corresponding API endpoints.

**Q: How do I scale the system?**
A: The system is designed for horizontal scaling. You can:
- Add more service replicas
- Use load balancers
- Scale database with read replicas
- Use Redis clustering

**Q: How do I backup the system?**
A: Backup both PostgreSQL database and Redis data:
```bash
# PostgreSQL backup
pg_dump gamedb > backup.sql

# Redis backup
redis-cli BGSAVE
```

### Development Questions

**Q: How do I run tests locally?**
A: Use pytest with the provided configuration:
```bash
pytest tests/ -v --cov=.
```

**Q: How do I add new API endpoints?**
A: Create new router files in `app/api/v1/`, define endpoints with proper schemas, and include the router in main application.

**Q: How do I handle database migrations?**
A: Use Alembic:
```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head
```

### Deployment Questions

**Q: How do I deploy to production?**
A: Use Docker Compose or Kubernetes configurations provided in the deployment documentation.

**Q: How do I monitor the system?**
A: Use the built-in health checks, metrics endpoints, and structured logging. Consider tools like Prometheus, Grafana, and ELK stack.

**Q: How do I handle secrets in production?**
A: Use environment variables, Docker secrets, or Kubernetes secrets. Never commit secrets to version control.

## Resources

### Documentation Links

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [aiogram Documentation](https://docs.aiogram.dev/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Pydantic Documentation](https://pydantic-docs.helpmanual.io/)
- [Redis Documentation](https://redis.io/documentation)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

### Useful Tools

- **Development**: VS Code, PyCharm, Docker Desktop
- **Testing**: pytest, Postman, curl
- **Database**: pgAdmin, DBeaver, Redis CLI
- **Monitoring**: Prometheus, Grafana, Sentry
- **Deployment**: Docker, Kubernetes, Nginx

### Community

- **GitHub Issues**: Report bugs and request features
- **Discussions**: Ask questions and share ideas
- **Wiki**: Additional documentation and examples
- **Slack/Discord**: Real-time community support

---

This developer guide provides comprehensive information for working with the game-telegram project. For additional help, please refer to the API documentation, user guides, or reach out to the development team.

**Last Updated**: January 2024  
**Version**: 1.0.0
