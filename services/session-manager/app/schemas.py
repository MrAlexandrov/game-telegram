"""
Session Manager Service - Pydantic Schemas
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid


class SessionBase(BaseModel):
    """Base session schema"""
    title: str = Field(..., description="Session title")
    description: Optional[str] = Field(None, description="Session description")
    max_players: int = Field(50, description="Maximum number of players")
    allow_late_join: bool = Field(True, description="Allow players to join after start")
    question_time_limit: int = Field(30, description="Time limit per question in seconds")


class SessionCreate(SessionBase):
    """Schema for creating a session"""
    game_id: uuid.UUID = Field(..., description="Game ID")
    admin_id: uuid.UUID = Field(..., description="Admin user ID")


class SessionUpdate(BaseModel):
    """Schema for updating a session"""
    title: Optional[str] = None
    description: Optional[str] = None
    max_players: Optional[int] = None
    allow_late_join: Optional[bool] = None
    question_time_limit: Optional[int] = None
    status: Optional[str] = None


class SessionResponse(SessionBase):
    """Schema for session response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    game_id: uuid.UUID
    admin_id: uuid.UUID
    session_code: str
    status: str
    current_question_index: int
    current_question_id: Optional[uuid.UUID]
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class ParticipantBase(BaseModel):
    """Base participant schema"""
    display_name: str = Field(..., description="Player display name")
    avatar_url: Optional[str] = Field(None, description="Player avatar URL")


class ParticipantJoin(ParticipantBase):
    """Schema for joining a session"""
    user_id: uuid.UUID = Field(..., description="User ID")


class ParticipantResponse(ParticipantBase):
    """Schema for participant response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    session_id: uuid.UUID
    user_id: uuid.UUID
    score: int
    is_active: bool
    is_connected: bool
    joined_at: datetime
    last_seen: datetime


class AnswerSubmit(BaseModel):
    """Schema for submitting an answer"""
    question_id: uuid.UUID = Field(..., description="Question ID")
    question_index: int = Field(..., description="Question index")
    answer_text: str = Field(..., description="Answer text")
    time_taken: Optional[float] = Field(None, description="Time taken in seconds")


class AnswerValidation(BaseModel):
    """Schema for answer validation"""
    is_correct: bool = Field(..., description="Whether the answer is correct")
    points_earned: int = Field(0, description="Points earned")
    validation_notes: Optional[str] = Field(None, description="Validation notes")


class AnswerResponse(BaseModel):
    """Schema for answer response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    session_id: uuid.UUID
    participant_id: uuid.UUID
    question_id: uuid.UUID
    question_index: int
    answer_text: str
    is_correct: Optional[bool]
    points_earned: int
    time_taken: Optional[float]
    answered_at: datetime
    validated_at: Optional[datetime]


class SessionStateUpdate(BaseModel):
    """Schema for session state updates"""
    current_state: Dict[str, Any] = Field(..., description="Current session state")
    game_state: Optional[Dict[str, Any]] = Field(None, description="Game-specific state")


class SessionEventCreate(BaseModel):
    """Schema for creating session events"""
    event_type: str = Field(..., description="Event type")
    event_data: Optional[Dict[str, Any]] = Field(None, description="Event data")
    actor_id: Optional[uuid.UUID] = Field(None, description="Actor user ID")
    actor_type: Optional[str] = Field(None, description="Actor type")


class SessionEventResponse(BaseModel):
    """Schema for session event response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    session_id: uuid.UUID
    event_type: str
    event_data: Optional[Dict[str, Any]]
    actor_id: Optional[uuid.UUID]
    actor_type: Optional[str]
    created_at: datetime


class SessionResults(BaseModel):
    """Schema for session results"""
    session_id: uuid.UUID
    total_questions: int
    total_participants: int
    completion_rate: float
    average_score: float
    top_players: List[Dict[str, Any]]
    question_stats: List[Dict[str, Any]]


class WebSocketMessage(BaseModel):
    """Schema for WebSocket messages"""
    type: str = Field(..., description="Message type")
    data: Dict[str, Any] = Field(..., description="Message data")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SessionJoinResponse(BaseModel):
    """Schema for session join response"""
    success: bool
    participant_id: Optional[uuid.UUID] = None
    session_info: Optional[SessionResponse] = None
    error: Optional[str] = None


class QuestionStartResponse(BaseModel):
    """Schema for question start response"""
    question_id: uuid.UUID
    question_index: int
    question_data: Dict[str, Any]
    time_limit: int
    start_time: datetime


class QuestionEndResponse(BaseModel):
    """Schema for question end response"""
    question_id: uuid.UUID
    question_index: int
    correct_answer: Optional[Dict[str, Any]]
    results: List[Dict[str, Any]]
    next_question_in: Optional[int] = None


class SessionStatusResponse(BaseModel):
    """Schema for session status response"""
    session: SessionResponse
    participants: List[ParticipantResponse]
    current_question: Optional[Dict[str, Any]]
    leaderboard: List[Dict[str, Any]]


class HealthResponse(BaseModel):
    """Schema for health check response"""
    status: str
    timestamp: datetime
    version: str
    database: str
    redis: str
    active_sessions: int
    connected_players: int