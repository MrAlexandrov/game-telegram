"""
Quiz Module - Question Types
Defines different types of questions supported by the quiz module
"""

from typing import Dict, Any, List, Optional, Union
from enum import Enum
from dataclasses import dataclass
from datetime import datetime


class QuestionType(Enum):
    """Supported question types"""
    MULTIPLE_CHOICE = "multiple_choice"
    TEXT_INPUT = "text_input"
    TRUE_FALSE = "true_false"
    MEDIA_QUESTION = "media_question"
    VALIDATION_REQUIRED = "validation_required"
    TIMED_QUESTION = "timed_question"
    WEIGHTED_QUESTION = "weighted_question"


@dataclass
class QuestionOption:
    """Option for multiple choice questions"""
    text: str
    is_correct: bool = False
    explanation: Optional[str] = None


@dataclass
class MediaContent:
    """Media content for questions"""
    media_type: str  # image, video, audio
    media_url: Optional[str] = None
    media_file: Optional[str] = None
    thumbnail_url: Optional[str] = None
    description: Optional[str] = None


@dataclass
class ValidationRule:
    """Validation rules for answers"""
    case_sensitive: bool = False
    exact_match: bool = False
    allow_partial: bool = True
    similarity_threshold: float = 0.8
    custom_validator: Optional[str] = None


class BaseQuestion:
    """Base class for all question types"""
    
    def __init__(self, 
                 question_id: str,
                 text: str,
                 points: int = 10,
                 time_limit: int = 30,
                 explanation: Optional[str] = None,
                 tags: Optional[List[str]] = None):
        self.question_id = question_id
        self.text = text
        self.points = points
        self.time_limit = time_limit
        self.explanation = explanation
        self.tags = tags or []
        self.question_type = QuestionType.TEXT_INPUT  # Default, should be overridden
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert question to dictionary"""
        return {
            "id": self.question_id,
            "text": self.text,
            "type": self.question_type.value,
            "points": self.points,
            "time_limit": self.time_limit,
            "explanation": self.explanation,
            "tags": self.tags
        }
    
    def validate_answer(self, answer: str) -> Dict[str, Any]:
        """Validate answer - to be implemented by subclasses"""
        raise NotImplementedError


class MultipleChoiceQuestion(BaseQuestion):
    """Multiple choice question with options"""
    
    def __init__(self, 
                 question_id: str,
                 text: str,
                 options: List[QuestionOption],
                 shuffle_options: bool = True,
                 **kwargs):
        super().__init__(question_id, text, **kwargs)
        self.question_type = QuestionType.MULTIPLE_CHOICE
        self.options = options
        self.shuffle_options = shuffle_options
        self.correct_answers = [opt.text for opt in options if opt.is_correct]
    
    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        base_dict.update({
            "options": [{"text": opt.text, "explanation": opt.explanation} for opt in self.options],
            "shuffle_options": self.shuffle_options,
            "correct_answers": self.correct_answers
        })
        return base_dict
    
    def validate_answer(self, answer: str) -> Dict[str, Any]:
        """Validate multiple choice answer"""
        is_correct = answer.strip() in self.correct_answers
        points_earned = self.points if is_correct else 0
        
        # Find the selected option for explanation
        selected_option = next((opt for opt in self.options if opt.text == answer), None)
        explanation = selected_option.explanation if selected_option else None
        
        return {
            "is_correct": is_correct,
            "points_earned": points_earned,
            "explanation": explanation or self.explanation,
            "correct_answers": self.correct_answers
        }


class TextInputQuestion(BaseQuestion):
    """Text input question with flexible matching"""
    
    def __init__(self, 
                 question_id: str,
                 text: str,
                 correct_answers: List[str],
                 validation_rules: Optional[ValidationRule] = None,
                 **kwargs):
        super().__init__(question_id, text, **kwargs)
        self.question_type = QuestionType.TEXT_INPUT
        self.correct_answers = correct_answers
        self.validation_rules = validation_rules or ValidationRule()
    
    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        base_dict.update({
            "correct_answers": self.correct_answers,
            "validation_rules": {
                "case_sensitive": self.validation_rules.case_sensitive,
                "exact_match": self.validation_rules.exact_match,
                "allow_partial": self.validation_rules.allow_partial,
                "similarity_threshold": self.validation_rules.similarity_threshold
            }
        })
        return base_dict
    
    def validate_answer(self, answer: str) -> Dict[str, Any]:
        """Validate text input answer with flexible matching"""
        user_answer = answer.strip()
        if not self.validation_rules.case_sensitive:
            user_answer = user_answer.lower()
        
        is_correct = False
        similarity_score = 0.0
        
        for correct in self.correct_answers:
            correct_answer = correct.strip()
            if not self.validation_rules.case_sensitive:
                correct_answer = correct_answer.lower()
            
            # Exact match
            if user_answer == correct_answer:
                is_correct = True
                similarity_score = 1.0
                break
            
            # Partial matching if allowed
            if self.validation_rules.allow_partial and not self.validation_rules.exact_match:
                similarity = self._calculate_similarity(user_answer, correct_answer)
                if similarity >= self.validation_rules.similarity_threshold:
                    is_correct = True
                    similarity_score = similarity
                    break
                elif similarity > similarity_score:
                    similarity_score = similarity
        
        # Calculate points based on similarity if partial credit is allowed
        points_earned = 0
        if is_correct:
            if self.validation_rules.allow_partial and similarity_score < 1.0:
                points_earned = int(self.points * similarity_score)
            else:
                points_earned = self.points
        
        return {
            "is_correct": is_correct,
            "points_earned": points_earned,
            "similarity_score": similarity_score,
            "explanation": self.explanation,
            "correct_answers": self.correct_answers
        }
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings using Levenshtein distance"""
        def levenshtein_distance(s1: str, s2: str) -> int:
            if len(s1) < len(s2):
                return levenshtein_distance(s2, s1)
            
            if len(s2) == 0:
                return len(s1)
            
            previous_row = list(range(len(s2) + 1))
            for i, c1 in enumerate(s1):
                current_row = [i + 1]
                for j, c2 in enumerate(s2):
                    insertions = previous_row[j + 1] + 1
                    deletions = current_row[j] + 1
                    substitutions = previous_row[j] + (c1 != c2)
                    current_row.append(min(insertions, deletions, substitutions))
                previous_row = current_row
            
            return previous_row[-1]
        
        max_len = max(len(text1), len(text2))
        if max_len == 0:
            return 1.0
        
        distance = levenshtein_distance(text1, text2)
        return 1.0 - (distance / max_len)


class TrueFalseQuestion(BaseQuestion):
    """True/False question"""
    
    def __init__(self, 
                 question_id: str,
                 text: str,
                 correct_answer: bool,
                 **kwargs):
        super().__init__(question_id, text, **kwargs)
        self.question_type = QuestionType.TRUE_FALSE
        self.correct_answer = correct_answer
    
    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        base_dict.update({
            "correct_answer": self.correct_answer
        })
        return base_dict
    
    def validate_answer(self, answer: str) -> Dict[str, Any]:
        """Validate true/false answer"""
        # Convert answer to boolean
        answer_bool = answer.lower() in ["true", "yes", "1", "да", "правда", "верно"]
        is_correct = answer_bool == self.correct_answer
        points_earned = self.points if is_correct else 0
        
        return {
            "is_correct": is_correct,
            "points_earned": points_earned,
            "explanation": self.explanation,
            "correct_answer": self.correct_answer
        }


class MediaQuestion(BaseQuestion):
    """Question with media content (images, videos, audio)"""
    
    def __init__(self, 
                 question_id: str,
                 text: str,
                 media_content: MediaContent,
                 correct_answers: List[str],
                 validation_rules: Optional[ValidationRule] = None,
                 **kwargs):
        super().__init__(question_id, text, **kwargs)
        self.question_type = QuestionType.MEDIA_QUESTION
        self.media_content = media_content
        self.correct_answers = correct_answers
        self.validation_rules = validation_rules or ValidationRule()
    
    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        base_dict.update({
            "media_content": {
                "media_type": self.media_content.media_type,
                "media_url": self.media_content.media_url,
                "media_file": self.media_content.media_file,
                "thumbnail_url": self.media_content.thumbnail_url,
                "description": self.media_content.description
            },
            "correct_answers": self.correct_answers
        })
        return base_dict
    
    def validate_answer(self, answer: str) -> Dict[str, Any]:
        """Validate media question answer (similar to text input)"""
        # Use same validation logic as TextInputQuestion
        text_question = TextInputQuestion(
            self.question_id, 
            self.text, 
            self.correct_answers, 
            self.validation_rules,
            points=self.points
        )
        return text_question.validate_answer(answer)


class ValidationRequiredQuestion(BaseQuestion):
    """Question that requires manual validation by admin"""
    
    def __init__(self, 
                 question_id: str,
                 text: str,
                 validation_criteria: str,
                 **kwargs):
        super().__init__(question_id, text, **kwargs)
        self.question_type = QuestionType.VALIDATION_REQUIRED
        self.validation_criteria = validation_criteria
        self.requires_validation = True
    
    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        base_dict.update({
            "validation_criteria": self.validation_criteria,
            "requires_validation": True
        })
        return base_dict
    
    def validate_answer(self, answer: str) -> Dict[str, Any]:
        """Mark answer for manual validation"""
        return {
            "is_correct": None,  # Will be determined by admin
            "points_earned": 0,  # Will be set after validation
            "requires_manual_validation": True,
            "validation_criteria": self.validation_criteria,
            "answer_text": answer
        }


class TimedQuestion(BaseQuestion):
    """Question with special timing mechanics"""
    
    def __init__(self, 
                 question_id: str,
                 text: str,
                 correct_answers: List[str],
                 time_bonus_multiplier: float = 1.5,
                 minimum_time_for_bonus: int = 5,
                 **kwargs):
        super().__init__(question_id, text, **kwargs)
        self.question_type = QuestionType.TIMED_QUESTION
        self.correct_answers = correct_answers
        self.time_bonus_multiplier = time_bonus_multiplier
        self.minimum_time_for_bonus = minimum_time_for_bonus
    
    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        base_dict.update({
            "correct_answers": self.correct_answers,
            "time_bonus_multiplier": self.time_bonus_multiplier,
            "minimum_time_for_bonus": self.minimum_time_for_bonus
        })
        return base_dict
    
    def validate_answer(self, answer: str, time_taken: Optional[float] = None) -> Dict[str, Any]:
        """Validate answer with time-based scoring"""
        is_correct = answer.strip().lower() in [ans.lower() for ans in self.correct_answers]
        
        if not is_correct:
            return {
                "is_correct": False,
                "points_earned": 0,
                "time_taken": time_taken,
                "explanation": self.explanation
            }
        
        # Calculate time bonus
        base_points = self.points
        if time_taken and time_taken <= self.minimum_time_for_bonus:
            bonus_points = int(base_points * (self.time_bonus_multiplier - 1))
            points_earned = base_points + bonus_points
        else:
            points_earned = base_points
        
        return {
            "is_correct": True,
            "points_earned": points_earned,
            "time_taken": time_taken,
            "time_bonus_applied": time_taken and time_taken <= self.minimum_time_for_bonus,
            "explanation": self.explanation
        }


class WeightedQuestion(BaseQuestion):
    """Question with variable point values based on difficulty"""
    
    def __init__(self, 
                 question_id: str,
                 text: str,
                 correct_answers: List[str],
                 difficulty_level: str = "medium",  # easy, medium, hard, expert
                 point_multipliers: Optional[Dict[str, float]] = None,
                 **kwargs):
        super().__init__(question_id, text, **kwargs)
        self.question_type = QuestionType.WEIGHTED_QUESTION
        self.correct_answers = correct_answers
        self.difficulty_level = difficulty_level
        self.point_multipliers = point_multipliers or {
            "easy": 1.0,
            "medium": 1.5,
            "hard": 2.0,
            "expert": 3.0
        }
    
    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        base_dict.update({
            "correct_answers": self.correct_answers,
            "difficulty_level": self.difficulty_level,
            "point_multipliers": self.point_multipliers
        })
        return base_dict
    
    def validate_answer(self, answer: str) -> Dict[str, Any]:
        """Validate answer with difficulty-based scoring"""
        is_correct = answer.strip().lower() in [ans.lower() for ans in self.correct_answers]
        
        if is_correct:
            multiplier = self.point_multipliers.get(self.difficulty_level, 1.0)
            points_earned = int(self.points * multiplier)
        else:
            points_earned = 0
        
        return {
            "is_correct": is_correct,
            "points_earned": points_earned,
            "difficulty_level": self.difficulty_level,
            "point_multiplier": self.point_multipliers.get(self.difficulty_level, 1.0),
            "explanation": self.explanation
        }


def create_question_from_dict(question_data: Dict[str, Any]) -> BaseQuestion:
    """Factory function to create question objects from dictionary data"""
    question_type = question_data.get("type", "text_input")
    question_id = question_data.get("id", "")
    text = question_data.get("text", "")
    points = question_data.get("points", 10)
    time_limit = question_data.get("time_limit", 30)
    explanation = question_data.get("explanation")
    tags = question_data.get("tags", [])
    
    if question_type == QuestionType.MULTIPLE_CHOICE.value:
        options_data = question_data.get("options", [])
        correct_answers = question_data.get("correct_answers", [])
        
        options = []
        for opt_data in options_data:
            if isinstance(opt_data, str):
                is_correct = opt_data in correct_answers
                options.append(QuestionOption(text=opt_data, is_correct=is_correct))
            elif isinstance(opt_data, dict):
                options.append(QuestionOption(
                    text=opt_data.get("text", ""),
                    is_correct=opt_data.get("text", "") in correct_answers,
                    explanation=opt_data.get("explanation")
                ))
        
        return MultipleChoiceQuestion(
            question_id=question_id,
            text=text,
            options=options,
            shuffle_options=question_data.get("shuffle_options", True),
            points=points,
            time_limit=time_limit,
            explanation=explanation,
            tags=tags
        )
    
    elif question_type == QuestionType.TRUE_FALSE.value:
        correct_answer = question_data.get("correct_answer", True)
        if isinstance(correct_answer, str):
            correct_answer = correct_answer.lower() in ["true", "yes", "1", "да"]
        
        return TrueFalseQuestion(
            question_id=question_id,
            text=text,
            correct_answer=correct_answer,
            points=points,
            time_limit=time_limit,
            explanation=explanation,
            tags=tags
        )
    
    elif question_type == QuestionType.MEDIA_QUESTION.value:
        media_data = question_data.get("media_content", {})
        media_content = MediaContent(
            media_type=media_data.get("media_type", "image"),
            media_url=media_data.get("media_url"),
            media_file=media_data.get("media_file"),
            thumbnail_url=media_data.get("thumbnail_url"),
            description=media_data.get("description")
        )
        
        validation_data = question_data.get("validation_rules", {})
        validation_rules = ValidationRule(
            case_sensitive=validation_data.get("case_sensitive", False),
            exact_match=validation_data.get("exact_match", False),
            allow_partial=validation_data.get("allow_partial", True),
            similarity_threshold=validation_data.get("similarity_threshold", 0.8)
        )
        
        return MediaQuestion(
            question_id=question_id,
            text=text,
            media_content=media_content,
            correct_answers=question_data.get("correct_answers", []),
            validation_rules=validation_rules,
            points=points,
            time_limit=time_limit,
            explanation=explanation,
            tags=tags
        )
    
    elif question_type == QuestionType.VALIDATION_REQUIRED.value:
        return ValidationRequiredQuestion(
            question_id=question_id,
            text=text,
            validation_criteria=question_data.get("validation_criteria", ""),
            points=points,
            time_limit=time_limit,
            explanation=explanation,
            tags=tags
        )
    
    elif question_type == QuestionType.TIMED_QUESTION.value:
        return TimedQuestion(
            question_id=question_id,
            text=text,
            correct_answers=question_data.get("correct_answers", []),
            time_bonus_multiplier=question_data.get("time_bonus_multiplier", 1.5),
            minimum_time_for_bonus=question_data.get("minimum_time_for_bonus", 5),
            points=points,
            time_limit=time_limit,
            explanation=explanation,
            tags=tags
        )
    
    elif question_type == QuestionType.WEIGHTED_QUESTION.value:
        return WeightedQuestion(
            question_id=question_id,
            text=text,
            correct_answers=question_data.get("correct_answers", []),
            difficulty_level=question_data.get("difficulty_level", "medium"),
            point_multipliers=question_data.get("point_multipliers"),
            points=points,
            time_limit=time_limit,
            explanation=explanation,
            tags=tags
        )
    
    else:  # Default to text input
        validation_data = question_data.get("validation_rules", {})
        validation_rules = ValidationRule(
            case_sensitive=validation_data.get("case_sensitive", False),
            exact_match=validation_data.get("exact_match", False),
            allow_partial=validation_data.get("allow_partial", True),
            similarity_threshold=validation_data.get("similarity_threshold", 0.8)
        )
        
        return TextInputQuestion(
            question_id=question_id,
            text=text,
            correct_answers=question_data.get("correct_answers", []),
            validation_rules=validation_rules,
            points=points,
            time_limit=time_limit,
            explanation=explanation,
            tags=tags
        )