"""
Session Manager Service - Database Models
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from .models.database import Base


class GameSession(Base):
    """Game session model"""
    
    __tablename__ = "game_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    game_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    admin_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    session_code = Column(String(10), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Session state
    status = Column(String(50), default="waiting", nullable=False, index=True)
    current_question_index = Column(Integer, default=0, nullable=False)
    current_question_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Configuration
    max_players = Column(Integer, default=50, nullable=False)
    allow_late_join = Column(Boolean, default=True, nullable=False)
    question_time_limit = Column(Integer, default=30, nullable=False)
    
    # Session data
    session_data = Column(JSONB, nullable=True)
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    participants = relationship("SessionParticipant", back_populates="session", cascade="all, delete-orphan")
    answers = relationship("PlayerAnswer", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<GameSession(id={self.id}, code={self.session_code}, status={self.status})>"


class SessionParticipant(Base):
    """Session participant model"""
    
    __tablename__ = "session_participants"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("game_sessions.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Player info
    display_name = Column(String(255), nullable=False)
    avatar_url = Column(String(500), nullable=True)
    
    # Game state
    score = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_connected = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    last_seen = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session = relationship("GameSession", back_populates="participants")
    answers = relationship("PlayerAnswer", back_populates="participant")
    
    def __repr__(self):
        return f"<SessionParticipant(id={self.id}, user_id={self.user_id}, score={self.score})>"


class PlayerAnswer(Base):
    """Player answer model"""
    
    __tablename__ = "player_answers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("game_sessions.id", ondelete="CASCADE"), nullable=False)
    participant_id = Column(UUID(as_uuid=True), ForeignKey("session_participants.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    question_index = Column(Integer, nullable=False)
    
    # Answer data
    answer_text = Column(Text, nullable=False)
    is_correct = Column(Boolean, nullable=True)  # Null until validated
    points_earned = Column(Integer, default=0, nullable=False)
    time_taken = Column(Float, nullable=True)  # Time in seconds
    
    # Validation
    validated_by = Column(UUID(as_uuid=True), nullable=True)
    validated_at = Column(DateTime(timezone=True), nullable=True)
    validation_notes = Column(Text, nullable=True)
    
    # Timestamps
    answered_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session = relationship("GameSession", back_populates="answers")
    participant = relationship("SessionParticipant", back_populates="answers")
    
    def __repr__(self):
        return f"<PlayerAnswer(id={self.id}, question_id={self.question_id}, is_correct={self.is_correct})>"


class SessionState(Base):
    """Session state model for real-time data"""
    
    __tablename__ = "session_states"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), nullable=False, unique=True, index=True)
    
    # Current state
    current_state = Column(JSONB, nullable=False)
    
    # Question state
    question_start_time = Column(DateTime(timezone=True), nullable=True)
    question_end_time = Column(DateTime(timezone=True), nullable=True)
    
    # Game-specific state
    game_state = Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<SessionState(id={self.id}, session_id={self.session_id})>"


class SessionEvent(Base):
    """Session event log model"""
    
    __tablename__ = "session_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Event data
    event_type = Column(String(100), nullable=False, index=True)
    event_data = Column(JSONB, nullable=True)
    
    # Actor
    actor_id = Column(UUID(as_uuid=True), nullable=True)
    actor_type = Column(String(50), nullable=True)  # admin, player, system
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<SessionEvent(id={self.id}, event_type={self.event_type})>"