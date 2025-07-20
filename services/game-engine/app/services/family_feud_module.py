"""
Game Engine Service - Family Feud Module
"""

from typing import Dict, Any, List
import re
from .module_loader import GameModule


class FamilyFeudModule(GameModule):
    """Family Feud game module implementation"""
    
    def __init__(self):
        super().__init__(
            name="Family Feud",
            version="1.0.0",
            description="Family Feud style survey game module"
        )
    
    def get_supported_question_types(self) -> List[str]:
        """Get list of supported question types"""
        return [
            "survey_question",
            "fast_money_round"
        ]
    
    def get_config_schema(self) -> Dict[str, Any]:
        """Get configuration schema for this module"""
        return {
            "type": "object",
            "properties": {
                "rounds": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10,
                    "default": 5,
                    "description": "Number of survey rounds"
                },
                "strikes_allowed": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 5,
                    "default": 3,
                    "description": "Number of strikes allowed per round"
                },
                "fast_money_time": {
                    "type": "integer",
                    "minimum": 15,
                    "maximum": 60,
                    "default": 20,
                    "description": "Time limit for fast money round in seconds"
                },
                "winning_score": {
                    "type": "integer",
                    "minimum": 100,
                    "maximum": 1000,
                    "default": 300,
                    "description": "Score needed to win the game"
                },
                "case_sensitive": {
                    "type": "boolean",
                    "default": False,
                    "description": "Case sensitive answer matching"
                }
            },
            "required": ["rounds", "strikes_allowed"]
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
        
        if question_type == "survey_question":
            if "answers" not in question_data:
                errors.append("Survey questions must have 'answers' field")
            elif not isinstance(question_data["answers"], list):
                errors.append("'answers' must be a list")
            else:
                answers = question_data["answers"]
                if len(answers) == 0:
                    errors.append("Survey questions must have at least one answer")
                
                for i, answer in enumerate(answers):
                    if not isinstance(answer, dict):
                        errors.append(f"Answer {i+1} must be a dictionary")
                        continue
                    
                    if "text" not in answer:
                        errors.append(f"Answer {i+1} missing 'text' field")
                    
                    if "points" not in answer:
                        errors.append(f"Answer {i+1} missing 'points' field")
                    elif not isinstance(answer["points"], int) or answer["points"] < 0:
                        errors.append(f"Answer {i+1} 'points' must be a non-negative integer")
        
        elif question_type == "fast_money_round":
            if "questions" not in question_data:
                errors.append("Fast money rounds must have 'questions' field")
            elif not isinstance(question_data["questions"], list):
                errors.append("'questions' must be a list")
            else:
                questions = question_data["questions"]
                if len(questions) != 5:
                    warnings.append("Fast money rounds typically have exactly 5 questions")
                
                for i, sub_question in enumerate(questions):
                    if not isinstance(sub_question, dict):
                        errors.append(f"Fast money question {i+1} must be a dictionary")
                        continue
                    
                    if "question" not in sub_question:
                        errors.append(f"Fast money question {i+1} missing 'question' field")
                    
                    if "top_answer" not in sub_question:
                        errors.append(f"Fast money question {i+1} missing 'top_answer' field")
                    
                    if "points" not in sub_question:
                        errors.append(f"Fast money question {i+1} missing 'points' field")
        
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
            "round_number": session_data.get("current_round", 1)
        }
        
        question_type = question_data.get("type")
        
        if question_type == "survey_question":
            # Only show the number of answers, not the actual answers
            answers = question_data.get("answers", [])
            processed_question["answer_count"] = len(answers)
            processed_question["revealed_answers"] = []  # Answers revealed during gameplay
            processed_question["strikes"] = 0
            processed_question["max_strikes"] = session_data.get("strikes_allowed", 3)
        
        elif question_type == "fast_money_round":
            questions = question_data.get("questions", [])
            processed_question["questions"] = [
                {
                    "question": q.get("question"),
                    "answered": False,
                    "points": 0
                }
                for q in questions
            ]
            processed_question["time_limit"] = session_data.get("fast_money_time", 20)
        
        return processed_question
    
    def validate_answer(self, answer: str, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate player answer"""
        question_type = question_data.get("type")
        is_correct = False
        points_earned = 0
        matched_answer = None
        explanation = None
        
        if question_type == "survey_question":
            answers = question_data.get("answers", [])
            case_sensitive = question_data.get("case_sensitive", False)
            
            if not case_sensitive:
                answer = answer.lower().strip()
            
            # Check for exact or partial matches
            best_match = None
            best_similarity = 0
            
            for survey_answer in answers:
                answer_text = survey_answer.get("text", "")
                if not case_sensitive:
                    answer_text = answer_text.lower().strip()
                
                # Check exact match first
                if answer == answer_text:
                    best_match = survey_answer
                    best_similarity = 1.0
                    break
                
                # Check partial match
                similarity = self._calculate_similarity(answer, answer_text)
                if similarity > best_similarity and similarity > 0.7:  # 70% similarity threshold
                    best_match = survey_answer
                    best_similarity = similarity
            
            if best_match:
                is_correct = True
                points_earned = best_match.get("points", 0)
                matched_answer = best_match.get("text")
        
        elif question_type == "fast_money_round":
            # For fast money, we need to check against specific question
            question_index = question_data.get("question_index", 0)
            questions = question_data.get("questions", [])
            
            if question_index < len(questions):
                target_question = questions[question_index]
                top_answer = target_question.get("top_answer", "")
                
                case_sensitive = question_data.get("case_sensitive", False)
                if not case_sensitive:
                    answer = answer.lower().strip()
                    top_answer = top_answer.lower().strip()
                
                similarity = self._calculate_similarity(answer, top_answer)
                if similarity > 0.6:  # 60% similarity for fast money
                    is_correct = True
                    points_earned = target_question.get("points", 0)
                    matched_answer = target_question.get("top_answer")
        
        return {
            "is_correct": is_correct,
            "points_earned": points_earned,
            "matched_answer": matched_answer,
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
        
        # Family Feud specific metrics
        strikes = session_data.get("total_strikes", 0)
        rounds_completed = session_data.get("rounds_completed", 0)
        fast_money_score = session_data.get("fast_money_score", 0)
        
        return {
            "total_questions": total_questions,
            "correct_answers": correct_answers,
            "total_score": total_score,
            "strikes": strikes,
            "rounds_completed": rounds_completed,
            "fast_money_score": fast_money_score,
            "performance": self._calculate_performance(total_score, strikes)
        }
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings"""
        # Simple word-based similarity for Family Feud answers
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 and not words2:
            return 1.0
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def _calculate_performance(self, score: int, strikes: int) -> str:
        """Calculate performance rating"""
        if score >= 200 and strikes <= 2:
            return "Excellent"
        elif score >= 150 and strikes <= 4:
            return "Good"
        elif score >= 100 and strikes <= 6:
            return "Average"
        elif score >= 50:
            return "Below Average"
        else:
            return "Poor"
    
    def reveal_answer(self, question_data: Dict[str, Any], answer_index: int) -> Dict[str, Any]:
        """Reveal a specific answer on the board"""
        answers = question_data.get("answers", [])
        if 0 <= answer_index < len(answers):
            return {
                "text": answers[answer_index].get("text"),
                "points": answers[answer_index].get("points"),
                "index": answer_index
            }
        return None
    
    def get_board_state(self, question_data: Dict[str, Any], revealed_indices: List[int]) -> Dict[str, Any]:
        """Get current board state with revealed answers"""
        answers = question_data.get("answers", [])
        board = []
        
        for i, answer in enumerate(answers):
            if i in revealed_indices:
                board.append({
                    "text": answer.get("text"),
                    "points": answer.get("points"),
                    "revealed": True
                })
            else:
                board.append({
                    "text": "?" * len(answer.get("text", "")),
                    "points": answer.get("points"),
                    "revealed": False
                })
        
        return {
            "answers": board,
            "total_points": sum(answer.get("points", 0) for i, answer in enumerate(answers) if i in revealed_indices)
        }