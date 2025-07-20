"""
Session Manager Service - Session Models
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base
import enum


class SessionStatus(enum.Enum):
    """Session status enumeration"""
    WAITING = "waiting"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class GameSession(Base):
    """Game session model"""
    __tablename__ = "game_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_code = Column(String(10), unique=True, index=True, nullable=False)
    game_id = Column(Integer, nullable=False)
    admin_id = Column(Integer, nullable=False)
    status = Column(Enum(SessionStatus), default=SessionStatus.WAITING)
    max_players = Column(Integer, default=50)
    current_question = Column(Integer, default=0)
    settings = Column(JSON, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class SessionParticipant(Base):
    """Session participant model"""
    __tablename__ = "session_participants"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("game_sessions.id"), nullable=False)
    user_id = Column(Integer, nullable=False)
    nickname = Column(String(100), nullable=False)
    score = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    left_at = Column(DateTime(timezone=True), nullable=True)


class PlayerAnswer(Base):
    """Player answer model"""
    __tablename__ = "player_answers"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("game_sessions.id"), nullable=False)
    participant_id = Column(Integer, ForeignKey("session_participants.id"), nullable=False)
    question_id = Column(Integer, nullable=False)
    answer_text = Column(Text, nullable=True)
    answer_id = Column(Integer, nullable=True)
    is_correct = Column(Boolean, default=False)
    points_earned = Column(Integer, default=0)
    response_time = Column(Integer, nullable=True)  # milliseconds
    answered_at = Column(DateTime(timezone=True), server_default=func.now())


class SessionState(Base):
    """Session state model"""
    __tablename__ = "session_states"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("game_sessions.id"), nullable=False)
    state_data = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SessionEvent(Base):
    """Session event model"""
    __tablename__ = "session_events"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("game_sessions.id"), nullable=False)
    event_type = Column(String(50), nullable=False)
    event_data = Column(JSON, nullable=True)
    user_id = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())