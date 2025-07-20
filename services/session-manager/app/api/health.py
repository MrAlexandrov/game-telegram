"""
Session Manager API - Health Check Endpoints
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import structlog

from ..models.database import get_db
from ..services.redis_service import redis_service
from ..schemas import HealthResponse

logger = structlog.get_logger()
router = APIRouter()


@router.get("/", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Check database connection
        await db.execute("SELECT 1")
        database_status = "healthy"
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        database_status = "unhealthy"
    
    # Check Redis connection
    redis_status = "healthy" if await redis_service.health_check() else "unhealthy"
    
    # Get statistics
    active_sessions = await redis_service.get_active_sessions_count()
    connected_players = await redis_service.get_connected_players_count()
    
    overall_status = "healthy" if database_status == "healthy" and redis_status == "healthy" else "unhealthy"
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow(),
        version="1.0.0",
        database=database_status,
        redis=redis_status,
        active_sessions=active_sessions,
        connected_players=connected_players
    )


@router.get("/ready")
async def readiness_check():
    """Kubernetes readiness probe"""
    return {"status": "ready"}


@router.get("/live")
async def liveness_check():
    """Kubernetes liveness probe"""
    return {"status": "alive"}