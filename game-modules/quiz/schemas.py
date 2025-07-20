"""
Quiz Module - Pydantic Schemas
Data validation schemas for quiz module
"""

from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, validator
from enum import Enum
from datetime import datetime


class QuestionTypeEnum(str, Enum):
    """Supported question types"""
    MULTIPLE_CHOICE = "multiple_choice"
    TEXT_INPUT = "text_input"
    TRUE_FALSE = "true_false"
    MEDIA_QUESTION = "media_question"
    VALIDATION_REQUIRED = "validation_required"
    TIMED_QUESTION = "timed_question"
    WEIGHTED_QUESTION = "weighted_question"


class DifficultyLevel(str, Enum):
    """Difficulty levels for weighted questions"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


class MediaType(str, Enum):
    """Media content types"""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"


class QuestionOptionSchema(BaseModel):
    """Schema for multiple choice question options"""
    text: str = Field(..., min_length=1, max_length=500)
    is_correct: bool = False
    explanation: Optional[str] = Field(None, max_length=1000)


class MediaContentSchema(BaseModel):
    """Schema for media content"""
    media_type: MediaType
    media_url: Optional[str] = Field(None, regex=r'^https?://.+')
    media_file: Optional[str] = None
    thumbnail_url: Optional[str] = Field(None, regex=r'^https?://.+')
    description: Optional[str] = Field(None, max_length=500)
    
    @validator('media_url', 'media_file')
    def validate_media_source(cls, v, values):
        """Ensure at least one media source is provided"""
        if not v and not values.get('media_file') and not values.get('media_url'):
            raise ValueError('Either media_url or media_file must be provided')
        return v


class ValidationRuleSchema(BaseModel):
    """Schema for answer validation rules"""
    case_sensitive: bool = False
    exact_match: bool = False
    allow_partial: bool = True
    similarity_threshold: float = Field(0.8, ge=0.0, le=1.0)
    custom_validator: Optional[str] = None


class BaseQuestionSchema(BaseModel):
    """Base schema for all question types"""
    id: str = Field(..., min_length=1, max_length=100)
    text: str = Field(..., min_length=1, max_length=2000)
    type: QuestionTypeEnum
    points: int = Field(10, ge=1, le=1000)
    time_limit: int = Field(30, ge=5, le=600)
    explanation: Optional[str] = Field(None, max_length=2000)
    tags: List[str] = Field(default_factory=list)
    order: Optional[int] = Field(None, ge=1)
    requires_validation: bool = False
    
    @validator('tags')
    def validate_tags(cls, v):
        """Validate tags list"""
        if len(v) > 10:
            raise ValueError('Maximum 10 tags allowed')
        for tag in v:
            if len(tag) > 50:
                raise ValueError('Tag length cannot exceed 50 characters')
        return v


class MultipleChoiceQuestionSchema(BaseQuestionSchema):
    """Schema for multiple choice questions"""
    type: QuestionTypeEnum = QuestionTypeEnum.MULTIPLE_CHOICE
    options: List[QuestionOptionSchema] = Field(..., min_items=2, max_items=10)
    shuffle_options: bool = True
    correct_answers: List[str] = Field(..., min_items=1)
    
    @validator('correct_answers')
    def validate_correct_answers(cls, v, values):
        """Ensure correct answers are in options"""
        if 'options' in values:
            option_texts = [opt.text for opt in values['options']]
            for answer in v:
                if answer not in option_texts:
                    raise ValueError(f'Correct answer "{answer}" not found in options')
        return v
    
    @validator('options')
    def validate_options_have_correct(cls, v, values):
        """Ensure at least one option is marked as correct"""
        if 'correct_answers' in values:
            correct_answers = values['correct_answers']
            option_texts = [opt.text for opt in v]
            if not any(answer in option_texts for answer in correct_answers):
                raise ValueError('At least one option must be marked as correct')
        return v


class TextInputQuestionSchema(BaseQuestionSchema):
    """Schema for text input questions"""
    type: QuestionTypeEnum = QuestionTypeEnum.TEXT_INPUT
    correct_answers: List[str] = Field(..., min_items=1, max_items=20)
    validation_rules: ValidationRuleSchema = Field(default_factory=ValidationRuleSchema)
    
    @validator('correct_answers')
    def validate_correct_answers(cls, v):
        """Validate correct answers"""
        for answer in v:
            if len(answer.strip()) == 0:
                raise ValueError('Correct answers cannot be empty')
            if len(answer) > 500:
                raise ValueError('Correct answer length cannot exceed 500 characters')
        return v


class TrueFalseQuestionSchema(BaseQuestionSchema):
    """Schema for true/false questions"""
    type: QuestionTypeEnum = QuestionTypeEnum.TRUE_FALSE
    correct_answer: bool


class MediaQuestionSchema(BaseQuestionSchema):
    """Schema for media questions"""
    type: QuestionTypeEnum = QuestionTypeEnum.MEDIA_QUESTION
    media_content: MediaContentSchema
    correct_answers: List[str] = Field(..., min_items=1, max_items=20)
    validation_rules: ValidationRuleSchema = Field(default_factory=ValidationRuleSchema)


class ValidationRequiredQuestionSchema(BaseQuestionSchema):
    """Schema for questions requiring manual validation"""
    type: QuestionTypeEnum = QuestionTypeEnum.VALIDATION_REQUIRED
    validation_criteria: str = Field(..., min_length=1, max_length=1000)
    requires_validation: bool = True


class TimedQuestionSchema(BaseQuestionSchema):
    """Schema for timed questions with bonus scoring"""
    type: QuestionTypeEnum = QuestionTypeEnum.TIMED_QUESTION
    correct_answers: List[str] = Field(..., min_items=1, max_items=20)
    time_bonus_multiplier: float = Field(1.5, ge=1.0, le=5.0)
    minimum_time_for_bonus: int = Field(5, ge=1, le=60)


class WeightedQuestionSchema(BaseQuestionSchema):
    """Schema for weighted questions with difficulty-based scoring"""
    type: QuestionTypeEnum = QuestionTypeEnum.WEIGHTED_QUESTION
    correct_answers: List[str] = Field(..., min_items=1, max_items=20)
    difficulty_level: DifficultyLevel = DifficultyLevel.MEDIUM
    point_multipliers: Optional[Dict[str, float]] = None
    
    @validator('point_multipliers')
    def validate_point_multipliers(cls, v):
        """Validate point multipliers"""
        if v is not None:
            for level, multiplier in v.items():
                if multiplier < 0.1 or multiplier > 10.0:
                    raise ValueError(f'Point multiplier for {level} must be between 0.1 and 10.0')
        return v


# Union type for all question schemas
QuestionSchema = Union[
    MultipleChoiceQuestionSchema,
    TextInputQuestionSchema,
    TrueFalseQuestionSchema,
    MediaQuestionSchema,
    ValidationRequiredQuestionSchema,
    TimedQuestionSchema,
    WeightedQuestionSchema
]


class QuizConfigSchema(BaseModel):
    """Schema for quiz game configuration"""
    time_limit: int = Field(30, ge=5, le=600, description="Default time limit per question in seconds")
    points_per_question: int = Field(10, ge=1, le=1000, description="Default points per question")
    shuffle_options: bool = Field(True, description="Shuffle multiple choice options")
    allow_partial_credit: bool = Field(False, description="Allow partial credit for partially correct answers")
    case_sensitive: bool = Field(False, description="Case sensitive text matching")
    show_correct_answers: bool = Field(True, description="Show correct answers after each question")
    show_explanations: bool = Field(True, description="Show explanations after each question")
    allow_review: bool = Field(False, description="Allow players to review questions before submitting")
    max_attempts: int = Field(1, ge=1, le=5, description="Maximum attempts per question")
    time_bonus_enabled: bool = Field(True, description="Enable time-based bonus scoring")
    difficulty_scaling: bool = Field(False, description="Enable difficulty-based point scaling")


class QuizMetadataSchema(BaseModel):
    """Schema for quiz metadata"""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    version: str = Field("1.0.0", regex=r'^\d+\.\d+\.\d+$')
    author: str = Field(..., min_length=1, max_length=100)
    game_type: str = Field("quiz", regex=r'^[a-z_]+$')
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    category: Optional[str] = Field(None, max_length=100)
    difficulty: Optional[DifficultyLevel] = None
    estimated_duration: Optional[int] = Field(None, ge=1, le=7200, description="Estimated duration in seconds")
    language: str = Field("ru", min_length=2, max_length=5)
    tags: List[str] = Field(default_factory=list, max_items=20)


class QuizPackSchema(BaseModel):
    """Schema for complete quiz pack"""
    metadata: QuizMetadataSchema
    config: QuizConfigSchema = Field(default_factory=QuizConfigSchema)
    questions: List[QuestionSchema] = Field(..., min_items=1, max_items=1000)
    
    @validator('questions')
    def validate_questions(cls, v):
        """Validate questions list"""
        question_ids = [q.id for q in v]
        if len(question_ids) != len(set(question_ids)):
            raise ValueError('Question IDs must be unique')
        return v


class AnswerSchema(BaseModel):
    """Schema for player answers"""
    user_id: str = Field(..., min_length=1, max_length=100)
    question_id: str = Field(..., min_length=1, max_length=100)
    session_id: str = Field(..., min_length=1, max_length=100)
    answer_text: str = Field(..., max_length=2000)
    answered_at: datetime = Field(default_factory=datetime.utcnow)
    time_taken: Optional[float] = Field(None, ge=0.0)
    is_correct: Optional[bool] = None
    points_earned: int = Field(0, ge=0)
    requires_validation: bool = False


class ValidationResultSchema(BaseModel):
    """Schema for answer validation results"""
    is_correct: Optional[bool]
    points_earned: int = Field(0, ge=0)
    explanation: Optional[str] = None
    similarity_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    time_bonus_applied: bool = False
    requires_manual_validation: bool = False
    validation_criteria: Optional[str] = None
    correct_answers: Optional[List[str]] = None


class GameSessionSchema(BaseModel):
    """Schema for game session data"""
    id: str = Field(..., min_length=1, max_length=100)
    game_id: str = Field(..., min_length=1, max_length=100)
    admin_id: str = Field(..., min_length=1, max_length=100)
    players: List[str] = Field(default_factory=list, max_items=1000)
    current_question: Optional[str] = None
    status: str = Field("waiting", regex=r'^(waiting|active|paused|completed|cancelled)$')
    config: QuizConfigSchema = Field(default_factory=QuizConfigSchema)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class PlayerStatsSchema(BaseModel):
    """Schema for player statistics"""
    user_id: str = Field(..., min_length=1, max_length=100)
    total_score: int = Field(0, ge=0)
    correct_answers: int = Field(0, ge=0)
    total_answers: int = Field(0, ge=0)
    accuracy: float = Field(0.0, ge=0.0, le=100.0)
    average_time: float = Field(0.0, ge=0.0)
    rank: int = Field(1, ge=1)
    time_bonus_points: int = Field(0, ge=0)
    difficulty_bonus_points: int = Field(0, ge=0)


class QuizResultsSchema(BaseModel):
    """Schema for quiz results"""
    game_type: str = "quiz"
    session_id: str = Field(..., min_length=1, max_length=100)
    total_players: int = Field(0, ge=0)
    total_questions: int = Field(0, ge=0)
    session_duration: int = Field(0, ge=0, description="Session duration in seconds")
    leaderboard: List[PlayerStatsSchema] = Field(default_factory=list)
    completion_rate: float = Field(0.0, ge=0.0, le=100.0)
    average_score: float = Field(0.0, ge=0.0)
    average_accuracy: float = Field(0.0, ge=0.0, le=100.0)
    questions_requiring_validation: List[str] = Field(default_factory=list)


class QuizExportSchema(BaseModel):
    """Schema for exporting quiz data"""
    quiz_pack: QuizPackSchema
    session_data: Optional[GameSessionSchema] = None
    results: Optional[QuizResultsSchema] = None
    answers: List[AnswerSchema] = Field(default_factory=list)
    export_timestamp: datetime = Field(default_factory=datetime.utcnow)
    export_format: str = Field("json", regex=r'^(json|csv|xlsx)$')


class QuizImportSchema(BaseModel):
    """Schema for importing quiz data"""
    source_format: str = Field(..., regex=r'^(json|csv|xlsx|txt)$')
    quiz_pack: QuizPackSchema
    import_options: Dict[str, Any] = Field(default_factory=dict)
    validation_strict: bool = Field(True, description="Strict validation during import")
    auto_fix_errors: bool = Field(False, description="Automatically fix minor errors")


def validate_question_by_type(question_data: Dict[str, Any]) -> QuestionSchema:
    """Validate question data based on its type"""
    question_type = question_data.get("type", "text_input")
    
    schema_map = {
        QuestionTypeEnum.MULTIPLE_CHOICE: MultipleChoiceQuestionSchema,
        QuestionTypeEnum.TEXT_INPUT: TextInputQuestionSchema,
        QuestionTypeEnum.TRUE_FALSE: TrueFalseQuestionSchema,
        QuestionTypeEnum.MEDIA_QUESTION: MediaQuestionSchema,
        QuestionTypeEnum.VALIDATION_REQUIRED: ValidationRequiredQuestionSchema,
        QuestionTypeEnum.TIMED_QUESTION: TimedQuestionSchema,
        QuestionTypeEnum.WEIGHTED_QUESTION: WeightedQuestionSchema,
    }
    
    schema_class = schema_map.get(QuestionTypeEnum(question_type), TextInputQuestionSchema)
    return schema_class(**question_data)


def create_default_quiz_config() -> QuizConfigSchema:
    """Create default quiz configuration"""
    return QuizConfigSchema()


def create_quiz_metadata(title: str, author: str, **kwargs) -> QuizMetadataSchema:
    """Create quiz metadata with required fields"""
    return QuizMetadataSchema(title=title, author=author, **kwargs)