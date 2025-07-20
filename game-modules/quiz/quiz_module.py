"""
Quiz Game Module - Comprehensive Implementation
Handles all types of quiz questions with advanced features
"""

from typing import Dict, Any, List, Union, Optional
from datetime import datetime
import re
import asyncio
import structlog

from ..base.game_module import GameModule, Question, Answer, GameSession, ValidationError, ProcessingError
from .question_types import (
    QuestionType, BaseQuestion, MultipleChoiceQuestion, TextInputQuestion, 
    TrueFalseQuestion, MediaQuestion, ValidationRequiredQuestion, 
    TimedQuestion, WeightedQuestion, create_question_from_dict
)
from .schemas import (
    QuizConfigSchema, QuestionSchema, AnswerSchema, ValidationResultSchema,
    QuizResultsSchema, PlayerStatsSchema, validate_question_by_type
)

logger = structlog.get_logger()


class QuizModule(GameModule):
    """Comprehensive quiz game module implementation"""
    
    def __init__(self):
        super().__init__(
            game_type="quiz",
            name="Advanced Quiz Module",
            version="2.0.0",
            description="Comprehensive quiz module with multiple question types and advanced scoring"
        )
        self.question_cache = {}
        self.validation_cache = {}
    
    def get_supported_question_types(self) -> List[str]:
        """Get list of supported question types"""
        return [
            QuestionType.MULTIPLE_CHOICE.value,
            QuestionType.TEXT_INPUT.value,
            QuestionType.TRUE_FALSE.value,
            QuestionType.MEDIA_QUESTION.value,
            QuestionType.VALIDATION_REQUIRED.value,
            QuestionType.TIMED_QUESTION.value,
            QuestionType.WEIGHTED_QUESTION.value
        ]
    
    def get_config_schema(self) -> Dict[str, Any]:
        """Get configuration schema for quiz module"""
        return {
            "type": "object",
            "properties": {
                "time_limit": {
                    "type": "integer",
                    "minimum": 5,
                    "maximum": 600,
                    "default": 30,
                    "description": "Default time limit per question in seconds"
                },
                "points_per_question": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 1000,
                    "default": 10,
                    "description": "Default points per correct answer"
                },
                "shuffle_options": {
                    "type": "boolean",
                    "default": True,
                    "description": "Shuffle multiple choice options"
                },
                "allow_partial_credit": {
                    "type": "boolean",
                    "default": False,
                    "description": "Allow partial credit for partially correct answers"
                },
                "case_sensitive": {
                    "type": "boolean",
                    "default": False,
                    "description": "Case sensitive text matching"
                },
                "show_correct_answers": {
                    "type": "boolean",
                    "default": True,
                    "description": "Show correct answers after each question"
                },
                "show_explanations": {
                    "type": "boolean",
                    "default": True,
                    "description": "Show explanations after each question"
                },
                "time_bonus_enabled": {
                    "type": "boolean",
                    "default": True,
                    "description": "Enable time-based bonus scoring"
                },
                "difficulty_scaling": {
                    "type": "boolean",
                    "default": False,
                    "description": "Enable difficulty-based point scaling"
                },
                "max_attempts": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 5,
                    "default": 1,
                    "description": "Maximum attempts per question"
                }
            },
            "required": ["time_limit", "points_per_question"]
        }
    
    def get_default_config(self) -> Dict[str, Any]:
        """Get default quiz configuration"""
        return {
            "time_limit": 30,
            "points_per_question": 10,
            "shuffle_options": True,
            "allow_partial_credit": False,
            "case_sensitive": False,
            "show_correct_answers": True,
            "show_explanations": True,
            "time_bonus_enabled": True,
            "difficulty_scaling": False,
            "max_attempts": 1,
            "allow_review": False,
            "auto_advance": True
        }
    
    def validate_question(self, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate question data using Pydantic schemas"""
        try:
            # Use the schema validation
            validated_question = validate_question_by_type(question_data)
            
            return {
                "is_valid": True,
                "errors": [],
                "warnings": [],
                "validated_data": validated_question.dict()
            }
        except Exception as e:
            self.logger.error("Question validation failed", error=str(e), question_id=question_data.get("id"))
            return {
                "is_valid": False,
                "errors": [str(e)],
                "warnings": [],
                "validated_data": None
            }
    
    async def process_question(self, question: Union[Question, Dict[str, Any]], session: Union[GameSession, Dict[str, Any]]) -> Dict[str, Any]:
        """Process a quiz question for display to players"""
        try:
            # Convert to proper objects
            question_obj = self._convert_to_question(question)
            session_obj = self._convert_to_session(session)
            
            # Create question object from data
            question_data = question_obj.content.copy()
            question_data.update({
                "id": question_obj.id,
                "type": question_obj.question_type,
                "text": question_data.get("text", question_data.get("question", "")),
                "points": question_obj.points,
                "time_limit": question_obj.time_limit,
                "explanation": question_obj.explanation,
                "tags": question_obj.tags
            })
            
            # Create typed question object
            typed_question = create_question_from_dict(question_data)
            
            # Get base processed data
            processed = typed_question.to_dict()
            
            # Apply session-specific processing
            if question_obj.question_type == QuestionType.MULTIPLE_CHOICE.value:
                # Shuffle options if configured
                if session_obj.config.get("shuffle_options", True) and "options" in processed:
                    import random
                    options = processed["options"].copy()
                    random.shuffle(options)
                    processed["options"] = options
            
            # Remove sensitive data that shouldn't be sent to players
            sensitive_fields = ["correct_answers", "validation_rules"]
            for field in sensitive_fields:
                processed.pop(field, None)
            
            # Add session context
            processed.update({
                "session_id": session_obj.id,
                "requires_validation": question_obj.requires_validation,
                "media_url": question_obj.media_url
            })
            
            # Cache the original question for validation
            self.question_cache[question_obj.id] = typed_question
            
            self.logger.info("Question processed", 
                           question_id=question_obj.id, 
                           question_type=question_obj.question_type,
                           session_id=session_obj.id)
            
            return processed
            
        except Exception as e:
            self.logger.error("Error processing question", error=str(e))
            raise ProcessingError(f"Failed to process question: {str(e)}")
    
    async def validate_answer(self, answer: Union[Answer, str], question: Union[Question, Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """Validate a player's answer"""
        try:
            # Handle different answer formats
            if isinstance(answer, str):
                answer_text = answer
                time_taken = kwargs.get("time_taken")
            else:
                answer_obj = self._convert_to_answer(answer)
                answer_text = answer_obj.answer_text
                time_taken = answer_obj.time_taken or kwargs.get("time_taken")
            
            # Get question object
            question_obj = self._convert_to_question(question)
            
            # Try to get cached question object, otherwise create new one
            typed_question = self.question_cache.get(question_obj.id)
            if not typed_question:
                question_data = question_obj.content.copy()
                question_data.update({
                    "id": question_obj.id,
                    "type": question_obj.question_type,
                    "text": question_data.get("text", question_data.get("question", "")),
                    "points": question_obj.points,
                    "time_limit": question_obj.time_limit,
                    "correct_answers": question_obj.correct_answers
                })
                typed_question = create_question_from_dict(question_data)
            
            # Validate answer using the typed question
            if isinstance(typed_question, TimedQuestion) and time_taken is not None:
                validation_result = typed_question.validate_answer(answer_text, time_taken)
            else:
                validation_result = typed_question.validate_answer(answer_text)
            
            # Apply additional processing based on question type
            if question_obj.requires_validation and validation_result.get("is_correct") is None:
                validation_result["requires_manual_validation"] = True
            
            # Cache validation result
            cache_key = f"{question_obj.id}:{answer_text}"
            self.validation_cache[cache_key] = validation_result
            
            self.logger.info("Answer validated", 
                           question_id=question_obj.id,
                           is_correct=validation_result.get("is_correct"),
                           points_earned=validation_result.get("points_earned", 0))
            
            return validation_result
            
        except Exception as e:
            self.logger.error("Error validating answer", error=str(e))
            raise ValidationError(f"Failed to validate answer: {str(e)}")
    
    async def calculate_score(self, answers: List[Union[Answer, Dict[str, Any]]], question: Union[Question, Dict[str, Any]]) -> Dict[str, int]:
        """Calculate scores for all players"""
        try:
            scores = {}
            question_obj = self._convert_to_question(question)
            
            for answer_data in answers:
                answer_obj = self._convert_to_answer(answer_data)
                
                # Validate the answer if not already done
                cache_key = f"{question_obj.id}:{answer_obj.answer_text}"
                if cache_key in self.validation_cache:
                    validation_result = self.validation_cache[cache_key]
                else:
                    validation_result = await self.validate_answer(answer_obj, question_obj)
                
                # Assign score
                if validation_result.get("is_correct"):
                    scores[answer_obj.user_id] = validation_result.get("points_earned", 0)
                else:
                    scores[answer_obj.user_id] = 0
            
            return scores
            
        except Exception as e:
            self.logger.error("Error calculating scores", error=str(e))
            return {}
    
    async def get_results(self, session: Union[GameSession, Dict[str, Any]], all_answers: List[Union[Answer, Dict[str, Any]]]) -> Dict[str, Any]:
        """Get comprehensive quiz results"""
        try:
            session_obj = self._convert_to_session(session)
            
            # Initialize player statistics
            player_stats = {}
            for player_id in session_obj.players:
                player_stats[player_id] = {
                    "user_id": player_id,
                    "total_score": 0,
                    "correct_answers": 0,
                    "total_answers": 0,
                    "accuracy": 0.0,
                    "average_time": 0.0,
                    "time_bonus_points": 0,
                    "difficulty_bonus_points": 0,
                    "questions_attempted": set(),
                    "total_time": 0.0
                }
            
            # Process all answers
            questions_requiring_validation = []
            total_questions = set()
            
            for answer_data in all_answers:
                answer_obj = self._convert_to_answer(answer_data)
                
                if answer_obj.user_id not in player_stats:
                    continue
                
                stats = player_stats[answer_obj.user_id]
                stats["total_answers"] += 1
                stats["questions_attempted"].add(answer_obj.question_id)
                total_questions.add(answer_obj.question_id)
                
                # Add to total score and correct answers
                if answer_obj.is_correct:
                    stats["correct_answers"] += 1
                
                stats["total_score"] += answer_obj.points_earned
                
                # Track time
                if answer_obj.time_taken:
                    stats["total_time"] += answer_obj.time_taken
                
                # Track validation requirements
                if answer_obj.requires_validation:
                    questions_requiring_validation.append(answer_obj.question_id)
            
            # Calculate final statistics
            leaderboard = []
            total_score_sum = 0
            total_accuracy_sum = 0
            active_players = 0
            
            for player_id, stats in player_stats.items():
                if stats["total_answers"] > 0:
                    # Calculate accuracy
                    stats["accuracy"] = (stats["correct_answers"] / stats["total_answers"]) * 100
                    
                    # Calculate average time
                    if stats["total_time"] > 0:
                        stats["average_time"] = stats["total_time"] / stats["total_answers"]
                    
                    # Remove temporary fields
                    stats.pop("questions_attempted", None)
                    stats.pop("total_time", None)
                    
                    leaderboard.append(stats)
                    total_score_sum += stats["total_score"]
                    total_accuracy_sum += stats["accuracy"]
                    active_players += 1
            
            # Sort leaderboard by score (descending), then by accuracy, then by average time
            leaderboard.sort(key=lambda x: (-x["total_score"], -x["accuracy"], x["average_time"]))
            
            # Add rankings
            for i, player in enumerate(leaderboard, 1):
                player["rank"] = i
            
            # Calculate session metrics
            session_duration = 0
            if session_obj.started_at and session_obj.completed_at:
                session_duration = int((session_obj.completed_at - session_obj.started_at).total_seconds())
            elif session_obj.started_at:
                session_duration = int((datetime.utcnow() - session_obj.started_at).total_seconds())
            
            completion_rate = 0.0
            if len(session_obj.players) > 0 and len(total_questions) > 0:
                completed_players = len([p for p in leaderboard if p["total_answers"] > 0])
                completion_rate = (completed_players / len(session_obj.players)) * 100
            
            average_score = total_score_sum / active_players if active_players > 0 else 0.0
            average_accuracy = total_accuracy_sum / active_players if active_players > 0 else 0.0
            
            results = {
                "game_type": self.game_type,
                "session_id": session_obj.id,
                "total_players": len(session_obj.players),
                "active_players": active_players,
                "total_questions": len(total_questions),
                "session_duration": session_duration,
                "leaderboard": leaderboard,
                "completion_rate": round(completion_rate, 1),
                "average_score": round(average_score, 1),
                "average_accuracy": round(average_accuracy, 1),
                "questions_requiring_validation": list(set(questions_requiring_validation)),
                "module_info": {
                    "name": self.name,
                    "version": self.version
                }
            }
            
            self.logger.info("Results calculated", 
                           session_id=session_obj.id,
                           total_players=len(session_obj.players),
                           active_players=active_players,
                           average_score=average_score)
            
            return results
            
        except Exception as e:
            self.logger.error("Error calculating results", error=str(e))
            raise ProcessingError(f"Failed to calculate results: {str(e)}")
    
    async def initialize_session(self, session: Union[GameSession, Dict[str, Any]]) -> Dict[str, Any]:
        """Initialize quiz session with module-specific setup"""
        try:
            session_obj = self._convert_to_session(session)
            
            # Clear caches for new session
            self.question_cache.clear()
            self.validation_cache.clear()
            
            # Validate session config
            config_validation = self.validate_game_config(session_obj.config)
            if not config_validation["is_valid"]:
                raise ValidationError(f"Invalid session config: {config_validation['errors']}")
            
            # Apply default config for missing values
            default_config = self.get_default_config()
            for key, value in default_config.items():
                if key not in session_obj.config:
                    session_obj.config[key] = value
            
            self.logger.info("Quiz session initialized", 
                           session_id=session_obj.id,
                           player_count=len(session_obj.players))
            
            return {
                "status": "initialized",
                "game_type": self.game_type,
                "module": self.name,
                "config": session_obj.config,
                "supported_question_types": self.get_supported_question_types()
            }
            
        except Exception as e:
            self.logger.error("Error initializing session", error=str(e))
            raise ProcessingError(f"Failed to initialize session: {str(e)}")
    
    async def finalize_session(self, session: Union[GameSession, Dict[str, Any]]) -> Dict[str, Any]:
        """Finalize quiz session with cleanup"""
        try:
            session_obj = self._convert_to_session(session)
            
            # Clean up caches
            cache_size = len(self.question_cache) + len(self.validation_cache)
            self.question_cache.clear()
            self.validation_cache.clear()
            
            self.logger.info("Quiz session finalized", 
                           session_id=session_obj.id,
                           cache_cleared=cache_size)
            
            return {
                "status": "finalized",
                "game_type": self.game_type,
                "module": self.name,
                "cache_cleared": cache_size
            }
            
        except Exception as e:
            self.logger.error("Error finalizing session", error=str(e))
            return {
                "status": "error",
                "error": str(e)
            }
    
    # Additional utility methods
    async def get_question_statistics(self, question_id: str, answers: List[Union[Answer, Dict[str, Any]]]) -> Dict[str, Any]:
        """Get statistics for a specific question"""
        try:
            stats = {
                "question_id": question_id,
                "total_answers": 0,
                "correct_answers": 0,
                "accuracy": 0.0,
                "average_time": 0.0,
                "answer_distribution": {},
                "common_mistakes": []
            }
            
            total_time = 0.0
            answer_texts = []
            
            for answer_data in answers:
                answer_obj = self._convert_to_answer(answer_data)
                if answer_obj.question_id != question_id:
                    continue
                
                stats["total_answers"] += 1
                answer_texts.append(answer_obj.answer_text)
                
                if answer_obj.is_correct:
                    stats["correct_answers"] += 1
                
                if answer_obj.time_taken:
                    total_time += answer_obj.time_taken
                
                # Track answer distribution
                answer_key = answer_obj.answer_text.lower().strip()
                stats["answer_distribution"][answer_key] = stats["answer_distribution"].get(answer_key, 0) + 1
            
            # Calculate final statistics
            if stats["total_answers"] > 0:
                stats["accuracy"] = (stats["correct_answers"] / stats["total_answers"]) * 100
                if total_time > 0:
                    stats["average_time"] = total_time / stats["total_answers"]
            
            # Find common mistakes (most frequent incorrect answers)
            incorrect_answers = {}
            for answer_data in answers:
                answer_obj = self._convert_to_answer(answer_data)
                if answer_obj.question_id == question_id and not answer_obj.is_correct:
                    key = answer_obj.answer_text.lower().strip()
                    incorrect_answers[key] = incorrect_answers.get(key, 0) + 1
            
            # Sort by frequency and take top 3
            stats["common_mistakes"] = sorted(incorrect_answers.items(), key=lambda x: x[1], reverse=True)[:3]
            
            return stats
            
        except Exception as e:
            self.logger.error("Error calculating question statistics", error=str(e))
            return {"error": str(e)}
    
    async def export_session_data(self, session: Union[GameSession, Dict[str, Any]], answers: List[Union[Answer, Dict[str, Any]]], format: str = "json") -> Dict[str, Any]:
        """Export session data in various formats"""
        try:
            session_obj = self._convert_to_session(session)
            results = await self.get_results(session, answers)
            
            export_data = {
                "session": {
                    "id": session_obj.id,
                    "game_id": session_obj.game_id,
                    "admin_id": session_obj.admin_id,
                    "status": session_obj.status,
                    "config": session_obj.config,
                    "created_at": session_obj.created_at.isoformat() if session_obj.created_at else None,
                    "started_at": session_obj.started_at.isoformat() if session_obj.started_at else None,
                    "completed_at": session_obj.completed_at.isoformat() if session_obj.completed_at else None
                },
                "results": results,
                "answers": [
                    {
                        "user_id": self._convert_to_answer(a).user_id,
                        "question_id": self._convert_to_answer(a).question_id,
                        "answer_text": self._convert_to_answer(a).answer_text,
                        "is_correct": self._convert_to_answer(a).is_correct,
                        "points_earned": self._convert_to_answer(a).points_earned,
                        "time_taken": self._convert_to_answer(a).time_taken,
                        "answered_at": self._convert_to_answer(a).answered_at.isoformat()
                    }
                    for a in answers
                ],
                "export_metadata": {
                    "exported_at": datetime.utcnow().isoformat(),
                    "format": format,
                    "module": self.name,
                    "version": self.version
                }
            }
            
            return export_data
            
        except Exception as e:
            self.logger.error("Error exporting session data", error=str(e))
            raise ProcessingError(f"Failed to export session data: {str(e)}")