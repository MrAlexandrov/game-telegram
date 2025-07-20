"""
Shared Base Models
Common data models used across all services
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


class GameType(str, Enum):
    """Supported game types"""
    QUIZ = "quiz"
    FAMILY_FEUD = "family_feud"
    CUSTOM = "custom"


class QuestionType(str, Enum):
    """Question types"""
    MULTIPLE_CHOICE = "multiple_choice"
    TEXT_INPUT = "text_input"
    MEDIA_QUESTION = "media_question"
    SURVEY_QUESTION = "survey_question"


class SessionStatus(str, Enum):
    """Game session statuses"""
    WAITING = "waiting"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class UserRole(str, Enum):
    """User roles"""
    ADMIN = "admin"
    PLAYER = "player"


class BaseResponse(BaseModel):
    """Base response model"""
    success: bool = True
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class UserBase(BaseModel):
    """Base user model"""
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: UserRole = UserRole.PLAYER
    language_code: Optional[str] = "en"


class GameBase(BaseModel):
    """Base game model"""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    game_type: GameType
    config: Dict[str, Any] = {}


class QuestionBase(BaseModel):
    """Base question model"""
    id: str = Field(..., min_length=1, max_length=50)
    order: int = Field(..., ge=1)
    type: QuestionType
    content: Dict[str, Any]
    correct_answers: List[str] = []
    points: int = Field(1, ge=1, le=1000)
    time_limit: int = Field(30, ge=10, le=300)
    requires_validation: bool = False
    explanation: Optional[str] = None


class SessionBase(BaseModel):
    """Base session model"""
    game_id: str
    admin_id: str
    session_code: str = Field(..., min_length=4, max_length=10)
    status: SessionStatus = SessionStatus.WAITING
    max_players: int = Field(50, ge=1, le=100)


class AnswerBase(BaseModel):
    """Base answer model"""
    user_id: str
    question_id: str
    session_id: str
    answer_text: str
    is_correct: Optional[bool] = None
    points_earned: int = 0
    answered_at: datetime = Field(default_factory=datetime.utcnow)
