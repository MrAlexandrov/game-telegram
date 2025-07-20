"""
Game Engine Schemas Package

This package contains Pydantic schemas for the game engine service.
"""

# Import from base schemas
from .base import (
    GameBase,
    GameCreate,
    GameUpdate,
    GameResponse,
    QuestionBase,
    QuestionCreate,
    QuestionUpdate,
    QuestionResponse,
    GamePackBase,
    GamePackCreate,
    GamePackResponse,
    GamePackValidation,
    MediaFileBase,
    MediaFileCreate,
    MediaFileResponse,
)

# Import from engine schemas
from .engine import (
    GameEngineRequest,
    AnswerValidationRequest,
    ResultsCalculationRequest,
    GameModuleInfo,
    HealthResponse,
)

# Import from game_packs.py in this directory
from .game_packs import (
    GameType,
    QuestionType,
    DifficultyLevel,
    MediaType,
    MediaFile,
    ValidationReport,
    ImportRequest,
    ImportResult,
    ExportRequest,
    ExportResult,
    GameLibraryFilter,
    GameLibraryResponse,
)

__all__ = [
    # From base.py
    "GameBase",
    "GameCreate",
    "GameUpdate",
    "GameResponse",
    "QuestionBase",
    "QuestionCreate",
    "QuestionUpdate",
    "QuestionResponse",
    "GamePackBase",
    "GamePackCreate",
    "GamePackResponse",
    "GamePackValidation",
    "MediaFileBase",
    "MediaFileCreate",
    "MediaFileResponse",
    # From engine.py
    "GameEngineRequest",
    "AnswerValidationRequest",
    "ResultsCalculationRequest",
    "GameModuleInfo",
    "HealthResponse",
    # From game_packs.py
    "GameType",
    "QuestionType",
    "DifficultyLevel",
    "MediaType",
    "MediaFile",
    "ValidationReport",
    "ImportRequest",
    "ImportResult",
    "ExportRequest",
    "ExportResult",
    "GameLibraryFilter",
    "GameLibraryResponse",
]
