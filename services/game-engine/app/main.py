"""
Game Engine Service - Main Application
Handles game logic, question processing, and score calculation
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import structlog
from prometheus_client import make_asgi_app

from .config import settings
from .services.game_processor import GameProcessor
from .services.module_loader import ModuleLoader
from .models.database import engine
from .models import Base

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting Game Engine Service")
    
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Initialize game modules
    module_loader = ModuleLoader()
    await module_loader.load_modules()
    
    # Store module loader in app state
    app.state.module_loader = module_loader
    app.state.game_processor = GameProcessor(module_loader)
    
    yield
    
    logger.info("Shutting down Game Engine Service")


# Create FastAPI application
app = FastAPI(
    title="Game Engine Service",
    description="Processes game logic, questions, and scoring",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
from .api import games, health, import_export
from .api import engine as engine_api
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(games.router, prefix="/games", tags=["games"])
app.include_router(engine_api.router, prefix="/engine", tags=["engine"])
app.include_router(import_export.router, prefix="/import", tags=["import"])

# Add Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Game Engine",
        "version": "1.0.0",
        "status": "running",
        "loaded_modules": list(app.state.module_loader.modules.keys()) if hasattr(app.state, 'module_loader') else []
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.post("/engine/process-question")
async def process_question(request: dict):
    """Process a game question"""
    try:
        result = await app.state.game_processor.process_question(
            session_id=request["session_id"],
            question_id=request["question_id"],
            game_type=request["game_type"]
        )
        return result
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/engine/validate-answer")
async def validate_answer(request: dict):
    """Validate a player's answer"""
    try:
        result = await app.state.game_processor.validate_answer(
            answer_id=request["answer_id"],
            is_correct=request["is_correct"],
            points=request.get("points", 0)
        )
        return result
    except Exception as e:
        logger.error(f"Error validating answer: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/engine/calculate-results")
async def calculate_results(request: dict):
    """Calculate game results"""
    try:
        results = await app.state.game_processor.calculate_results(
            session_id=request["session_id"]
        )
        return {"results": results}
    except Exception as e:
        logger.error(f"Error calculating results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )

