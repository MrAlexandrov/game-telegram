"""
Redis Subscriber Service for Notification Service
Listens to Redis pub/sub channels for real-time events
"""

import asyncio
import structlog
import json
import redis.asyncio as redis
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..config import settings
from .notification_manager import notification_manager

logger = structlog.get_logger()


class RedisSubscriber:
    """Redis subscriber for real-time event notifications"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None
        self.is_running = False
        self.subscribed_channels = [
            "session:*",  # Session events
            "game:*",     # Game events
            "system:*",   # System events
            "connection:*"  # Connection events
        ]
    
    async def start(self):
        """Start Redis subscriber"""
        try:
            # Connect to Redis
            self.redis_client = redis.from_url(
                settings.redis_url,
                db=settings.redis_db,
                password=settings.redis_password if settings.redis_password else None,
                decode_responses=True
            )
            
            # Test connection
            await self.redis_client.ping()
            
            # Create pubsub instance
            self.pubsub = self.redis_client.pubsub()
            
            # Subscribe to channels
            for channel in self.subscribed_channels:
                await self.pubsub.psubscribe(channel)
            
            self.is_running = True
            
            # Start listening task
            asyncio.create_task(self._listen_for_messages())
            
            logger.info("Redis subscriber started", channels=self.subscribed_channels)
            
        except Exception as e:
            logger.error("Failed to start Redis subscriber", error=str(e))
            raise
    
    async def stop(self):
        """Stop Redis subscriber"""
        try:
            self.is_running = False
            
            if self.pubsub:
                await self.pubsub.unsubscribe()
                await self.pubsub.close()
            
            if self.redis_client:
                await self.redis_client.close()
            
            logger.info("Redis subscriber stopped")
            
        except Exception as e:
            logger.error("Error stopping Redis subscriber", error=str(e))
    
    async def is_connected(self) -> bool:
        """Check if Redis connection is active"""
        try:
            if self.redis_client:
                await self.redis_client.ping()
                return True
        except Exception:
            pass
        return False
    
    async def _listen_for_messages(self):
        """Listen for Redis pub/sub messages"""
        logger.info("Started listening for Redis messages")
        
        while self.is_running:
            try:
                if not self.pubsub:
                    await asyncio.sleep(1)
                    continue
                
                # Get message with timeout
                message = await asyncio.wait_for(
                    self.pubsub.get_message(ignore_subscribe_messages=True),
                    timeout=1.0
                )
                
                if message and message["type"] == "pmessage":
                    await self._process_message(message)
                
            except asyncio.TimeoutError:
                continue  # No message received, continue listening
            except Exception as e:
                logger.error("Error listening for Redis messages", error=str(e))
                await asyncio.sleep(5)  # Wait before retrying
    
    async def _process_message(self, message: Dict[str, Any]):
        """Process received Redis message"""
        try:
            channel = message["channel"]
            data = message["data"]
            
            # Parse JSON data
            try:
                event_data = json.loads(data)
            except json.JSONDecodeError:
                logger.warning("Invalid JSON in Redis message", channel=channel, data=data)
                return
            
            # Route message based on channel pattern
            if channel.startswith("session:"):
                await self._handle_session_event(channel, event_data)
            elif channel.startswith("game:"):
                await self._handle_game_event(channel, event_data)
            elif channel.startswith("system:"):
                await self._handle_system_event(channel, event_data)
            elif channel.startswith("connection:"):
                await self._handle_connection_event(channel, event_data)
            else:
                logger.warning("Unknown channel pattern", channel=channel)
            
        except Exception as e:
            logger.error("Error processing Redis message", error=str(e), message=message)
    
    async def _handle_session_event(self, channel: str, event_data: Dict[str, Any]):
        """Handle session-related events"""
        try:
            event_type = event_data.get("type")
            session_id = channel.split(":", 1)[1]  # Extract session ID from channel
            
            if event_type == "player_joined":
                # Register user for session notifications
                user_id = event_data.get("data", {}).get("user_id")
                if user_id:
                    await notification_manager.register_user_session(user_id, session_id)
                
                # Send connection notification
                await notification_manager.send_notification({
                    "recipient_id": "admin",  # This would be the actual admin ID
                    "message": f"🎮 Новый игрок присоединился к игре",
                    "notification_type": "player_joined",
                    "priority": "normal",
                    "channels": ["telegram"],
                    "data": event_data
                })
            
            elif event_type == "player_left":
                # Unregister user from session notifications
                user_id = event_data.get("data", {}).get("user_id")
                if user_id:
                    await notification_manager.unregister_user_session(user_id, session_id)
                
                # Send notification
                await notification_manager.send_notification({
                    "recipient_id": "admin",
                    "message": f"🚪 Игрок покинул игру",
                    "notification_type": "player_left",
                    "priority": "normal",
                    "channels": ["telegram"],
                    "data": event_data
                })
            
            elif event_type == "session_started":
                # Notify all players that session started
                await notification_manager.notify_session_players(
                    session_id=session_id,
                    message="🎮 Игра началась! Приготовьтесь к первому вопросу.",
                    notification_type="game_started",
                    data=event_data
                )
            
            elif event_type == "session_ended":
                # Notify all players that session ended
                winner_name = event_data.get("data", {}).get("winner_name", "Неизвестный")
                await notification_manager.notify_session_players(
                    session_id=session_id,
                    message=f"🏆 Игра завершена! Победитель: {winner_name}",
                    notification_type="game_ended",
                    data=event_data
                )
            
            logger.info("Session event processed", event_type=event_type, session_id=session_id)
            
        except Exception as e:
            logger.error("Error handling session event", error=str(e), channel=channel, data=event_data)
    
    async def _handle_game_event(self, channel: str, event_data: Dict[str, Any]):
        """Handle game-related events"""
        try:
            event_type = event_data.get("type")
            game_id = channel.split(":", 1)[1]
            
            if event_type == "question_started":
                question_data = event_data.get("data", {})
                session_id = question_data.get("session_id")
                
                if session_id:
                    question_text = question_data.get("question", {}).get("text", "Новый вопрос")
                    time_limit = question_data.get("time_limit", 30)
                    
                    await notification_manager.notify_session_players(
                        session_id=session_id,
                        message=f"❓ {question_text}\n\n⏰ Время на ответ: {time_limit} секунд",
                        notification_type="question_started",
                        data=event_data
                    )
            
            elif event_type == "question_ended":
                results = event_data.get("data", {})
                session_id = results.get("session_id")
                
                if session_id:
                    correct_answer = results.get("correct_answer", "")
                    await notification_manager.notify_session_players(
                        session_id=session_id,
                        message=f"✅ Правильный ответ: {correct_answer}",
                        notification_type="question_ended",
                        data=event_data
                    )
            
            elif event_type == "answer_submitted":
                answer_data = event_data.get("data", {})
                session_id = answer_data.get("session_id")
                user_id = answer_data.get("user_id")
                
                if session_id and user_id:
                    # Notify other players that someone answered
                    await notification_manager.notify_session_players(
                        session_id=session_id,
                        message="💭 Кто-то ответил на вопрос!",
                        notification_type="answer_submitted",
                        exclude_user=user_id,
                        data=event_data
                    )
            
            logger.info("Game event processed", event_type=event_type, game_id=game_id)
            
        except Exception as e:
            logger.error("Error handling game event", error=str(e), channel=channel, data=event_data)
    
    async def _handle_system_event(self, channel: str, event_data: Dict[str, Any]):
        """Handle system-related events"""
        try:
            event_type = event_data.get("type")
            
            if event_type == "service_error":
                error_data = event_data.get("data", {})
                service_name = error_data.get("service", "Unknown")
                error_message = error_data.get("error", "Unknown error")
                
                # Notify administrators
                await notification_manager.notify_administrators(
                    message=f"🚨 Ошибка сервиса {service_name}: {error_message}",
                    notification_type="service_error",
                    priority="high",
                    data=event_data
                )
            
            elif event_type == "maintenance_scheduled":
                maintenance_data = event_data.get("data", {})
                start_time = maintenance_data.get("start_time", "неизвестно")
                duration = maintenance_data.get("duration", "неизвестно")
                
                # Broadcast to all users
                await notification_manager.broadcast_to_all_users(
                    message=f"🔧 Запланировано техническое обслуживание\n"
                           f"Время: {start_time}\n"
                           f"Продолжительность: {duration}",
                    notification_type="system_maintenance",
                    priority="high",
                    data=event_data
                )
            
            elif event_type == "security_alert":
                alert_data = event_data.get("data", {})
                alert_message = alert_data.get("message", "Security alert")
                
                # Notify administrators immediately
                await notification_manager.notify_administrators(
                    message=f"🔒 Предупреждение безопасности: {alert_message}",
                    notification_type="security_alert",
                    priority="urgent",
                    data=event_data
                )
            
            logger.info("System event processed", event_type=event_type)
            
        except Exception as e:
            logger.error("Error handling system event", error=str(e), channel=channel, data=event_data)
    
    async def _handle_connection_event(self, channel: str, event_data: Dict[str, Any]):
        """Handle connection-related events"""
        try:
            event_type = event_data.get("type")
            connection_data = event_data.get("data", {})
            
            if event_type == "connection_attempt":
                user_id = connection_data.get("user_id")
                session_id = connection_data.get("session_id")
                success = connection_data.get("success", False)
                
                if success:
                    # Welcome message to user
                    if user_id:
                        await notification_manager.notify_user(
                            user_id=user_id,
                            message="✅ Вы успешно подключились к игре! Ожидайте начала.",
                            notification_type="connection_success",
                            data=event_data
                        )
                else:
                    # Connection failed
                    error_message = connection_data.get("error_message", "Неизвестная ошибка")
                    if user_id:
                        await notification_manager.notify_user(
                            user_id=user_id,
                            message=f"❌ Не удалось подключиться к игре: {error_message}",
                            notification_type="connection_failed",
                            data=event_data
                        )
            
            elif event_type == "rate_limit_exceeded":
                user_id = connection_data.get("user_id")
                if user_id:
                    await notification_manager.notify_user(
                        user_id=user_id,
                        message="⚠️ Слишком много попыток подключения. Попробуйте позже.",
                        notification_type="rate_limit",
                        priority="high",
                        data=event_data
                    )
            
            elif event_type == "suspicious_activity":
                # Notify administrators about suspicious activity
                activity_details = connection_data.get("details", "Unknown activity")
                await notification_manager.notify_administrators(
                    message=f"🚨 Подозрительная активность: {activity_details}",
                    notification_type="security_alert",
                    priority="urgent",
                    data=event_data
                )
            
            logger.info("Connection event processed", event_type=event_type)
            
        except Exception as e:
            logger.error("Error handling connection event", error=str(e), channel=channel, data=event_data)
    
    async def publish_event(self, channel: str, event_data: Dict[str, Any]):
        """Publish an event to Redis channel"""
        try:
            if self.redis_client:
                await self.redis_client.publish(channel, json.dumps(event_data))
                logger.info("Event published", channel=channel, event_type=event_data.get("type"))
        except Exception as e:
            logger.error("Error publishing event", error=str(e), channel=channel)


# Global Redis subscriber instance
redis_subscriber = RedisSubscriber()