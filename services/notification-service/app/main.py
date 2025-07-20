"""
Notification Service - Main Application
Handles notifications for game events, player connections, and system alerts
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import structlog
from prometheus_client import make_asgi_app
import asyncio
from typing import Dict, Any, List, Optional
import json
import uuid
from datetime import datetime

from .config import settings
from .services.notification_manager import notification_manager
from .services.redis_subscriber import redis_subscriber
from .schemas import (
    NotificationCreate, NotificationResponse, NotificationBatch,
    ConnectionNotification, GameEventNotification, SystemNotification
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting Notification Service")
    
    # Initialize notification manager
    await notification_manager.initialize()
    
    # Start Redis subscriber for real-time events
    await redis_subscriber.start()
    
    # Start background tasks
    asyncio.create_task(process_notification_queue())
    asyncio.create_task(cleanup_old_notifications())
    
    yield
    
    # Cleanup
    await redis_subscriber.stop()
    await notification_manager.cleanup()
    logger.info("Shutting down Notification Service")


# Create FastAPI application
app = FastAPI(
    title="Notification Service",
    description="Handles notifications for game events and player connections",
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

# Add Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Notification Service",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "redis_connected": await redis_subscriber.is_connected(),
        "notification_manager_ready": notification_manager.is_ready()
    }


@app.post("/notifications", response_model=NotificationResponse)
async def send_notification(
    notification: NotificationCreate,
    background_tasks: BackgroundTasks
):
    """Send a single notification"""
    try:
        # Add to processing queue
        background_tasks.add_task(
            notification_manager.send_notification,
            notification.dict()
        )
        
        return NotificationResponse(
            id=str(uuid.uuid4()),
            status="queued",
            message="Notification queued for processing"
        )
        
    except Exception as e:
        logger.error("Error queuing notification", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to queue notification")


@app.post("/notifications/batch", response_model=List[NotificationResponse])
async def send_notification_batch(
    batch: NotificationBatch,
    background_tasks: BackgroundTasks
):
    """Send multiple notifications"""
    try:
        responses = []
        
        for notification in batch.notifications:
            notification_id = str(uuid.uuid4())
            
            background_tasks.add_task(
                notification_manager.send_notification,
                {**notification.dict(), "id": notification_id}
            )
            
            responses.append(NotificationResponse(
                id=notification_id,
                status="queued",
                message="Notification queued for processing"
            ))
        
        return responses
        
    except Exception as e:
        logger.error("Error queuing notification batch", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to queue notification batch")


@app.post("/notifications/connection")
async def send_connection_notification(
    notification: ConnectionNotification,
    background_tasks: BackgroundTasks
):
    """Send connection-specific notification"""
    try:
        # Process connection notification
        background_tasks.add_task(
            process_connection_notification,
            notification.dict()
        )
        
        return {"status": "queued", "message": "Connection notification queued"}
        
    except Exception as e:
        logger.error("Error processing connection notification", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to process connection notification")


@app.post("/notifications/game-event")
async def send_game_event_notification(
    notification: GameEventNotification,
    background_tasks: BackgroundTasks
):
    """Send game event notification"""
    try:
        background_tasks.add_task(
            process_game_event_notification,
            notification.dict()
        )
        
        return {"status": "queued", "message": "Game event notification queued"}
        
    except Exception as e:
        logger.error("Error processing game event notification", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to process game event notification")


@app.post("/notifications/system")
async def send_system_notification(
    notification: SystemNotification,
    background_tasks: BackgroundTasks
):
    """Send system notification"""
    try:
        background_tasks.add_task(
            process_system_notification,
            notification.dict()
        )
        
        return {"status": "queued", "message": "System notification queued"}
        
    except Exception as e:
        logger.error("Error processing system notification", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to process system notification")


async def process_connection_notification(notification_data: Dict[str, Any]):
    """Process connection-specific notifications"""
    try:
        event_type = notification_data.get("event_type")
        session_id = notification_data.get("session_id")
        user_data = notification_data.get("user_data", {})
        
        if event_type == "player_joined":
            # Notify admin about new player
            await notification_manager.notify_session_admin(
                session_id=session_id,
                message=f"🎮 Новый игрок присоединился: {user_data.get('display_name', 'Неизвестный')}",
                notification_type="player_joined",
                data=notification_data
            )
            
            # Notify other players
            await notification_manager.notify_session_players(
                session_id=session_id,
                message=f"👋 {user_data.get('display_name', 'Игрок')} присоединился к игре!",
                notification_type="player_joined",
                exclude_user=user_data.get("user_id"),
                data=notification_data
            )
            
            # Send welcome message to new player
            await notification_manager.notify_user(
                user_id=user_data.get("user_id"),
                message="✅ Вы успешно присоединились к игре! Ожидайте начала.",
                notification_type="connection_success",
                data=notification_data
            )
        
        elif event_type == "player_left":
            # Notify admin about player leaving
            await notification_manager.notify_session_admin(
                session_id=session_id,
                message=f"🚪 Игрок покинул игру: {user_data.get('display_name', 'Неизвестный')}",
                notification_type="player_left",
                data=notification_data
            )
            
            # Notify other players
            await notification_manager.notify_session_players(
                session_id=session_id,
                message=f"👋 {user_data.get('display_name', 'Игрок')} покинул игру",
                notification_type="player_left",
                exclude_user=user_data.get("user_id"),
                data=notification_data
            )
        
        elif event_type == "connection_failed":
            # Notify user about connection failure
            error_message = notification_data.get("error_message", "Неизвестная ошибка")
            await notification_manager.notify_user(
                user_id=user_data.get("user_id"),
                message=f"❌ Не удалось подключиться к игре: {error_message}",
                notification_type="connection_failed",
                data=notification_data
            )
        
        logger.info("Connection notification processed", event_type=event_type, session_id=session_id)
        
    except Exception as e:
        logger.error("Error processing connection notification", error=str(e), data=notification_data)


async def process_game_event_notification(notification_data: Dict[str, Any]):
    """Process game event notifications"""
    try:
        event_type = notification_data.get("event_type")
        session_id = notification_data.get("session_id")
        
        if event_type == "game_started":
            # Notify all players that game has started
            await notification_manager.notify_session_players(
                session_id=session_id,
                message="🎮 Игра началась! Приготовьтесь к первому вопросу.",
                notification_type="game_started",
                data=notification_data
            )
        
        elif event_type == "question_started":
            question_data = notification_data.get("question_data", {})
            question_text = question_data.get("text", "Новый вопрос")
            time_limit = question_data.get("time_limit", 30)
            
            await notification_manager.notify_session_players(
                session_id=session_id,
                message=f"❓ {question_text}\n\n⏰ Время на ответ: {time_limit} секунд",
                notification_type="question_started",
                data=notification_data
            )
        
        elif event_type == "question_ended":
            results = notification_data.get("results", {})
            correct_answer = results.get("correct_answer", "")
            
            await notification_manager.notify_session_players(
                session_id=session_id,
                message=f"✅ Правильный ответ: {correct_answer}",
                notification_type="question_ended",
                data=notification_data
            )
        
        elif event_type == "game_ended":
            winner_data = notification_data.get("winner", {})
            winner_name = winner_data.get("display_name", "Неизвестный")
            
            await notification_manager.notify_session_players(
                session_id=session_id,
                message=f"🏆 Игра завершена! Победитель: {winner_name}",
                notification_type="game_ended",
                data=notification_data
            )
            
            # Notify admin
            await notification_manager.notify_session_admin(
                session_id=session_id,
                message=f"🎯 Игра завершена. Победитель: {winner_name}",
                notification_type="game_ended",
                data=notification_data
            )
        
        logger.info("Game event notification processed", event_type=event_type, session_id=session_id)
        
    except Exception as e:
        logger.error("Error processing game event notification", error=str(e), data=notification_data)


async def process_system_notification(notification_data: Dict[str, Any]):
    """Process system notifications"""
    try:
        notification_type = notification_data.get("notification_type")
        message = notification_data.get("message")
        severity = notification_data.get("severity", "info")
        
        if notification_type == "system_maintenance":
            # Notify all active users about maintenance
            await notification_manager.broadcast_to_all_users(
                message=f"🔧 {message}",
                notification_type="system_maintenance",
                data=notification_data
            )
        
        elif notification_type == "service_error":
            # Notify administrators about service errors
            await notification_manager.notify_administrators(
                message=f"🚨 Ошибка сервиса: {message}",
                notification_type="service_error",
                data=notification_data
            )
        
        elif notification_type == "security_alert":
            # Notify administrators about security issues
            await notification_manager.notify_administrators(
                message=f"🔒 Предупреждение безопасности: {message}",
                notification_type="security_alert",
                data=notification_data,
                priority="high"
            )
        
        logger.info("System notification processed", notification_type=notification_type, severity=severity)
        
    except Exception as e:
        logger.error("Error processing system notification", error=str(e), data=notification_data)


async def process_notification_queue():
    """Background task to process notification queue"""
    while True:
        try:
            await notification_manager.process_queue()
            await asyncio.sleep(1)  # Process queue every second
        except Exception as e:
            logger.error("Error processing notification queue", error=str(e))
            await asyncio.sleep(5)  # Wait longer on error


async def cleanup_old_notifications():
    """Background task to cleanup old notifications"""
    while True:
        try:
            await notification_manager.cleanup_old_notifications()
            await asyncio.sleep(3600)  # Cleanup every hour
        except Exception as e:
            logger.error("Error cleaning up notifications", error=str(e))
            await asyncio.sleep(1800)  # Wait 30 minutes on error


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )