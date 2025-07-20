"""
Metrics API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from ..schemas import MetricsRequest, MetricsResponse
from ..services.metrics_service import MetricsService
from ..main import get_db, get_redis

logger = structlog.get_logger()
router = APIRouter()


@router.get("/", response_model=MetricsResponse)
async def get_metrics(
    request: MetricsRequest = Depends(),
    db: AsyncSession = Depends(get_db),
    redis_client = Depends(get_redis)
):
    """Get system metrics"""
    try:
        metrics_service = MetricsService(db, redis_client)
        result = await metrics_service.get_metrics(request)
        
        return result
        
    except Exception as e:
        logger.error("Failed to get metrics", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
