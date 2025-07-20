"""
Comprehensive game pack validator with detailed error reporting.
Validates structure, content, and media files for all game types.
"""

import json
import re
import asyncio
import aiohttp
import os
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path
import logging
from urllib.parse import urlparse

from pydantic import ValidationError as PydanticValidationError
from ..schemas.game_packs import (
    GamePack, QuizGamePack, FamilyFeudGamePack, LegacyGamePack,
    ValidationError, ValidationReport, MediaFile, MediaType,
    GameType, QuestionType, DifficultyLevel
)

logger = logging.getLogger(__name__)


class PackValidator:
    """Comprehensive game pack validator."""
    
    def __init__(self, media_base_path: Optional[str] = None):
        """Initialize validator with optional media base path."""
        self.media_base_path = media_base_path or "/app/media"
        self.supported_image_formats = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'}
        self.supported_video_formats = {'mp4', 'webm', 'avi', 'mov', 'mkv'}
        self.supported_audio_formats = {'mp3', 'wav', 'ogg', 'aac', 'm4a'}
        
    async def validate_pack(self, content: str, filename: str = "unknown") -> ValidationReport:
        """
        Validate a complete game pack.
        
        Args:
            content: JSON content of the game pack
            filename: Original filename for context
            
        Returns:
            Comprehensive validation report
        """
        logger.info(f"Starting validation of game pack: {filename}")
        
        errors = []
        warnings = []
        game_type = None
        question_count = 0
        media_files = []
        estimated_size = len(content.encode('utf-8'))
        
        try:
            # Parse JSON
            try:
                data = json.loads(content)
            except json.JSONDecodeError as e:
                errors.append(ValidationError(
                    field="json",
                    message=f"Invalid JSON format: {str(e)}",
                    value=None,
                    code="INVALID_JSON"
                ))
                return ValidationReport(
                    is_valid=False,
                    errors=errors,
                    warnings=warnings,
                    estimated_size=estimated_size
                )
            
            # Detect game type and normalize structure
            game_type, normalized_data = self._detect_and_normalize_game_type(data)
            if not game_type:
                errors.append(ValidationError(
                    field="type",
                    message="Could not detect game type. Must be 'quiz' or 'family_feud'",
                    value=data.get("type"),
                    code="UNKNOWN_GAME_TYPE"
                ))
                return ValidationReport(
                    is_valid=False,
                    errors=errors,
                    warnings=warnings,
                    game_type=game_type,
                    estimated_size=estimated_size
                )
            
            # Validate based on game type
            if game_type == "quiz":
                game_pack, pack_errors, pack_warnings = await self._validate_quiz_pack(normalized_data)
            elif game_type == "family_feud":
                game_pack, pack_errors, pack_warnings = await self._validate_family_feud_pack(normalized_data)
            else:
                errors.append(ValidationError(
                    field="type",
                    message=f"Unsupported game type: {game_type}",
                    value=game_type,
                    code="UNSUPPORTED_GAME_TYPE"
                ))
                return ValidationReport(
                    is_valid=False,
                    errors=errors,
                    warnings=warnings,
                    game_type=game_type,
                    estimated_size=estimated_size
                )
            
            errors.extend(pack_errors)
            warnings.extend(pack_warnings)
            
            if game_pack:
                question_count = len(game_pack.questions)
                media_files = await self._extract_media_files(game_pack)
                
                # Validate media files
                media_errors, media_warnings = await self._validate_media_files(media_files)
                errors.extend(media_errors)
                warnings.extend(media_warnings)
                
                # Additional content validation
                content_errors, content_warnings = await self._validate_content_quality(game_pack)
                errors.extend(content_errors)
                warnings.extend(content_warnings)
        
        except Exception as e:
            logger.error(f"Unexpected error during validation: {str(e)}")
            errors.append(ValidationError(
                field="validation",
                message=f"Unexpected validation error: {str(e)}",
                value=None,
                code="VALIDATION_ERROR"
            ))
        
        is_valid = len(errors) == 0
        
        logger.info(f"Validation completed for {filename}: valid={is_valid}, errors={len(errors)}, warnings={len(warnings)}")
        
        return ValidationReport(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            game_type=game_type,
            question_count=question_count,
            media_files=media_files,
            estimated_size=estimated_size
        )
    
    def _detect_and_normalize_game_type(self, data: Dict[str, Any]) -> Tuple[Optional[str], Dict[str, Any]]:
        """Detect game type and normalize data structure."""
        # Handle legacy game_pack wrapper
        if "game_pack" in data:
            pack_data = data["game_pack"]
            
            # Extract metadata
            meta = pack_data.get("meta", {})
            game_type = meta.get("game_type")
            
            # Normalize structure
            normalized = {
                "type": game_type,
                "metadata": meta,
                "settings": pack_data.get("config", {}),
                "questions": pack_data.get("questions", [])
            }
            
            return game_type, normalized
        
        # Handle direct structure
        game_type = data.get("type") or data.get("metadata", {}).get("game_type")
        
        if not game_type:
            # Try to detect from structure
            if "questions" in data:
                questions = data["questions"]
                if questions and isinstance(questions, list):
                    first_question = questions[0]
                    if "answers" in first_question.get("content", {}) or "answers" in first_question:
                        game_type = "family_feud"
                    else:
                        game_type = "quiz"
        
        return game_type, data
    
    async def _validate_quiz_pack(self, data: Dict[str, Any]) -> Tuple[Optional[QuizGamePack], List[ValidationError], List[ValidationError]]:
        """Validate quiz game pack."""
        errors = []
        warnings = []
        
        try:
            game_pack = QuizGamePack(**data)
            
            # Additional quiz-specific validation
            quiz_errors, quiz_warnings = await self._validate_quiz_logic(game_pack)
            errors.extend(quiz_errors)
            warnings.extend(quiz_warnings)
            
            return game_pack, errors, warnings
            
        except PydanticValidationError as e:
            for error in e.errors():
                field_path = ".".join(str(loc) for loc in error["loc"])
                errors.append(ValidationError(
                    field=field_path,
                    message=error["msg"],
                    value=error.get("input"),
                    code=error["type"].upper()
                ))
            return None, errors, warnings
    
    async def _validate_family_feud_pack(self, data: Dict[str, Any]) -> Tuple[Optional[FamilyFeudGamePack], List[ValidationError], List[ValidationError]]:
        """Validate Family Feud game pack."""
        errors = []
        warnings = []
        
        try:
            game_pack = FamilyFeudGamePack(**data)
            
            # Additional Family Feud-specific validation
            ff_errors, ff_warnings = await self._validate_family_feud_logic(game_pack)
            errors.extend(ff_errors)
            warnings.extend(ff_warnings)
            
            return game_pack, errors, warnings
            
        except PydanticValidationError as e:
            for error in e.errors():
                field_path = ".".join(str(loc) for loc in error["loc"])
                errors.append(ValidationError(
                    field=field_path,
                    message=error["msg"],
                    value=error.get("input"),
                    code=error["type"].upper()
                ))
            return None, errors, warnings
    
    async def _validate_quiz_logic(self, game_pack: QuizGamePack) -> Tuple[List[ValidationError], List[ValidationError]]:
        """Validate quiz-specific logic."""
        errors = []
        warnings = []
        
        # Check for balanced difficulty distribution
        difficulty_counts = {}
        for question in game_pack.questions:
            difficulty = question.difficulty or DifficultyLevel.MEDIUM
            difficulty_counts[difficulty] = difficulty_counts.get(difficulty, 0) + 1
        
        total_questions = len(game_pack.questions)
        if total_questions > 10:
            # Warn if difficulty distribution is very unbalanced
            max_difficulty_ratio = max(difficulty_counts.values()) / total_questions
            if max_difficulty_ratio > 0.8:
                warnings.append(ValidationError(
                    field="questions.difficulty",
                    message="Difficulty distribution is very unbalanced",
                    value=difficulty_counts,
                    code="UNBALANCED_DIFFICULTY"
                ))
        
        # Check for reasonable point distribution
        point_values = [q.points for q in game_pack.questions]
        if point_values:
            avg_points = sum(point_values) / len(point_values)
            max_points = max(point_values)
            min_points = min(point_values)
            
            if max_points > avg_points * 5:
                warnings.append(ValidationError(
                    field="questions.points",
                    message="Some questions have disproportionately high points",
                    value={"max": max_points, "avg": avg_points},
                    code="UNBALANCED_POINTS"
                ))
            
            if min_points < avg_points * 0.2:
                warnings.append(ValidationError(
                    field="questions.points",
                    message="Some questions have very low points",
                    value={"min": min_points, "avg": avg_points},
                    code="LOW_POINTS"
                ))
        
        # Validate question types consistency
        question_types = [q.type for q in game_pack.questions]
        type_counts = {}
        for qtype in question_types:
            type_counts[qtype] = type_counts.get(qtype, 0) + 1
        
        # Check for questions requiring validation
        validation_questions = [q for q in game_pack.questions if q.requires_validation]
        if len(validation_questions) > total_questions * 0.3:
            warnings.append(ValidationError(
                field="questions.requires_validation",
                message="Many questions require manual validation, which may slow down gameplay",
                value=len(validation_questions),
                code="MANY_VALIDATION_QUESTIONS"
            ))
        
        return errors, warnings
    
    async def _validate_family_feud_logic(self, game_pack: FamilyFeudGamePack) -> Tuple[List[ValidationError], List[ValidationError]]:
        """Validate Family Feud-specific logic."""
        errors = []
        warnings = []
        
        for i, question in enumerate(game_pack.questions):
            if not question.answers:
                errors.append(ValidationError(
                    field=f"questions.{i}.answers",
                    message="Family Feud questions must have answers",
                    value=None,
                    code="MISSING_ANSWERS"
                ))
                continue
            
            # Check answer point distribution
            total_points = sum(answer.points for answer in question.answers)
            if total_points != 100:
                warnings.append(ValidationError(
                    field=f"questions.{i}.answers.points",
                    message=f"Answer points should sum to 100, got {total_points}",
                    value=total_points,
                    code="INCORRECT_POINT_TOTAL"
                ))
            
            # Check rank consistency
            ranks = [answer.rank for answer in question.answers]
            expected_ranks = list(range(1, len(question.answers) + 1))
            if sorted(ranks) != expected_ranks:
                errors.append(ValidationError(
                    field=f"questions.{i}.answers.rank",
                    message="Answer ranks must be consecutive starting from 1",
                    value=ranks,
                    code="INVALID_RANKS"
                ))
            
            # Check for reasonable answer distribution
            points = [answer.points for answer in question.answers]
            if points and max(points) > 50:
                warnings.append(ValidationError(
                    field=f"questions.{i}.answers.points",
                    message="Top answer has more than 50% of points, may be too dominant",
                    value=max(points),
                    code="DOMINANT_ANSWER"
                ))
        
        return errors, warnings
    
    async def _extract_media_files(self, game_pack: Union[QuizGamePack, FamilyFeudGamePack]) -> List[str]:
        """Extract media file references from game pack."""
        media_files = []
        
        for question in game_pack.questions:
            # Check direct media field
            if hasattr(question, 'media') and question.media:
                media_files.append(question.media.url)
            
            # Check media_content field (legacy)
            if hasattr(question, 'media_content') and question.media_content:
                media_content = question.media_content
                if isinstance(media_content, dict):
                    if 'media_url' in media_content:
                        media_files.append(media_content['media_url'])
                    if 'thumbnail_url' in media_content:
                        media_files.append(media_content['thumbnail_url'])
            
            # Check options for media (quiz questions)
            if hasattr(question, 'options') and question.options:
                for option in question.options:
                    if hasattr(option, 'media') and option.media:
                        media_files.append(option.media.url)
        
        return list(set(media_files))  # Remove duplicates
    
    async def _validate_media_files(self, media_files: List[str]) -> Tuple[List[ValidationError], List[ValidationError]]:
        """Validate media file references."""
        errors = []
        warnings = []
        
        for media_url in media_files:
            try:
                # Parse URL
                parsed = urlparse(media_url)
                
                if parsed.scheme in ['http', 'https']:
                    # Validate remote URL
                    url_errors, url_warnings = await self._validate_remote_media(media_url)
                    errors.extend(url_errors)
                    warnings.extend(url_warnings)
                else:
                    # Validate local file
                    file_errors, file_warnings = await self._validate_local_media(media_url)
                    errors.extend(file_errors)
                    warnings.extend(file_warnings)
                    
            except Exception as e:
                errors.append(ValidationError(
                    field="media",
                    message=f"Error validating media file {media_url}: {str(e)}",
                    value=media_url,
                    code="MEDIA_VALIDATION_ERROR"
                ))
        
        return errors, warnings
    
    async def _validate_remote_media(self, url: str) -> Tuple[List[ValidationError], List[ValidationError]]:
        """Validate remote media URL."""
        errors = []
        warnings = []
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.head(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status >= 400:
                        errors.append(ValidationError(
                            field="media.url",
                            message=f"Media URL returns {response.status} status",
                            value=url,
                            code="MEDIA_URL_ERROR"
                        ))
                    
                    # Check content type
                    content_type = response.headers.get('content-type', '').lower()
                    if not any(media_type in content_type for media_type in ['image', 'video', 'audio']):
                        warnings.append(ValidationError(
                            field="media.content_type",
                            message=f"Unexpected content type: {content_type}",
                            value=content_type,
                            code="UNEXPECTED_CONTENT_TYPE"
                        ))
                    
                    # Check file size
                    content_length = response.headers.get('content-length')
                    if content_length:
                        size = int(content_length)
                        if size > 50 * 1024 * 1024:  # 50MB
                            warnings.append(ValidationError(
                                field="media.size",
                                message=f"Large media file: {size / (1024*1024):.1f}MB",
                                value=size,
                                code="LARGE_MEDIA_FILE"
                            ))
                        
        except asyncio.TimeoutError:
            warnings.append(ValidationError(
                field="media.url",
                message=f"Media URL timeout: {url}",
                value=url,
                code="MEDIA_URL_TIMEOUT"
            ))
        except Exception as e:
            warnings.append(ValidationError(
                field="media.url",
                message=f"Could not validate media URL: {str(e)}",
                value=url,
                code="MEDIA_URL_VALIDATION_ERROR"
            ))
        
        return errors, warnings
    
    async def _validate_local_media(self, file_path: str) -> Tuple[List[ValidationError], List[ValidationError]]:
        """Validate local media file."""
        errors = []
        warnings = []
        
        # Construct full path
        if file_path.startswith('./') or file_path.startswith('/'):
            full_path = Path(self.media_base_path) / file_path.lstrip('./')
        else:
            full_path = Path(self.media_base_path) / file_path
        
        if not full_path.exists():
            errors.append(ValidationError(
                field="media.file",
                message=f"Media file not found: {file_path}",
                value=file_path,
                code="MEDIA_FILE_NOT_FOUND"
            ))
        else:
            # Check file size
            size = full_path.stat().st_size
            if size > 50 * 1024 * 1024:  # 50MB
                warnings.append(ValidationError(
                    field="media.size",
                    message=f"Large media file: {size / (1024*1024):.1f}MB",
                    value=size,
                    code="LARGE_MEDIA_FILE"
                ))
            
            # Check file extension
            extension = full_path.suffix.lower().lstrip('.')
            all_formats = self.supported_image_formats | self.supported_video_formats | self.supported_audio_formats
            if extension not in all_formats:
                warnings.append(ValidationError(
                    field="media.format",
                    message=f"Unsupported media format: {extension}",
                    value=extension,
                    code="UNSUPPORTED_MEDIA_FORMAT"
                ))
        
        return errors, warnings
    
    async def _validate_content_quality(self, game_pack: Union[QuizGamePack, FamilyFeudGamePack]) -> Tuple[List[ValidationError], List[ValidationError]]:
        """Validate content quality and completeness."""
        errors = []
        warnings = []
        
        # Check metadata completeness
        metadata = game_pack.metadata
        if not metadata:
            errors.append(ValidationError(
                field="metadata",
                message="Game pack must have metadata",
                value=None,
                code="MISSING_METADATA"
            ))
            return errors, warnings
        
        if not metadata.description:
            warnings.append(ValidationError(
                field="metadata.description",
                message="Game pack should have a description",
                value=None,
                code="MISSING_DESCRIPTION"
            ))
        
        if not metadata.tags:
            warnings.append(ValidationError(
                field="metadata.tags",
                message="Game pack should have tags for better categorization",
                value=None,
                code="MISSING_TAGS"
            ))
        
        # Check question content quality
        for i, question in enumerate(game_pack.questions):
            # Check question text length
            if len(question.text) < 10:
                warnings.append(ValidationError(
                    field=f"questions.{i}.text",
                    message="Question text is very short",
                    value=len(question.text),
                    code="SHORT_QUESTION_TEXT"
                ))
            
            if len(question.text) > 500:
                warnings.append(ValidationError(
                    field=f"questions.{i}.text",
                    message="Question text is very long",
                    value=len(question.text),
                    code="LONG_QUESTION_TEXT"
                ))
            
            # Check for explanation
            if not question.explanation:
                warnings.append(ValidationError(
                    field=f"questions.{i}.explanation",
                    message="Question should have an explanation",
                    value=None,
                    code="MISSING_EXPLANATION"
                ))
            
            # Check time limits
            if question.time_limit < 10:
                warnings.append(ValidationError(
                    field=f"questions.{i}.time_limit",
                    message="Very short time limit may be too challenging",
                    value=question.time_limit,
                    code="SHORT_TIME_LIMIT"
                ))
            
            if question.time_limit > 300:
                warnings.append(ValidationError(
                    field=f"questions.{i}.time_limit",
                    message="Very long time limit may slow down gameplay",
                    value=question.time_limit,
                    code="LONG_TIME_LIMIT"
                ))
        
        return errors, warnings
    
    def get_validation_summary(self, report: ValidationReport) -> str:
        """Generate a human-readable validation summary."""
        if report.is_valid:
            return f"✅ Game pack is valid! Found {report.question_count} questions."
        
        summary = f"❌ Game pack validation failed with {report.error_count} errors"
        if report.warning_count > 0:
            summary += f" and {report.warning_count} warnings"
        
        summary += f"\n\nGame Type: {report.game_type or 'Unknown'}"
        summary += f"\nQuestions: {report.question_count}"
        summary += f"\nMedia Files: {len(report.media_files)}"
        summary += f"\nEstimated Size: {report.estimated_size / 1024:.1f} KB"
        
        if report.errors:
            summary += "\n\n🔴 Errors:"
            for error in report.errors[:5]:  # Show first 5 errors
                summary += f"\n  • {error.field}: {error.message}"
            if len(report.errors) > 5:
                summary += f"\n  ... and {len(report.errors) - 5} more errors"
        
        if report.warnings:
            summary += "\n\n🟡 Warnings:"
            for warning in report.warnings[:3]:  # Show first 3 warnings
                summary += f"\n  • {warning.field}: {warning.message}"
            if len(report.warnings) > 3:
                summary += f"\n  ... and {len(report.warnings) - 3} more warnings"
        
        return summary
