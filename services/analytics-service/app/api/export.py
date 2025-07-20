"""
Export API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from ..schemas import ExportRequest, ExportResponse
from ..services.export_service import ExportService
from ..main import get_db

logger = structlog.get_logger()
router = APIRouter()


@router.post("/", response_model=ExportResponse)
async def export_data(
    request: ExportRequest,
    db: AsyncSession = Depends(get_db)
):
    """Export data in various formats"""
    try:
        export_service = ExportService(db)
        result = await export_service.export_data(request)
        
        return result
        
    except Exception as e:
        logger.error("Failed to export data", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
