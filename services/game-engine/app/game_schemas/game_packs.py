"""
Game Packs Schemas for Game Engine
Local copy of shared game pack schemas to avoid Docker build issues
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum
import uuid


class GameType(str, Enum):
    """Game type enumeration"""
    QUIZ = "quiz"
    FAMILY_FEUD = "family_feud"
    TRIVIA = "trivia"
    WORD_GAME = "word_game"
    CUSTOM = "custom"


class QuestionType(str, Enum):
    """Question type enumeration"""
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    OPEN_ENDED = "open_ended"
    FILL_IN_BLANK = "fill_in_blank"
    MATCHING = "matching"
    ORDERING = "ordering"


class DifficultyLevel(str, Enum):
    """Difficulty level enumeration"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


class MediaType(str, Enum):
    """Media type enumeration"""
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"


class MediaFile(BaseModel):
    """Schema for media files"""
    id: str = Field(..., description="Media file ID")
    filename: str = Field(..., description="Original filename")
    media_type: MediaType = Field(..., description="Type of media")
    url: Optional[str] = Field(None, description="Media file URL")
    size: Optional[int] = Field(None, description="File size in bytes")
    mime_type: Optional[str] = Field(None, description="MIME type")
    alt_text: Optional[str] = Field(None, description="Alternative text")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ValidationError(BaseModel):
    """Schema for validation errors"""
    field: str = Field(..., description="Field with error")
    message: str = Field(..., description="Error message")
    error_type: str = Field(..., description="Type of error")
    line_number: Optional[int] = Field(None, description="Line number if applicable")


class ValidationReport(BaseModel):
    """Schema for validation reports"""
    valid: bool = Field(..., description="Whether validation passed")
    errors: List[ValidationError] = Field(default_factory=list, description="List of errors")
    warnings: List[ValidationError] = Field(default_factory=list, description="List of warnings")
    filename: Optional[str] = Field(None, description="Validated filename")
    game_type: Optional[GameType] = Field(None, description="Detected game type")
    total_questions: Optional[int] = Field(None, description="Total questions found")
    validation_time: datetime = Field(default_factory=datetime.utcnow)


class GameMetadata(BaseModel):
    """Schema for game metadata"""
    title: str = Field(..., description="Game title")
    description: Optional[str] = Field(None, description="Game description")
    author: Optional[str] = Field(None, description="Game author")
    version: str = Field("1.0.0", description="Game version")
    category: Optional[str] = Field(None, description="Game category")
    tags: List[str] = Field(default_factory=list, description="Game tags")
    difficulty: DifficultyLevel = Field(DifficultyLevel.MEDIUM, description="Difficulty level")
    estimated_duration: Optional[int] = Field(None, description="Estimated duration in minutes")
    min_players: int = Field(1, description="Minimum players")
    max_players: int = Field(100, description="Maximum players")
    language: str = Field("en", description="Game language")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class QuizQuestion(BaseModel):
    """Schema for quiz questions"""
    id: str = Field(..., description="Question ID")
    question: str = Field(..., description="Question text")
    question_type: QuestionType = Field(QuestionType.MULTIPLE_CHOICE, description="Question type")
    options: List[str] = Field(default_factory=list, description="Answer options")
    correct_answer: Union[str, List[str]] = Field(..., description="Correct answer(s)")
    explanation: Optional[str] = Field(None, description="Answer explanation")
    points: int = Field(1, description="Points for correct answer")
    time_limit: Optional[int] = Field(None, description="Time limit in seconds")
    media: List[MediaFile] = Field(default_factory=list, description="Associated media")
    tags: List[str] = Field(default_factory=list, description="Question tags")
    difficulty: DifficultyLevel = Field(DifficultyLevel.MEDIUM, description="Question difficulty")


class FamilyFeudAnswer(BaseModel):
    """Schema for Family Feud answers"""
    answer: str = Field(..., description="Answer text")
    points: int = Field(..., description="Points for this answer")
    rank: int = Field(..., description="Answer rank (1 is most popular)")


class FamilyFeudQuestion(BaseModel):
    """Schema for Family Feud questions"""
    id: str = Field(..., description="Question ID")
    question: str = Field(..., description="Question text")
    answers: List[FamilyFeudAnswer] = Field(..., description="List of answers")
    category: Optional[str] = Field(None, description="Question category")
    media: List[MediaFile] = Field(default_factory=list, description="Associated media")
    tags: List[str] = Field(default_factory=list, description="Question tags")


class GamePack(BaseModel):
    """Base schema for game packs"""
    metadata: GameMetadata = Field(..., description="Game metadata")
    game_type: GameType = Field(..., description="Type of game")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Game-specific settings")
    media_files: List[MediaFile] = Field(default_factory=list, description="Media files")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class QuizGamePack(GamePack):
    """Schema for quiz game packs"""
    game_type: GameType = Field(GameType.QUIZ, description="Game type")
    questions: List[QuizQuestion] = Field(..., description="Quiz questions")
    
    @validator('questions')
    def validate_questions(cls, v):
        if not v:
            raise ValueError('Quiz must have at least one question')
        return v


class FamilyFeudGamePack(GamePack):
    """Schema for Family Feud game packs"""
    game_type: GameType = Field(GameType.FAMILY_FEUD, description="Game type")
    questions: List[FamilyFeudQuestion] = Field(..., description="Family Feud questions")
    
    @validator('questions')
    def validate_questions(cls, v):
        if not v:
            raise ValueError('Family Feud game must have at least one question')
        return v


class LegacyGamePack(BaseModel):
    """Schema for legacy game pack format"""
    title: str = Field(..., description="Game title")
    description: Optional[str] = Field(None, description="Game description")
    type: str = Field(..., description="Game type")
    questions: List[Dict[str, Any]] = Field(..., description="Questions in legacy format")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Game settings")


class ImportRequest(BaseModel):
    """Schema for import requests"""
    file_content: str = Field(..., description="JSON content of the game pack")
    filename: str = Field(..., description="Original filename")
    validate_only: bool = Field(False, description="Only validate, don't import")
    overwrite_existing: bool = Field(False, description="Overwrite existing games")
    import_media: bool = Field(True, description="Import media files")
    created_by: Optional[uuid.UUID] = Field(None, description="User importing the pack")


class ImportResult(BaseModel):
    """Schema for import results"""
    success: bool = Field(..., description="Import success status")
    game_id: Optional[uuid.UUID] = Field(None, description="Imported game ID")
    message: str = Field(..., description="Import message")
    validation_report: Optional[ValidationReport] = Field(None, description="Validation report")
    imported_questions: int = Field(0, description="Number of imported questions")
    imported_media: int = Field(0, description="Number of imported media files")
    warnings: List[str] = Field(default_factory=list, description="Import warnings")
    import_time: datetime = Field(default_factory=datetime.utcnow)


class ExportRequest(BaseModel):
    """Schema for export requests"""
    game_id: str = Field(..., description="Game ID to export")
    include_media: bool = Field(True, description="Include media files")
    format: str = Field("json", description="Export format")
    compress: bool = Field(False, description="Compress the export")


class ExportResult(BaseModel):
    """Schema for export results"""
    success: bool = Field(..., description="Export success status")
    content: Optional[str] = Field(None, description="Exported content")
    filename: str = Field(..., description="Export filename")
    message: str = Field(..., description="Export message")
    file_size: Optional[int] = Field(None, description="Export file size")
    export_time: datetime = Field(default_factory=datetime.utcnow)


class GameLibraryEntry(BaseModel):
    """Schema for game library entries"""
    id: uuid.UUID = Field(..., description="Game ID")
    title: str = Field(..., description="Game title")
    description: Optional[str] = Field(None, description="Game description")
    game_type: GameType = Field(..., description="Game type")
    author: Optional[str] = Field(None, description="Game author")
    category: Optional[str] = Field(None, description="Game category")
    difficulty: DifficultyLevel = Field(..., description="Difficulty level")
    total_questions: int = Field(..., description="Total number of questions")
    tags: List[str] = Field(default_factory=list, description="Game tags")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    is_public: bool = Field(True, description="Whether game is public")
    play_count: int = Field(0, description="Number of times played")
    rating: Optional[float] = Field(None, description="Average rating")


class GameLibraryFilter(BaseModel):
    """Schema for game library filters"""
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(20, ge=1, le=100, description="Items per page")
    game_type: Optional[GameType] = Field(None, description="Filter by game type")
    category: Optional[str] = Field(None, description="Filter by category")
    difficulty: Optional[DifficultyLevel] = Field(None, description="Filter by difficulty")
    author: Optional[str] = Field(None, description="Filter by author")
    search_text: Optional[str] = Field(None, description="Search in title and description")
    tags: List[str] = Field(default_factory=list, description="Filter by tags")
    min_questions: Optional[int] = Field(None, ge=1, description="Minimum questions")
    max_questions: Optional[int] = Field(None, ge=1, description="Maximum questions")
    is_public: Optional[bool] = Field(None, description="Filter by public status")
    created_after: Optional[datetime] = Field(None, description="Created after date")
    created_before: Optional[datetime] = Field(None, description="Created before date")


class GameLibraryResponse(BaseModel):
    """Schema for game library responses"""
    games: List[GameLibraryEntry] = Field(..., description="List of games")
    total: int = Field(..., description="Total number of games")
    page: int = Field(..., description="Current page")
    per_page: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there's a next page")
    has_prev: bool = Field(..., description="Whether there's a previous page")


class GameStats(BaseModel):
    """Schema for game statistics"""
    total_games: int = Field(0, description="Total number of games")
    games_by_type: Dict[str, int] = Field(default_factory=dict, description="Games by type")
    games_by_difficulty: Dict[str, int] = Field(default_factory=dict, description="Games by difficulty")
    games_by_category: Dict[str, int] = Field(default_factory=dict, description="Games by category")
    total_questions: int = Field(0, description="Total questions across all games")
    average_questions_per_game: float = Field(0.0, description="Average questions per game")
    most_popular_tags: List[str] = Field(default_factory=list, description="Most popular tags")
    recent_games: List[GameLibraryEntry] = Field(default_factory=list, description="Recently created games")