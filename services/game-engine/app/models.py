"""
Game Engine Service - Database Models
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from .models.database import Base


class Game(Base):
    """Game model for storing game templates"""
    
    __tablename__ = "games"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    game_type = Column(String(100), nullable=False, index=True)
    config = Column(JSONB, nullable=False)
    created_by = Column(UUID(as_uuid=True), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    questions = relationship("Question", back_populates="game", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Game(id={self.id}, title={self.title}, game_type={self.game_type})>"


class GamePack(Base):
    """Game pack model for storing uploaded game packs"""
    
    __tablename__ = "game_packs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    version = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    game_type = Column(String(100), nullable=False, index=True)
    pack_data = Column(JSONB, nullable=False)
    file_path = Column(String(500), nullable=True)
    uploaded_by = Column(UUID(as_uuid=True), nullable=False)
    is_validated = Column(Boolean, default=False, nullable=False)
    validation_errors = Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<GamePack(id={self.id}, name={self.name}, game_type={self.game_type})>"


class Question(Base):
    """Question model for storing game questions"""
    
    __tablename__ = "questions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    game_id = Column(UUID(as_uuid=True), ForeignKey("games.id", ondelete="CASCADE"), nullable=False)
    order_index = Column(Integer, nullable=False)
    question_type = Column(String(50), nullable=False)
    content = Column(JSONB, nullable=False)
    media_url = Column(String(500), nullable=True)
    correct_answers = Column(JSONB, nullable=True)
    points = Column(Integer, default=1, nullable=False)
    time_limit = Column(Integer, default=30, nullable=False)  # seconds
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    game = relationship("Game", back_populates="questions")
    
    def __repr__(self):
        return f"<Question(id={self.id}, game_id={self.game_id}, order_index={self.order_index})>"


class Answer(Base):
    """Answer model for storing question answers"""
    
    __tablename__ = "answers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    answer_text = Column(Text, nullable=False)
    is_correct = Column(Boolean, nullable=False)
    points = Column(Integer, default=0, nullable=False)
    explanation = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<Answer(id={self.id}, question_id={self.question_id}, is_correct={self.is_correct})>"


class MediaFile(Base):
    """Media file model for storing game media"""
    
    __tablename__ = "media_files"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    original_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    game_id = Column(UUID(as_uuid=True), ForeignKey("games.id", ondelete="CASCADE"), nullable=True)
    uploaded_by = Column(UUID(as_uuid=True), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<MediaFile(id={self.id}, filename={self.filename}, mime_type={self.mime_type})>"