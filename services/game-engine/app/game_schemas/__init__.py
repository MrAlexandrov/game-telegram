"""
Game Engine Schemas Package

This package contains Pydantic schemas for the game engine service.
"""

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
