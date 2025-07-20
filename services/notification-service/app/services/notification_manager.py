"""
Notification Manager Service
Handles notification processing, delivery, and management
"""

import asyncio
import structlog
from typing import Dict, Any, List, Optional, Set
import json
import uuid
from datetime import datetime, timedelta
import aiohttp
from collections import defaultdict, deque

from ..config import settings
from ..schemas import (
    NotificationCreate, NotificationStatus, NotificationChannel,
    NotificationPriority, NotificationQueue
)

logger = structlog.get_logger()


class NotificationManager:
    """Manages notification processing and delivery"""
    
    def __init__(self):
        self.notification_queue = asyncio.Queue()
        self.priority_queue = asyncio.PriorityQueue()
        self.delivery_handlers = {}
        self.active_notifications: Dict[str, Dict[str, Any]] = {}
        self.user_sessions: Dict[str, Set[str]] = defaultdict(set)  # user_id -> session_ids
        self.session_users: Dict[str, Set[str]] = defaultdict(set)  # session_id -> user_ids
        self.admin_users: Set[str] = set()
        self.delivery_stats = defaultdict(int)
        self.recent_notifications = deque(maxlen=1000)
        self.is_initialized = False
    
    async def initialize(self):
        """Initialize the notification manager"""
        try:
            # Register delivery handlers
            self.delivery_handlers = {
                NotificationChannel.TELEGRAM: self._deliver_telegram,
                NotificationChannel.WEBSOCKET: self._deliver_websocket,
                NotificationChannel.EMAIL: self._deliver_email,
                NotificationChannel.PUSH: self._deliver_push
            }
            
            # Load admin users from config or database
            await self._load_admin_users()
            
            # Start delivery workers
            for i in range(settings.NOTIFICATION_WORKERS):
                asyncio.create_task(self._delivery_worker(f"worker-{i}"))
            
            self.is_initialized = True
            logger.info("Notification manager initialized")
            
        except Exception as e:
            logger.error("Failed to initialize notification manager", error=str(e))
            raise
    
    def is_ready(self) -> bool:
        """Check if notification manager is ready"""
        return self.is_initialized
    
    async def cleanup(self):
        """Cleanup resources"""
        self.is_initialized = False
        logger.info("Notification manager cleaned up")
    
    async def send_notification(self, notification_data: Dict[str, Any]) -> str:
        """Queue a notification for delivery"""
        try:
            notification_id = notification_data.get("id", str(uuid.uuid4()))
            
            # Create notification object
            notification = NotificationCreate(**notification_data)
            
            # Calculate priority score
            priority_score = self._calculate_priority_score(notification.priority)
            
            # Add to priority queue
            queue_item = NotificationQueue(
                id=notification_id,
                notification=notification,
                priority=priority_score
            )
            
            await self.priority_queue.put((priority_score, queue_item))
            
            # Track active notification
            self.active_notifications[notification_id] = {
                "status": NotificationStatus.QUEUED,
                "created_at": datetime.utcnow(),
                "notification": notification_data
            }
            
            logger.info("Notification queued", notification_id=notification_id, priority=priority_score)
            return notification_id
            
        except Exception as e:
            logger.error("Error queuing notification", error=str(e), data=notification_data)
            raise
    
    async def process_queue(self):
        """Process notification queue"""
        try:
            if not self.priority_queue.empty():
                _, queue_item = await asyncio.wait_for(
                    self.priority_queue.get(), 
                    timeout=1.0
                )
                
                await self._process_notification(queue_item)
                
        except asyncio.TimeoutError:
            pass  # No items in queue
        except Exception as e:
            logger.error("Error processing notification queue", error=str(e))
    
    async def _process_notification(self, queue_item: NotificationQueue):
        """Process a single notification"""
        notification_id = queue_item.id
        notification = queue_item.notification
        
        try:
            # Update status
            if notification_id in self.active_notifications:
                self.active_notifications[notification_id]["status"] = NotificationStatus.SENDING
            
            # Deliver through all channels
            delivery_results = []
            for channel in notification.channels:
                if channel in self.delivery_handlers:
                    result = await self.delivery_handlers[channel](notification)
                    delivery_results.append({
                        "channel": channel,
                        "success": result.get("success", False),
                        "error": result.get("error")
                    })
                    
                    # Update stats
                    if result.get("success"):
                        self.delivery_stats[f"{channel}_success"] += 1
                    else:
                        self.delivery_stats[f"{channel}_failed"] += 1
            
            # Determine overall status
            success_count = sum(1 for r in delivery_results if r["success"])
            overall_success = success_count > 0
            
            # Update notification status
            final_status = NotificationStatus.SENT if overall_success else NotificationStatus.FAILED
            
            if notification_id in self.active_notifications:
                self.active_notifications[notification_id].update({
                    "status": final_status,
                    "sent_at": datetime.utcnow(),
                    "delivery_results": delivery_results
                })
            
            # Add to recent notifications
            self.recent_notifications.append({
                "id": notification_id,
                "recipient_id": notification.recipient_id,
                "message": notification.message[:100] + "..." if len(notification.message) > 100 else notification.message,
                "type": notification.notification_type,
                "status": final_status,
                "timestamp": datetime.utcnow(),
                "channels": [str(c) for c in notification.channels]
            })
            
            logger.info(
                "Notification processed",
                notification_id=notification_id,
                success=overall_success,
                channels=len(notification.channels)
            )
            
        except Exception as e:
            logger.error("Error processing notification", notification_id=notification_id, error=str(e))
            
            if notification_id in self.active_notifications:
                self.active_notifications[notification_id].update({
                    "status": NotificationStatus.FAILED,
                    "error": str(e)
                })
    
    async def _delivery_worker(self, worker_name: str):
        """Background worker for processing notifications"""
        logger.info(f"Delivery worker {worker_name} started")
        
        while self.is_initialized:
            try:
                await self.process_queue()
                await asyncio.sleep(0.1)  # Small delay to prevent busy waiting
            except Exception as e:
                logger.error(f"Error in delivery worker {worker_name}", error=str(e))
                await asyncio.sleep(1)
    
    def _calculate_priority_score(self, priority: NotificationPriority) -> int:
        """Calculate priority score for queue ordering"""
        priority_scores = {
            NotificationPriority.LOW: 1,
            NotificationPriority.NORMAL: 5,
            NotificationPriority.HIGH: 10,
            NotificationPriority.URGENT: 20
        }
        return priority_scores.get(priority, 5)
    
    async def _deliver_telegram(self, notification: NotificationCreate) -> Dict[str, Any]:
        """Deliver notification via Telegram"""
        try:
            # This would integrate with Telegram Bot API
            # For now, we'll simulate the delivery
            
            # In a real implementation, you would:
            # 1. Get user's Telegram chat ID from database
            # 2. Send message via Telegram Bot API
            # 3. Handle rate limits and errors
            
            await asyncio.sleep(0.1)  # Simulate API call
            
            logger.info(
                "Telegram notification delivered",
                recipient=notification.recipient_id,
                message_length=len(notification.message)
            )
            
            return {"success": True}
            
        except Exception as e:
            logger.error("Telegram delivery failed", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _deliver_websocket(self, notification: NotificationCreate) -> Dict[str, Any]:
        """Deliver notification via WebSocket"""
        try:
            # This would send to WebSocket connections
            # Integration with session manager's WebSocket service
            
            message = {
                "type": "notification",
                "data": {
                    "id": str(uuid.uuid4()),
                    "message": notification.message,
                    "notification_type": notification.notification_type,
                    "priority": notification.priority,
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": notification.data
                }
            }
            
            # Send to user's active WebSocket connections
            # This would be implemented with Redis pub/sub or direct WebSocket manager
            
            logger.info(
                "WebSocket notification delivered",
                recipient=notification.recipient_id
            )
            
            return {"success": True}
            
        except Exception as e:
            logger.error("WebSocket delivery failed", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _deliver_email(self, notification: NotificationCreate) -> Dict[str, Any]:
        """Deliver notification via Email"""
        try:
            # Email delivery implementation
            # Would integrate with email service (SendGrid, AWS SES, etc.)
            
            await asyncio.sleep(0.2)  # Simulate email sending
            
            logger.info(
                "Email notification delivered",
                recipient=notification.recipient_id
            )
            
            return {"success": True}
            
        except Exception as e:
            logger.error("Email delivery failed", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _deliver_push(self, notification: NotificationCreate) -> Dict[str, Any]:
        """Deliver notification via Push"""
        try:
            # Push notification delivery
            # Would integrate with FCM, APNs, etc.
            
            await asyncio.sleep(0.1)  # Simulate push sending
            
            logger.info(
                "Push notification delivered",
                recipient=notification.recipient_id
            )
            
            return {"success": True}
            
        except Exception as e:
            logger.error("Push delivery failed", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def notify_user(
        self,
        user_id: str,
        message: str,
        notification_type: str = "custom",
        priority: NotificationPriority = NotificationPriority.NORMAL,
        channels: Optional[List[NotificationChannel]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Send notification to a specific user"""
        if channels is None:
            channels = [NotificationChannel.TELEGRAM]
        
        notification_data = {
            "recipient_id": user_id,
            "message": message,
            "notification_type": notification_type,
            "priority": priority,
            "channels": channels,
            "data": data or {}
        }
        
        return await self.send_notification(notification_data)
    
    async def notify_session_players(
        self,
        session_id: str,
        message: str,
        notification_type: str = "game_event",
        exclude_user: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Send notification to all players in a session"""
        notification_ids = []
        
        # Get players in session
        players = self.session_users.get(session_id, set())
        
        for user_id in players:
            if exclude_user and user_id == exclude_user:
                continue
            
            notification_id = await self.notify_user(
                user_id=user_id,
                message=message,
                notification_type=notification_type,
                data=data
            )
            notification_ids.append(notification_id)
        
        return notification_ids
    
    async def notify_session_admin(
        self,
        session_id: str,
        message: str,
        notification_type: str = "admin_alert",
        data: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Send notification to session admin"""
        # In a real implementation, you would get the admin ID from the session
        # For now, we'll notify all admin users
        
        for admin_id in self.admin_users:
            return await self.notify_user(
                user_id=admin_id,
                message=message,
                notification_type=notification_type,
                priority=NotificationPriority.HIGH,
                data=data
            )
        
        return None
    
    async def notify_administrators(
        self,
        message: str,
        notification_type: str = "system_alert",
        priority: NotificationPriority = NotificationPriority.HIGH,
        data: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Send notification to all administrators"""
        notification_ids = []
        
        for admin_id in self.admin_users:
            notification_id = await self.notify_user(
                user_id=admin_id,
                message=message,
                notification_type=notification_type,
                priority=priority,
                data=data
            )
            notification_ids.append(notification_id)
        
        return notification_ids
    
    async def broadcast_to_all_users(
        self,
        message: str,
        notification_type: str = "broadcast",
        priority: NotificationPriority = NotificationPriority.NORMAL,
        data: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Broadcast notification to all active users"""
        notification_ids = []
        
        # Get all active users from sessions
        all_users = set()
        for users in self.session_users.values():
            all_users.update(users)
        
        for user_id in all_users:
            notification_id = await self.notify_user(
                user_id=user_id,
                message=message,
                notification_type=notification_type,
                priority=priority,
                data=data
            )
            notification_ids.append(notification_id)
        
        return notification_ids
    
    async def register_user_session(self, user_id: str, session_id: str):
        """Register user in a session for notifications"""
        self.user_sessions[user_id].add(session_id)
        self.session_users[session_id].add(user_id)
        
        logger.info("User registered for session notifications", user_id=user_id, session_id=session_id)
    
    async def unregister_user_session(self, user_id: str, session_id: str):
        """Unregister user from session notifications"""
        self.user_sessions[user_id].discard(session_id)
        self.session_users[session_id].discard(user_id)
        
        # Clean up empty sets
        if not self.user_sessions[user_id]:
            del self.user_sessions[user_id]
        if not self.session_users[session_id]:
            del self.session_users[session_id]
        
        logger.info("User unregistered from session notifications", user_id=user_id, session_id=session_id)
    
    async def _load_admin_users(self):
        """Load admin users from configuration or database"""
        # In a real implementation, this would load from database
        # For now, we'll use configuration
        admin_user_ids = getattr(settings, 'ADMIN_USER_IDS', [])
        self.admin_users.update(admin_user_ids)
        
        logger.info(f"Loaded {len(self.admin_users)} admin users")
    
    async def cleanup_old_notifications(self):
        """Clean up old notifications from memory"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            
            # Clean up active notifications
            expired_notifications = [
                nid for nid, data in self.active_notifications.items()
                if data.get("created_at", datetime.utcnow()) < cutoff_time
            ]
            
            for nid in expired_notifications:
                del self.active_notifications[nid]
            
            if expired_notifications:
                logger.info(f"Cleaned up {len(expired_notifications)} old notifications")
                
        except Exception as e:
            logger.error("Error cleaning up old notifications", error=str(e))
    
    def get_stats(self) -> Dict[str, Any]:
        """Get notification statistics"""
        return {
            "active_notifications": len(self.active_notifications),
            "queue_size": self.priority_queue.qsize(),
            "delivery_stats": dict(self.delivery_stats),
            "active_sessions": len(self.session_users),
            "active_users": len(self.user_sessions),
            "admin_users": len(self.admin_users),
            "recent_notifications": len(self.recent_notifications)
        }
    
    def get_recent_notifications(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent notifications"""
        return list(self.recent_notifications)[-limit:]


# Global notification manager instance
notification_manager = NotificationManager()