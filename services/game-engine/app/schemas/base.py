"""
Game Engine Service - Base Pydantic Schemas
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid


class GameBase(BaseModel):
    """Base game schema"""
    title: str = Field(..., description="Game title")
    description: Optional[str] = Field(None, description="Game description")
    game_type: str = Field(..., description="Game type (quiz, family_feud, etc.)")
    config: Dict[str, Any] = Field(..., description="Game configuration")


class GameCreate(GameBase):
    """Schema for creating a game"""
    created_by: uuid.UUID = Field(..., description="User ID who created the game")


class GameUpdate(BaseModel):
    """Schema for updating a game"""
    title: Optional[str] = None
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class GameResponse(GameBase):
    """Schema for game response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    created_by: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime


class QuestionBase(BaseModel):
    """Base question schema"""
    order_index: int = Field(..., description="Question order in the game")
    question_type: str = Field(..., description="Type of question")
    content: Dict[str, Any] = Field(..., description="Question content")
    media_url: Optional[str] = Field(None, description="Media file URL")
    correct_answers: Optional[List[str]] = Field(None, description="Correct answers")
    points: int = Field(1, description="Points for correct answer")
    time_limit: int = Field(30, description="Time limit in seconds")


class QuestionCreate(QuestionBase):
    """Schema for creating a question"""
    game_id: uuid.UUID = Field(..., description="Game ID")


class QuestionUpdate(BaseModel):
    """Schema for updating a question"""
    order_index: Optional[int] = None
    question_type: Optional[str] = None
    content: Optional[Dict[str, Any]] = None
    media_url: Optional[str] = None
    correct_answers: Optional[List[str]] = None
    points: Optional[int] = None
    time_limit: Optional[int] = None


class QuestionResponse(QuestionBase):
    """Schema for question response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    game_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class GamePackBase(BaseModel):
    """Base game pack schema"""
    name: str = Field(..., description="Game pack name")
    version: str = Field(..., description="Game pack version")
    description: Optional[str] = Field(None, description="Game pack description")
    game_type: str = Field(..., description="Game type")
    pack_data: Dict[str, Any] = Field(..., description="Game pack data")


class GamePackCreate(GamePackBase):
    """Schema for creating a game pack"""
    uploaded_by: uuid.UUID = Field(..., description="User ID who uploaded the pack")
    file_path: Optional[str] = Field(None, description="File path")


class GamePackResponse(GamePackBase):
    """Schema for game pack response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    uploaded_by: uuid.UUID
    file_path: Optional[str]
    is_validated: bool
    validation_errors: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime


class GamePackValidation(BaseModel):
    """Schema for game pack validation"""
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []


class MediaFileBase(BaseModel):
    """Base media file schema"""
    filename: str = Field(..., description="File name")
    original_name: str = Field(..., description="Original file name")
    file_size: int = Field(..., description="File size in bytes")
    mime_type: str = Field(..., description="MIME type")


class MediaFileCreate(MediaFileBase):
    """Schema for creating a media file"""
    file_path: str = Field(..., description="File path")
    game_id: Optional[uuid.UUID] = Field(None, description="Associated game ID")
    uploaded_by: uuid.UUID = Field(..., description="User ID who uploaded the file")


class MediaFileResponse(MediaFileBase):
    """Schema for media file response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    file_path: str
    game_id: Optional[uuid.UUID]
    uploaded_by: uuid.UUID
    created_at: datetime