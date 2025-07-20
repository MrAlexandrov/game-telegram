"""
Results API endpoints
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import structlog

from ..models import GameResult, PlayerGameResult, QuestionResult
from ..schemas import (
    RecordResultRequest, RecordResultResponse,
    GetPlayerStatsRequest, GetPlayerStatsResponse,
    BatchRecordRequest, BatchRecordResponse
)
from ..services.results_service import ResultsService
from ..main import get_db, get_redis

logger = structlog.get_logger()
router = APIRouter()


@router.post("/record", response_model=RecordResultResponse)
async def record_result(
    request: RecordResultRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    redis_client = Depends(get_redis)
):
    """Record game result"""
    try:
        results_service = ResultsService(db, redis_client)
        
        # Record the result
        result_id = await results_service.record_game_result(request.game_result)
        
        # Schedule background tasks for analytics generation
        background_tasks.add_task(
            results_service.generate_session_analytics,
            request.session_id
        )
        background_tasks.add_task(
            results_service.update_player_stats,
            request.game_result.player_results
        )
        background_tasks.add_task(
            results_service.check_achievements,
            request.game_result.player_results
        )
        
        logger.info(
            "Game result recorded",
            session_id=request.session_id,
            result_id=result_id,
            players=len(request.game_result.player_results)
        )
        
        return RecordResultResponse(
            success=True,
            message="Result recorded successfully",
            result_id=result_id,
            analytics_generated=True
        )
        
    except Exception as e:
        logger.error("Failed to record result", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}")
async def get_session_results(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get results for a specific session"""
    try:
        # Query game result
        stmt = select(GameResult).where(GameResult.session_id == session_id)
        result = await db.execute(stmt)
        game_result = result.scalar_one_or_none()
        
        if not game_result:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Query player results
        stmt = select(PlayerGameResult).where(
            PlayerGameResult.game_result_id == game_result.id
        ).order_by(PlayerGameResult.position.asc())
        result = await db.execute(stmt)
        player_results = result.scalars().all()
        
        # Query question results for each player
        for player_result in player_results:
            stmt = select(QuestionResult).where(
                QuestionResult.player_result_id == player_result.id
            )
            result = await db.execute(stmt)
            player_result.question_results = result.scalars().all()
        
        return {
            "session_id": session_id,
            "game_result": game_result,
            "player_results": player_results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get session results", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/player/{player_id}")
async def get_player_results(
    player_id: str,
    limit: int = 10,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """Get results for a specific player"""
    try:
        # Query player's game results
        stmt = (
            select(PlayerGameResult)
            .join(GameResult)
            .where(PlayerGameResult.player_id == player_id)
            .order_by(GameResult.start_time.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await db.execute(stmt)
        player_results = result.scalars().all()
        
        return {
            "player_id": player_id,
            "results": player_results,
            "total": len(player_results)
        }
        
    except Exception as e:
        logger.error("Failed to get player results", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch", response_model=BatchRecordResponse)
async def batch_record_results(
    request: BatchRecordRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    redis_client = Depends(get_redis)
):
    """Record multiple game results in batch"""
    try:
        results_service = ResultsService(db, redis_client)
        
        processed_count = 0
        failed_count = 0
        errors = []
        result_ids = []
        
        for game_result in request.results:
            try:
                result_id = await results_service.record_game_result(game_result)
                result_ids.append(result_id)
                processed_count += 1
                
                # Schedule background tasks
                background_tasks.add_task(
                    results_service.generate_session_analytics,
                    game_result.session_id
                )
                background_tasks.add_task(
                    results_service.update_player_stats,
                    game_result.player_results
                )
                
            except Exception as e:
                failed_count += 1
                errors.append(f"Session {game_result.session_id}: {str(e)}")
                logger.error(
                    "Failed to record batch result",
                    session_id=game_result.session_id,
                    error=str(e)
                )
        
        logger.info(
            "Batch record completed",
            processed=processed_count,
            failed=failed_count
        )
        
        return BatchRecordResponse(
            success=failed_count == 0,
            processed_count=processed_count,
            failed_count=failed_count,
            errors=errors,
            result_ids=result_ids
        )
        
    except Exception as e:
        logger.error("Failed to process batch", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/session/{session_id}")
async def delete_session_results(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete results for a specific session"""
    try:
        # Find game result
        stmt = select(GameResult).where(GameResult.session_id == session_id)
        result = await db.execute(stmt)
        game_result = result.scalar_one_or_none()
        
        if not game_result:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Delete will cascade to player and question results
        await db.delete(game_result)
        await db.commit()
        
        logger.info("Session results deleted", session_id=session_id)
        
        return {"message": "Session results deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete session results", error=str(e))
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recent")
async def get_recent_results(
    limit: int = 20,
    game_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get recent game results"""
    try:
        stmt = select(GameResult).order_by(GameResult.start_time.desc()).limit(limit)
        
        if game_type:
            stmt = stmt.where(GameResult.game_type == game_type)
        
        result = await db.execute(stmt)
        game_results = result.scalars().all()
        
        return {
            "results": game_results,
            "total": len(game_results)
        }
        
    except Exception as e:
        logger.error("Failed to get recent results", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
