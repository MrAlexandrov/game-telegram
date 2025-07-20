"""
User Manager Service - Health Check Routes
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from ..schemas import HealthResponse
from ..services.database import get_db, check_database_health

router = APIRouter()


@router.get("/", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check endpoint"""
    db_status = await check_database_health()
    
    return HealthResponse(
        status="healthy" if db_status else "unhealthy",
        timestamp=datetime.utcnow(),
        version="1.0.0",
        database="connected" if db_status else "disconnected"
    )


@router.get("/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """Readiness check endpoint"""
    db_status = await check_database_health()
    
    if not db_status:
        return {"status": "not ready", "reason": "database not available"}
    
    return {"status": "ready"}


@router.get("/live")
async def liveness_check():
    """Liveness check endpoint"""
    return {"status": "alive"}