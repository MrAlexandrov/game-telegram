"""
Game Engine Service - Quiz Module
"""

from typing import Dict, Any, List
import re
from .module_loader import GameModule


class QuizModule(GameModule):
    """Quiz game module implementation"""
    
    def __init__(self):
        super().__init__(
            name="Quiz",
            version="1.0.0",
            description="Multiple choice and text-based quiz game module"
        )
    
    def get_supported_question_types(self) -> List[str]:
        """Get list of supported question types"""
        return [
            "multiple_choice",
            "text_input",
            "true_false",
            "media_question"
        ]
    
    def get_config_schema(self) -> Dict[str, Any]:
        """Get configuration schema for this module"""
        return {
            "type": "object",
            "properties": {
                "time_limit": {
                    "type": "integer",
                    "minimum": 5,
                    "maximum": 300,
                    "default": 30,
                    "description": "Default time limit per question in seconds"
                },
                "points_per_question": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 100,
                    "default": 10,
                    "description": "Default points per correct answer"
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
                }
            },
            "required": ["time_limit", "points_per_question"]
        }
    
    def validate_question(self, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate question data"""
        errors = []
        warnings = []
        
        # Check required fields
        if "question" not in question_data:
            errors.append("Missing 'question' field")
        
        if "type" not in question_data:
            errors.append("Missing 'type' field")
        elif question_data["type"] not in self.get_supported_question_types():
            errors.append(f"Unsupported question type: {question_data['type']}")
        
        # Validate based on question type
        question_type = question_data.get("type")
        
        if question_type == "multiple_choice":
            if "options" not in question_data:
                errors.append("Multiple choice questions must have 'options' field")
            elif not isinstance(question_data["options"], list) or len(question_data["options"]) < 2:
                errors.append("Multiple choice questions must have at least 2 options")
            
            if "correct_answer" not in question_data:
                errors.append("Multiple choice questions must have 'correct_answer' field")
            elif question_data["correct_answer"] not in question_data.get("options", []):
                errors.append("Correct answer must be one of the options")
        
        elif question_type == "text_input":
            if "correct_answers" not in question_data:
                errors.append("Text input questions must have 'correct_answers' field")
            elif not isinstance(question_data["correct_answers"], list):
                errors.append("'correct_answers' must be a list")
        
        elif question_type == "true_false":
            if "correct_answer" not in question_data:
                errors.append("True/false questions must have 'correct_answer' field")
            elif question_data["correct_answer"] not in [True, False, "true", "false"]:
                errors.append("True/false correct answer must be boolean or 'true'/'false' string")
        
        elif question_type == "media_question":
            if "media_url" not in question_data and "media_file" not in question_data:
                warnings.append("Media questions should have 'media_url' or 'media_file' field")
        
        # Check optional fields
        if "points" in question_data and not isinstance(question_data["points"], int):
            errors.append("'points' field must be an integer")
        
        if "time_limit" in question_data and not isinstance(question_data["time_limit"], int):
            errors.append("'time_limit' field must be an integer")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def process_question(self, question_data: Dict[str, Any], session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a question for the game session"""
        processed_question = {
            "id": question_data.get("id"),
            "question": question_data.get("question"),
            "type": question_data.get("type"),
            "points": question_data.get("points", 10),
            "time_limit": question_data.get("time_limit", 30)
        }
        
        question_type = question_data.get("type")
        
        if question_type == "multiple_choice":
            processed_question["options"] = question_data.get("options", [])
        
        elif question_type == "media_question":
            processed_question["media_url"] = question_data.get("media_url")
            processed_question["media_file"] = question_data.get("media_file")
        
        # Don't include correct answers in processed question for security
        return processed_question
    
    def validate_answer(self, answer: str, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate player answer"""
        question_type = question_data.get("type")
        is_correct = False
        points_earned = 0
        explanation = None
        
        if question_type == "multiple_choice":
            correct_answer = question_data.get("correct_answer")
            is_correct = answer == correct_answer
            points_earned = question_data.get("points", 10) if is_correct else 0
        
        elif question_type == "text_input":
            correct_answers = question_data.get("correct_answers", [])
            case_sensitive = question_data.get("case_sensitive", False)
            
            if not case_sensitive:
                answer = answer.lower()
                correct_answers = [ans.lower() for ans in correct_answers]
            
            # Check exact matches first
            is_correct = answer in correct_answers
            
            # Check partial matches if allowed
            if not is_correct and question_data.get("allow_partial_credit", False):
                for correct_answer in correct_answers:
                    similarity = self._calculate_similarity(answer, correct_answer)
                    if similarity > 0.8:  # 80% similarity threshold
                        is_correct = True
                        points_earned = int(question_data.get("points", 10) * similarity)
                        break
            
            if is_correct and points_earned == 0:
                points_earned = question_data.get("points", 10)
        
        elif question_type == "true_false":
            correct_answer = question_data.get("correct_answer")
            if isinstance(correct_answer, str):
                correct_answer = correct_answer.lower() == "true"
            
            answer_bool = answer.lower() in ["true", "yes", "1"] if isinstance(answer, str) else bool(answer)
            is_correct = answer_bool == correct_answer
            points_earned = question_data.get("points", 10) if is_correct else 0
        
        return {
            "is_correct": is_correct,
            "points_earned": points_earned,
            "explanation": explanation
        }
    
    def calculate_score(self, answers: List[Dict[str, Any]], question_data: Dict[str, Any]) -> int:
        """Calculate score for answers"""
        total_score = 0
        for answer in answers:
            total_score += answer.get("points_earned", 0)
        return total_score
    
    def get_results(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get game results"""
        answers = session_data.get("answers", [])
        total_questions = len(session_data.get("questions", []))
        correct_answers = sum(1 for answer in answers if answer.get("is_correct", False))
        total_score = sum(answer.get("points_earned", 0) for answer in answers)
        
        accuracy = (correct_answers / total_questions * 100) if total_questions > 0 else 0
        
        return {
            "total_questions": total_questions,
            "correct_answers": correct_answers,
            "total_score": total_score,
            "accuracy": round(accuracy, 2),
            "grade": self._calculate_grade(accuracy)
        }
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings"""
        # Simple Levenshtein distance-based similarity
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
    
    def _calculate_grade(self, accuracy: float) -> str:
        """Calculate letter grade based on accuracy"""
        if accuracy >= 90:
            return "A"
        elif accuracy >= 80:
            return "B"
        elif accuracy >= 70:
            return "C"
        elif accuracy >= 60:
            return "D"
        else:
            return "F"