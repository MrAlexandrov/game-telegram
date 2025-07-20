"""
Game Engine Service - Games Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import uuid
import json

from ..schemas import (
    GameCreate, GameUpdate, GameResponse, QuestionCreate, QuestionUpdate, 
    QuestionResponse, GamePackCreate, GamePackResponse, GamePackValidation,
    MediaFileCreate, MediaFileResponse
)
from ..models.database import get_db
from ..crud import GameCRUD, QuestionCRUD, GamePackCRUD, MediaFileCRUD
from ..services.game_processor import GameProcessor

router = APIRouter()


@router.get("/", response_model=List[GameResponse])
async def get_games(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    game_type: Optional[str] = Query(None),
    created_by: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get list of games"""
    games = await GameCRUD.get_games(
        db, skip=skip, limit=limit, game_type=game_type, created_by=created_by
    )
    return games


@router.post("/", response_model=GameResponse, status_code=status.HTTP_201_CREATED)
async def create_game(
    game_data: GameCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new game"""
    try:
        game = await GameCRUD.create_game(db, game_data)
        return game
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{game_id}", response_model=GameResponse)
async def get_game(
    game_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get game by ID"""
    game = await GameCRUD.get_game_by_id(db, game_id)
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game not found"
        )
    return game


@router.put("/{game_id}", response_model=GameResponse)
async def update_game(
    game_id: uuid.UUID,
    game_data: GameUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update game"""
    game = await GameCRUD.update_game(db, game_id, game_data)
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game not found"
        )
    return game


@router.delete("/{game_id}")
async def delete_game(
    game_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete game"""
    success = await GameCRUD.delete_game(db, game_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game not found"
        )
    return {"message": "Game deleted successfully"}


@router.get("/{game_id}/questions", response_model=List[QuestionResponse])
async def get_game_questions(
    game_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get questions for a game"""
    # First check if game exists
    game = await GameCRUD.get_game_by_id(db, game_id)
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game not found"
        )
    
    questions = await QuestionCRUD.get_questions_by_game(db, game_id)
    return questions


@router.post("/{game_id}/questions", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
async def create_question(
    game_id: uuid.UUID,
    question_data: QuestionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new question for a game"""
    # Check if game exists
    game = await GameCRUD.get_game_by_id(db, game_id)
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game not found"
        )
    
    # Set the game_id
    question_data.game_id = game_id
    
    try:
        question = await QuestionCRUD.create_question(db, question_data)
        return question
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/questions/{question_id}", response_model=QuestionResponse)
async def update_question(
    question_id: uuid.UUID,
    question_data: QuestionUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update question"""
    question = await QuestionCRUD.update_question(db, question_id, question_data)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    return question


@router.delete("/questions/{question_id}")
async def delete_question(
    question_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete question"""
    success = await QuestionCRUD.delete_question(db, question_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    return {"message": "Question deleted successfully"}


@router.post("/validate-pack", response_model=GamePackValidation)
async def validate_game_pack(
    file: UploadFile = File(...),
    game_processor: GameProcessor = Depends(lambda: None)  # This would be injected from app state
):
    """Validate a game pack file"""
    try:
        # Read and parse the JSON file
        content = await file.read()
        pack_data = json.loads(content)
        
        # Extract game type
        game_type = pack_data.get("metadata", {}).get("type", "quiz")
        
        # Get game processor from app state (this is a simplified approach)
        # In a real implementation, you'd inject this properly
        from ..main import app
        if hasattr(app.state, 'game_processor'):
            validation_result = await app.state.game_processor.validate_game_pack(game_type, pack_data)
        else:
            validation_result = {
                "is_valid": False,
                "errors": ["Game processor not available"],
                "warnings": []
            }
        
        return GamePackValidation(**validation_result)
    
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON file"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation error: {str(e)}"
        )


@router.post("/from-pack", response_model=GameResponse, status_code=status.HTTP_201_CREATED)
async def create_game_from_pack(
    file: UploadFile = File(...),
    created_by: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """Create a game from a game pack file"""
    try:
        # Read and parse the JSON file
        content = await file.read()
        pack_data = json.loads(content)
        
        # Get game processor from app state
        from ..main import app
        if not hasattr(app.state, 'game_processor'):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Game processor not available"
            )
        
        # Create game from pack
        result = await app.state.game_processor.create_game_from_pack(pack_data, created_by)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to create game from pack")
            )
        
        # Get the created game
        game_id = uuid.UUID(result["game_id"])
        game = await GameCRUD.get_game_by_id(db, game_id)
        
        return game
    
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON file"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating game: {str(e)}"
        )