"""
Session Manager Service - Main Application
Handles game sessions, real-time updates, and player management
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import structlog
from prometheus_client import make_asgi_app

from .config import settings
from .services.redis_service import redis_service
from .models.database import engine
from .models import Base

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting Session Manager Service")
    
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Connect to Redis
    await redis_service.connect()
    
    # Store services in app state
    app.state.redis_service = redis_service
    
    yield
    
    # Cleanup
    await redis_service.disconnect()
    logger.info("Shutting down Session Manager Service")


# Create FastAPI application
app = FastAPI(
    title="Session Manager Service",
    description="Manages game sessions, real-time updates, and player interactions",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
from .api import sessions, websocket, health
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])

# Add Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Session Manager",
        "version": "1.0.0",
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )