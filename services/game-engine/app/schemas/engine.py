"""
Game Engine Service - Engine-specific Pydantic Schemas
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any
from datetime import datetime
import uuid


class GameEngineRequest(BaseModel):
    """Schema for game engine processing requests"""
    session_id: str = Field(..., description="Game session ID")
    question_id: uuid.UUID = Field(..., description="Question ID")
    game_type: str = Field(..., description="Game type")


class AnswerValidationRequest(BaseModel):
    """Schema for answer validation requests"""
    answer_id: uuid.UUID = Field(..., description="Answer ID")
    is_correct: bool = Field(..., description="Whether the answer is correct")
    points: int = Field(0, description="Points awarded")


class ResultsCalculationRequest(BaseModel):
    """Schema for results calculation requests"""
    session_id: str = Field(..., description="Game session ID")


class GameModuleInfo(BaseModel):
    """Schema for game module information"""
    name: str
    version: str
    description: str
    supported_question_types: List[str]
    config_schema: Dict[str, Any]


class HealthResponse(BaseModel):
    """Schema for health check response"""
    status: str
    timestamp: datetime
    version: str
    database: str
    loaded_modules: List[str]