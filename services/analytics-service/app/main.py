"""
Analytics Service - FastAPI Application
"""
import os
import sys
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
import uvicorn
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker
import redis.asyncio as redis

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'shared'))

from .models import Base
from schemas import HealthCheckResponse
from config import get_settings

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Global variables
engine = None
async_session = None
redis_client = None
app_start_time = datetime.utcnow()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global engine, async_session, redis_client
    
    settings = get_settings()
    
    try:
        # Initialize database
        engine = create_async_engine(
            settings.database_url,
            echo=settings.debug,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
        
        async_session = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        
        # Create tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        # Initialize Redis
        if settings.redis_url:
            redis_client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await redis_client.ping()
            logger.info("Redis connection established")
        
        logger.info("Analytics service started successfully")
        
        yield
        
    except Exception as e:
        logger.error("Failed to start analytics service", error=str(e))
        raise
    finally:
        # Cleanup
        if redis_client:
            await redis_client.close()
        if engine:
            await engine.dispose()
        logger.info("Analytics service shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Game Analytics Service",
    description="Comprehensive analytics and statistics service for game results",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency to get database session
async def get_db() -> AsyncSession:
    """Get database session"""
    if not async_session:
        raise HTTPException(status_code=500, detail="Database not initialized")
    
    async with async_session() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error("Database session error", error=str(e))
            raise
        finally:
            await session.close()


# Dependency to get Redis client
async def get_redis():
    """Get Redis client"""
    if not redis_client:
        raise HTTPException(status_code=500, detail="Redis not initialized")
    return redis_client


# Health check endpoint
@app.get("/health", response_model=HealthCheckResponse)
async def health_check(
    db: AsyncSession = Depends(get_db),
    redis_conn = Depends(get_redis)
):
    """Health check endpoint"""
    try:
        # Check database
        await db.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        db_status = "unhealthy"
    
    # Check Redis
    redis_status = "healthy"
    try:
        if redis_conn:
            await redis_conn.ping()
    except Exception as e:
        logger.error("Redis health check failed", error=str(e))
        redis_status = "unhealthy"
    
    # Calculate uptime
    uptime = (datetime.utcnow() - app_start_time).total_seconds()
    
    overall_status = "healthy" if db_status == "healthy" else "unhealthy"
    
    return HealthCheckResponse(
        status=overall_status,
        timestamp=datetime.utcnow(),
        version="1.0.0",
        database_status=db_status,
        redis_status=redis_status,
        uptime=uptime
    )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Game Analytics Service",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.utcnow(),
        "docs": "/docs"
    }


# Include API routers
from api import results, analytics, leaderboard, achievements, export, metrics

app.include_router(results.router, prefix="/api/v1/results", tags=["Results"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
app.include_router(leaderboard.router, prefix="/api/v1/leaderboard", tags=["Leaderboard"])
app.include_router(achievements.router, prefix="/api/v1/achievements", tags=["Achievements"])
app.include_router(export.router, prefix="/api/v1/export", tags=["Export"])
app.include_router(metrics.router, prefix="/api/v1/metrics", tags=["Metrics"])


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(
        "Unhandled exception",
        error=str(exc),
        path=request.url.path,
        method=request.method
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# Startup event for background tasks
@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    logger.info("Analytics service startup complete")


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )
