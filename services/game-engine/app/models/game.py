"""
Game Engine Service - Game Models
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base


class Game(Base):
    """Game model"""
    __tablename__ = "games"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    game_type = Column(String(50), nullable=False)  # quiz, family_feud, etc.
    difficulty = Column(String(20), default="medium")
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class GamePack(Base):
    """Game pack model"""
    __tablename__ = "game_packs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    game_type = Column(String(50), nullable=False)
    pack_data = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Question(Base):
    """Question model"""
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50), default="multiple_choice")
    difficulty = Column(String(20), default="medium")
    points = Column(Integer, default=10)
    time_limit = Column(Integer, default=30)  # seconds
    extra_data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Answer(Base):
    """Answer model"""
    __tablename__ = "answers"
    
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    answer_text = Column(Text, nullable=False)
    is_correct = Column(Boolean, default=False)
    points = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class MediaFile(Base):
    """Media file model"""
    __tablename__ = "media_files"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)  # image, audio, video
    file_size = Column(Integer, nullable=False)
    file_path = Column(String(500), nullable=False)
    mime_type = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())