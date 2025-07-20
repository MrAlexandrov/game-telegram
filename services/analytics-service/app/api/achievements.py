"""
Achievements API endpoints
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from ..models import Achievement, PlayerAchievement, PlayerStats
from ..schemas import CreateAchievementRequest, UpdateAchievementRequest, AchievementProgressUpdate
from ..services.achievement_service import AchievementService
from ..main import get_db, get_redis

logger = structlog.get_logger()
router = APIRouter()


@router.get("/")
async def get_achievements(
    include_hidden: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """Get all achievements"""
    try:
        stmt = select(Achievement).where(Achievement.is_active == True)
        if not include_hidden:
            stmt = stmt.where(Achievement.is_hidden == False)
        
        result = await db.execute(stmt)
        achievements = result.scalars().all()
        
        return {"achievements": achievements}
        
    except Exception as e:
        logger.error("Failed to get achievements", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/player/{player_id}")
async def get_player_achievements(
    player_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get player's achievements"""
    try:
        stmt = (
            select(PlayerAchievement, Achievement)
            .join(Achievement)
            .where(PlayerAchievement.player_id == player_id)
            .order_by(PlayerAchievement.earned_at.desc())
        )
        
        result = await db.execute(stmt)
        player_achievements = result.all()
        
        return {
            "player_id": player_id,
            "achievements": [
                {
                    "achievement": pa.Achievement,
                    "earned_at": pa.PlayerAchievement.earned_at,
                    "progress": pa.PlayerAchievement.progress
                }
                for pa in player_achievements
            ]
        }
        
    except Exception as e:
        logger.error("Failed to get player achievements", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=dict)
async def create_achievement(
    request: CreateAchievementRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create new achievement"""
    try:
        achievement = Achievement(
            id=request.id,
            name=request.name,
            description=request.description,
            type=request.type,
            icon=request.icon,
            criteria=request.criteria,
            points=request.points,
            is_hidden=request.is_hidden
        )
        
        db.add(achievement)
        await db.commit()
        await db.refresh(achievement)
        
        logger.info("Achievement created", achievement_id=request.id)
        
        return {"message": "Achievement created successfully", "achievement": achievement}
        
    except Exception as e:
        logger.error("Failed to create achievement", error=str(e))
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
