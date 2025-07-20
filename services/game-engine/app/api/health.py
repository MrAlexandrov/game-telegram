"""
Game Engine Service - Health Check Routes
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from ..schemas import HealthResponse
from ..models.database import get_db
from ..services.game_processor import GameProcessor

router = APIRouter()


async def check_database_health(db: AsyncSession) -> bool:
    """Check database connection health"""
    try:
        from sqlalchemy import text
        await db.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def get_game_processor() -> GameProcessor:
    """Get game processor from app state"""
    from ..main import app
    if hasattr(app.state, 'game_processor'):
        return app.state.game_processor
    return None


@router.get("/", response_model=HealthResponse)
async def health_check(
    db: AsyncSession = Depends(get_db),
    game_processor: GameProcessor = Depends(get_game_processor)
):
    """Health check endpoint"""
    db_status = await check_database_health(db)
    
    # Get loaded modules
    loaded_modules = []
    if game_processor:
        try:
            modules_info = game_processor.get_loaded_modules()
            loaded_modules = list(modules_info.keys())
        except Exception:
            pass
    
    return HealthResponse(
        status="healthy" if db_status else "unhealthy",
        timestamp=datetime.utcnow(),
        version="1.0.0",
        database="connected" if db_status else "disconnected",
        loaded_modules=loaded_modules
    )


@router.get("/ready")
async def readiness_check(
    db: AsyncSession = Depends(get_db),
    game_processor: GameProcessor = Depends(get_game_processor)
):
    """Readiness check endpoint"""
    db_status = await check_database_health(db)
    
    if not db_status:
        return {"status": "not ready", "reason": "database not available"}
    
    if not game_processor:
        return {"status": "not ready", "reason": "game processor not available"}
    
    return {"status": "ready"}


@router.get("/live")
async def liveness_check():
    """Liveness check endpoint"""
    return {"status": "alive"}