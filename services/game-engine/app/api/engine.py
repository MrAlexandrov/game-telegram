"""
Game Engine Service - Engine Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any

from ..schemas import (
    GameEngineRequest, AnswerValidationRequest, ResultsCalculationRequest,
    GameModuleInfo
)
from ..services.game_processor import GameProcessor

router = APIRouter()


def get_game_processor() -> GameProcessor:
    """Get game processor from app state"""
    from ..main import app
    if not hasattr(app.state, 'game_processor'):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Game processor not available"
        )
    return app.state.game_processor


@router.post("/process-question")
async def process_question(
    request: GameEngineRequest,
    game_processor: GameProcessor = Depends(get_game_processor)
):
    """Process a game question"""
    try:
        result = await game_processor.process_question(
            session_id=request.session_id,
            question_id=request.question_id,
            game_type=request.game_type
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to process question")
            )
        
        return result
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing question: {str(e)}"
        )


@router.post("/validate-answer")
async def validate_answer(
    request: AnswerValidationRequest,
    game_processor: GameProcessor = Depends(get_game_processor)
):
    """Validate a player's answer"""
    try:
        result = await game_processor.validate_answer(
            answer_id=request.answer_id,
            is_correct=request.is_correct,
            points=request.points
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to validate answer")
            )
        
        return result
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating answer: {str(e)}"
        )


@router.post("/calculate-results")
async def calculate_results(
    request: ResultsCalculationRequest,
    game_processor: GameProcessor = Depends(get_game_processor)
):
    """Calculate game results"""
    try:
        result = await game_processor.calculate_results(
            session_id=request.session_id
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to calculate results")
            )
        
        return result
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating results: {str(e)}"
        )


@router.get("/modules")
async def get_loaded_modules(
    game_processor: GameProcessor = Depends(get_game_processor)
) -> Dict[str, GameModuleInfo]:
    """Get information about all loaded game modules"""
    try:
        modules_info = game_processor.get_loaded_modules()
        
        # Convert to GameModuleInfo schema
        result = {}
        for game_type, info in modules_info.items():
            result[game_type] = GameModuleInfo(
                name=info["name"],
                version=info["version"],
                description=info["description"],
                supported_question_types=info["supported_question_types"],
                config_schema=info["config_schema"]
            )
        
        return result
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting modules: {str(e)}"
        )


@router.get("/modules/{game_type}")
async def get_module_info(
    game_type: str,
    game_processor: GameProcessor = Depends(get_game_processor)
) -> GameModuleInfo:
    """Get information about a specific game module"""
    try:
        modules_info = game_processor.get_loaded_modules()
        
        if game_type not in modules_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Game module not found: {game_type}"
            )
        
        info = modules_info[game_type]
        return GameModuleInfo(
            name=info["name"],
            version=info["version"],
            description=info["description"],
            supported_question_types=info["supported_question_types"],
            config_schema=info["config_schema"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting module info: {str(e)}"
        )