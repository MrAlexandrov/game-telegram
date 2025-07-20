"""
Game Engine Service - Game Processor
"""

from typing import Dict, Any, Optional
import structlog
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from .module_loader import ModuleLoader
from ..crud import GameCRUD, QuestionCRUD
from ..models.database import AsyncSessionLocal

logger = structlog.get_logger()


class GameProcessor:
    """Game processing service"""
    
    def __init__(self, module_loader: ModuleLoader):
        self.module_loader = module_loader
    
    async def process_question(self, session_id: str, question_id: uuid.UUID, game_type: str) -> Dict[str, Any]:
        """Process a question for a game session"""
        try:
            # Get the game module
            module = self.module_loader.get_module(game_type)
            if not module:
                raise ValueError(f"Unknown game type: {game_type}")
            
            # Get question data from database
            async with AsyncSessionLocal() as db:
                question = await QuestionCRUD.get_question_by_id(db, question_id)
                if not question:
                    raise ValueError(f"Question not found: {question_id}")
                
                # Convert question to dict for processing
                question_data = {
                    "id": str(question.id),
                    "question": question.content.get("question"),
                    "type": question.question_type,
                    "content": question.content,
                    "media_url": question.media_url,
                    "correct_answers": question.correct_answers,
                    "points": question.points,
                    "time_limit": question.time_limit
                }
                
                # Session data (this would typically come from session manager)
                session_data = {
                    "session_id": session_id,
                    "game_type": game_type,
                    "current_round": 1,  # This should come from session state
                    "strikes_allowed": 3,  # This should come from game config
                    "fast_money_time": 20  # This should come from game config
                }
                
                # Process the question
                processed_question = module.process_question(question_data, session_data)
                
                logger.info("Question processed", 
                           session_id=session_id, 
                           question_id=str(question_id),
                           game_type=game_type)
                
                return {
                    "success": True,
                    "question": processed_question,
                    "session_id": session_id
                }
        
        except Exception as e:
            logger.error("Error processing question", 
                        session_id=session_id,
                        question_id=str(question_id),
                        error=str(e))
            return {
                "success": False,
                "error": str(e),
                "session_id": session_id
            }
    
    async def validate_answer(self, answer_id: uuid.UUID, is_correct: bool, points: int) -> Dict[str, Any]:
        """Validate and score a player's answer"""
        try:
            # This is a simplified implementation
            # In a real system, this would interact with the session manager
            # to get the current question and validate the answer using the appropriate module
            
            logger.info("Answer validated", 
                       answer_id=str(answer_id),
                       is_correct=is_correct,
                       points=points)
            
            return {
                "success": True,
                "answer_id": str(answer_id),
                "is_correct": is_correct,
                "points_awarded": points
            }
        
        except Exception as e:
            logger.error("Error validating answer", 
                        answer_id=str(answer_id),
                        error=str(e))
            return {
                "success": False,
                "error": str(e),
                "answer_id": str(answer_id)
            }
    
    async def calculate_results(self, session_id: str) -> Dict[str, Any]:
        """Calculate final results for a game session"""
        try:
            # This would typically get session data from session manager
            # and use the appropriate game module to calculate results
            
            # Placeholder implementation
            results = {
                "session_id": session_id,
                "total_questions": 0,
                "correct_answers": 0,
                "total_score": 0,
                "accuracy": 0.0,
                "completion_time": 0,
                "rank": "N/A"
            }
            
            logger.info("Results calculated", 
                       session_id=session_id,
                       total_score=results["total_score"])
            
            return {
                "success": True,
                "results": results
            }
        
        except Exception as e:
            logger.error("Error calculating results", 
                        session_id=session_id,
                        error=str(e))
            return {
                "success": False,
                "error": str(e),
                "session_id": session_id
            }
    
    async def validate_game_pack(self, game_type: str, pack_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a game pack using the appropriate module"""
        try:
            validation_result = self.module_loader.validate_game_pack(game_type, pack_data)
            
            logger.info("Game pack validated", 
                       game_type=game_type,
                       is_valid=validation_result["is_valid"],
                       error_count=len(validation_result["errors"]))
            
            return validation_result
        
        except Exception as e:
            logger.error("Error validating game pack", 
                        game_type=game_type,
                        error=str(e))
            return {
                "is_valid": False,
                "errors": [f"Validation error: {str(e)}"],
                "warnings": []
            }
    
    async def create_game_from_pack(self, pack_data: Dict[str, Any], created_by: uuid.UUID) -> Dict[str, Any]:
        """Create a game from a validated game pack"""
        try:
            # Extract game metadata
            metadata = pack_data.get("metadata", {})
            game_type = metadata.get("type", "quiz")
            
            # Validate the pack first
            validation_result = await self.validate_game_pack(game_type, pack_data)
            if not validation_result["is_valid"]:
                return {
                    "success": False,
                    "error": "Game pack validation failed",
                    "validation_errors": validation_result["errors"]
                }
            
            async with AsyncSessionLocal() as db:
                # Create the game
                from ..schemas import GameCreate
                game_data = GameCreate(
                    title=metadata.get("title", "Untitled Game"),
                    description=metadata.get("description"),
                    game_type=game_type,
                    config=metadata.get("config", {}),
                    created_by=created_by
                )
                
                game = await GameCRUD.create_game(db, game_data)
                
                # Create questions
                questions = pack_data.get("questions", [])
                created_questions = []
                
                for i, question_data in enumerate(questions):
                    from ..schemas import QuestionCreate
                    question_create = QuestionCreate(
                        game_id=game.id,
                        order_index=i + 1,
                        question_type=question_data.get("type", "multiple_choice"),
                        content=question_data,
                        media_url=question_data.get("media_url"),
                        correct_answers=question_data.get("correct_answers"),
                        points=question_data.get("points", 10),
                        time_limit=question_data.get("time_limit", 30)
                    )
                    
                    question = await QuestionCRUD.create_question(db, question_create)
                    created_questions.append(question)
                
                logger.info("Game created from pack", 
                           game_id=str(game.id),
                           question_count=len(created_questions),
                           game_type=game_type)
                
                return {
                    "success": True,
                    "game_id": str(game.id),
                    "question_count": len(created_questions),
                    "validation_warnings": validation_result.get("warnings", [])
                }
        
        except Exception as e:
            logger.error("Error creating game from pack", 
                        error=str(e))
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_loaded_modules(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all loaded modules"""
        modules_info = {}
        for game_type, module in self.module_loader.get_all_modules().items():
            modules_info[game_type] = {
                "name": module.name,
                "version": module.version,
                "description": module.description,
                "supported_question_types": module.get_supported_question_types(),
                "config_schema": module.get_config_schema()
            }
        return modules_info