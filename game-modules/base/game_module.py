"""
Base Game Module
Abstract base class for all game modules with unified interface
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import logging
import structlog

logger = structlog.get_logger()


@dataclass
class Question:
    """Question data structure"""
    id: str
    content: Dict[str, Any]
    question_type: str
    correct_answers: List[str]
    points: int
    time_limit: int
    requires_validation: bool = False
    explanation: Optional[str] = None
    tags: Optional[List[str]] = None
    order: Optional[int] = None
    media_url: Optional[str] = None


@dataclass
class Answer:
    """Answer data structure"""
    user_id: str
    question_id: str
    session_id: str
    answer_text: str
    answered_at: datetime
    is_correct: Optional[bool] = None
    points_earned: int = 0
    time_taken: Optional[float] = None
    requires_validation: bool = False


@dataclass
class GameSession:
    """Game session data structure"""
    id: str
    game_id: str
    admin_id: str
    players: List[str]
    current_question: Optional[str]
    status: str
    config: Dict[str, Any]
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ModuleError(Exception):
    """Base exception for game module errors"""
    pass


class ValidationError(ModuleError):
    """Exception for validation errors"""
    pass


class ProcessingError(ModuleError):
    """Exception for processing errors"""
    pass


class GameModule(ABC):
    """Abstract base class for game modules with unified interface"""
    
    def __init__(self, game_type: str, name: Optional[str] = None, version: str = "1.0.0", description: Optional[str] = None):
        self.game_type = game_type
        self.name = name or self.__class__.__name__
        self.version = version
        self.description = description or f"{self.name} game module"
        self.logger = structlog.get_logger().bind(module=self.name, game_type=game_type)
    
    # Core abstract methods that must be implemented
    @abstractmethod
    async def process_question(self, question: Union[Question, Dict[str, Any]], session: Union[GameSession, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process a question for the specific game type
        
        Args:
            question: The question to process (Question object or dict)
            session: Current game session (GameSession object or dict)
            
        Returns:
            Dict containing processed question data
        """
        pass
    
    @abstractmethod
    async def validate_answer(self, answer: Union[Answer, str], question: Union[Question, Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """
        Validate a player's answer
        
        Args:
            answer: The player's answer (Answer object or string)
            question: The question being answered (Question object or dict)
            **kwargs: Additional validation parameters
            
        Returns:
            Dict containing validation result
        """
        pass
    
    @abstractmethod
    async def calculate_score(self, answers: List[Union[Answer, Dict[str, Any]]], question: Union[Question, Dict[str, Any]]) -> Dict[str, int]:
        """
        Calculate scores for players based on their answers
        
        Args:
            answers: List of player answers
            question: The question being scored
            
        Returns:
            Dict mapping user_id to score
        """
        pass
    
    @abstractmethod
    async def get_results(self, session: Union[GameSession, Dict[str, Any]], all_answers: List[Union[Answer, Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Get final results for the game session
        
        Args:
            session: The completed game session
            all_answers: All answers from the session
            
        Returns:
            Dict containing game results
        """
        pass
    
    @abstractmethod
    def get_supported_question_types(self) -> List[str]:
        """
        Get list of question types supported by this module
        
        Returns:
            List of supported question type strings
        """
        pass
    
    # Optional methods with default implementations
    async def initialize_session(self, session: Union[GameSession, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Initialize a new game session (optional override)
        
        Args:
            session: The new game session
            
        Returns:
            Dict containing initialization data
        """
        session_id = session.id if isinstance(session, GameSession) else session.get("id", "unknown")
        self.logger.info("Session initialized", session_id=session_id)
        return {"status": "initialized", "game_type": self.game_type, "module": self.name}
    
    async def finalize_session(self, session: Union[GameSession, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Finalize a completed game session (optional override)
        
        Args:
            session: The completed game session
            
        Returns:
            Dict containing finalization data
        """
        session_id = session.id if isinstance(session, GameSession) else session.get("id", "unknown")
        self.logger.info("Session finalized", session_id=session_id)
        return {"status": "finalized", "game_type": self.game_type, "module": self.name}
    
    def validate_game_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate game configuration for this module
        
        Args:
            config: Game configuration to validate
            
        Returns:
            Dict with validation results
        """
        try:
            # Basic validation - can be overridden by subclasses
            errors = []
            warnings = []
            
            # Check for common config fields
            if "time_limit" in config:
                if not isinstance(config["time_limit"], int) or config["time_limit"] < 5:
                    errors.append("time_limit must be an integer >= 5")
            
            if "points_per_question" in config:
                if not isinstance(config["points_per_question"], int) or config["points_per_question"] < 1:
                    errors.append("points_per_question must be an integer >= 1")
            
            return {
                "is_valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings
            }
        except Exception as e:
            self.logger.error("Config validation error", error=str(e))
            return {
                "is_valid": False,
                "errors": [f"Validation error: {str(e)}"],
                "warnings": []
            }
    
    def get_default_config(self) -> Dict[str, Any]:
        """
        Get default configuration for this game type
        
        Returns:
            Dict containing default configuration
        """
        return {
            "time_limit": 30,
            "points_per_question": 10,
            "max_players": 100,
            "allow_late_join": True
        }
    
    def get_config_schema(self) -> Dict[str, Any]:
        """
        Get configuration schema for this module (for validation)
        
        Returns:
            JSON schema dict for configuration validation
        """
        return {
            "type": "object",
            "properties": {
                "time_limit": {
                    "type": "integer",
                    "minimum": 5,
                    "maximum": 600,
                    "default": 30
                },
                "points_per_question": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 1000,
                    "default": 10
                }
            }
        }
    
    def validate_question(self, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate question data for this module
        
        Args:
            question_data: Question data to validate
            
        Returns:
            Dict with validation results
        """
        try:
            errors = []
            warnings = []
            
            # Basic validation
            if "id" not in question_data:
                errors.append("Missing 'id' field")
            
            if "text" not in question_data and "question" not in question_data:
                errors.append("Missing 'text' or 'question' field")
            
            if "type" not in question_data:
                errors.append("Missing 'type' field")
            elif question_data["type"] not in self.get_supported_question_types():
                errors.append(f"Unsupported question type: {question_data['type']}")
            
            # Points validation
            if "points" in question_data:
                if not isinstance(question_data["points"], int) or question_data["points"] < 1:
                    errors.append("'points' must be a positive integer")
            
            # Time limit validation
            if "time_limit" in question_data:
                if not isinstance(question_data["time_limit"], int) or question_data["time_limit"] < 5:
                    errors.append("'time_limit' must be an integer >= 5")
            
            return {
                "is_valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings
            }
        except Exception as e:
            self.logger.error("Question validation error", error=str(e))
            return {
                "is_valid": False,
                "errors": [f"Validation error: {str(e)}"],
                "warnings": []
            }
    
    def get_module_info(self) -> Dict[str, Any]:
        """
        Get module information
        
        Returns:
            Dict containing module metadata
        """
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "game_type": self.game_type,
            "supported_question_types": self.get_supported_question_types(),
            "config_schema": self.get_config_schema(),
            "default_config": self.get_default_config()
        }
    
    # Utility methods for data conversion
    def _convert_to_question(self, question_data: Union[Question, Dict[str, Any]]) -> Question:
        """Convert question data to Question object"""
        if isinstance(question_data, Question):
            return question_data
        
        return Question(
            id=question_data.get("id", ""),
            content=question_data.get("content", question_data),
            question_type=question_data.get("type", "text_input"),
            correct_answers=question_data.get("correct_answers", []),
            points=question_data.get("points", 10),
            time_limit=question_data.get("time_limit", 30),
            requires_validation=question_data.get("requires_validation", False),
            explanation=question_data.get("explanation"),
            tags=question_data.get("tags"),
            order=question_data.get("order"),
            media_url=question_data.get("media_url")
        )
    
    def _convert_to_session(self, session_data: Union[GameSession, Dict[str, Any]]) -> GameSession:
        """Convert session data to GameSession object"""
        if isinstance(session_data, GameSession):
            return session_data
        
        return GameSession(
            id=session_data.get("id", ""),
            game_id=session_data.get("game_id", ""),
            admin_id=session_data.get("admin_id", ""),
            players=session_data.get("players", []),
            current_question=session_data.get("current_question"),
            status=session_data.get("status", "waiting"),
            config=session_data.get("config", {}),
            created_at=session_data.get("created_at", datetime.utcnow()),
            started_at=session_data.get("started_at"),
            completed_at=session_data.get("completed_at")
        )
    
    def _convert_to_answer(self, answer_data: Union[Answer, Dict[str, Any]], answer_text: Optional[str] = None) -> Answer:
        """Convert answer data to Answer object"""
        if isinstance(answer_data, Answer):
            return answer_data
        
        if isinstance(answer_data, str):
            # If answer_data is a string, it's the answer text
            return Answer(
                user_id="",
                question_id="",
                session_id="",
                answer_text=answer_data,
                answered_at=datetime.utcnow()
            )
        
        return Answer(
            user_id=answer_data.get("user_id", ""),
            question_id=answer_data.get("question_id", ""),
            session_id=answer_data.get("session_id", ""),
            answer_text=answer_text or answer_data.get("answer_text", ""),
            answered_at=answer_data.get("answered_at", datetime.utcnow()),
            is_correct=answer_data.get("is_correct"),
            points_earned=answer_data.get("points_earned", 0),
            time_taken=answer_data.get("time_taken"),
            requires_validation=answer_data.get("requires_validation", False)
        )
    
    def __str__(self):
        return f"{self.name} v{self.version} ({self.game_type})"
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(name='{self.name}', game_type='{self.game_type}', version='{self.version}')>"