"""
Notification Service - Pydantic Schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


class NotificationType(str, Enum):
    """Notification types"""
    CONNECTION_SUCCESS = "connection_success"
    CONNECTION_FAILED = "connection_failed"
    PLAYER_JOINED = "player_joined"
    PLAYER_LEFT = "player_left"
    GAME_STARTED = "game_started"
    GAME_ENDED = "game_ended"
    QUESTION_STARTED = "question_started"
    QUESTION_ENDED = "question_ended"
    SYSTEM_MAINTENANCE = "system_maintenance"
    SERVICE_ERROR = "service_error"
    SECURITY_ALERT = "security_alert"
    CUSTOM = "custom"


class NotificationPriority(str, Enum):
    """Notification priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationChannel(str, Enum):
    """Notification delivery channels"""
    TELEGRAM = "telegram"
    WEBSOCKET = "websocket"
    EMAIL = "email"
    PUSH = "push"
    SMS = "sms"


class NotificationStatus(str, Enum):
    """Notification status"""
    PENDING = "pending"
    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NotificationBase(BaseModel):
    """Base notification schema"""
    recipient_id: str = Field(..., description="Recipient user ID")
    message: str = Field(..., description="Notification message")
    notification_type: NotificationType = Field(NotificationType.CUSTOM, description="Notification type")
    priority: NotificationPriority = Field(NotificationPriority.NORMAL, description="Priority level")
    channels: List[NotificationChannel] = Field([NotificationChannel.TELEGRAM], description="Delivery channels")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional notification data")
    scheduled_at: Optional[datetime] = Field(None, description="Schedule delivery time")
    expires_at: Optional[datetime] = Field(None, description="Expiration time")


class NotificationCreate(NotificationBase):
    """Schema for creating notifications"""
    pass


class NotificationResponse(BaseModel):
    """Schema for notification response"""
    id: str = Field(..., description="Notification ID")
    status: NotificationStatus = Field(..., description="Notification status")
    message: str = Field(..., description="Response message")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    sent_at: Optional[datetime] = Field(None, description="Sent timestamp")
    delivered_at: Optional[datetime] = Field(None, description="Delivered timestamp")
    error_message: Optional[str] = Field(None, description="Error message if failed")


class NotificationBatch(BaseModel):
    """Schema for batch notifications"""
    notifications: List[NotificationCreate] = Field(..., description="List of notifications")
    batch_id: Optional[str] = Field(None, description="Batch identifier")
    priority: NotificationPriority = Field(NotificationPriority.NORMAL, description="Batch priority")


class ConnectionNotification(BaseModel):
    """Schema for connection-specific notifications"""
    event_type: str = Field(..., description="Connection event type")
    session_id: str = Field(..., description="Session ID")
    user_data: Dict[str, Any] = Field(..., description="User data")
    connection_method: Optional[str] = Field(None, description="Connection method used")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class GameEventNotification(BaseModel):
    """Schema for game event notifications"""
    event_type: str = Field(..., description="Game event type")
    session_id: str = Field(..., description="Session ID")
    game_data: Optional[Dict[str, Any]] = Field(None, description="Game-specific data")
    question_data: Optional[Dict[str, Any]] = Field(None, description="Question data")
    results: Optional[Dict[str, Any]] = Field(None, description="Game results")
    winner: Optional[Dict[str, Any]] = Field(None, description="Winner information")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SystemNotification(BaseModel):
    """Schema for system notifications"""
    notification_type: str = Field(..., description="System notification type")
    message: str = Field(..., description="System message")
    severity: str = Field("info", description="Severity level")
    affected_services: Optional[List[str]] = Field(None, description="Affected services")
    maintenance_window: Optional[Dict[str, Any]] = Field(None, description="Maintenance window info")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class NotificationTemplate(BaseModel):
    """Schema for notification templates"""
    template_id: str = Field(..., description="Template ID")
    name: str = Field(..., description="Template name")
    notification_type: NotificationType = Field(..., description="Notification type")
    message_template: str = Field(..., description="Message template with placeholders")
    default_channels: List[NotificationChannel] = Field(..., description="Default channels")
    default_priority: NotificationPriority = Field(NotificationPriority.NORMAL)
    variables: List[str] = Field(default_factory=list, description="Template variables")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class NotificationPreferences(BaseModel):
    """Schema for user notification preferences"""
    user_id: str = Field(..., description="User ID")
    enabled_channels: List[NotificationChannel] = Field(..., description="Enabled channels")
    enabled_types: List[NotificationType] = Field(..., description="Enabled notification types")
    quiet_hours_start: Optional[str] = Field(None, description="Quiet hours start (HH:MM)")
    quiet_hours_end: Optional[str] = Field(None, description="Quiet hours end (HH:MM)")
    timezone: str = Field("UTC", description="User timezone")
    language: str = Field("en", description="Preferred language")
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class NotificationStats(BaseModel):
    """Schema for notification statistics"""
    total_sent: int = Field(0, description="Total notifications sent")
    total_delivered: int = Field(0, description="Total notifications delivered")
    total_failed: int = Field(0, description="Total notifications failed")
    by_type: Dict[str, int] = Field(default_factory=dict, description="Stats by notification type")
    by_channel: Dict[str, int] = Field(default_factory=dict, description="Stats by channel")
    by_priority: Dict[str, int] = Field(default_factory=dict, description="Stats by priority")
    success_rate: float = Field(0.0, description="Success rate percentage")
    average_delivery_time: Optional[float] = Field(None, description="Average delivery time in seconds")
    period_start: datetime = Field(..., description="Statistics period start")
    period_end: datetime = Field(..., description="Statistics period end")


class NotificationHistory(BaseModel):
    """Schema for notification history"""
    notification_id: str = Field(..., description="Notification ID")
    recipient_id: str = Field(..., description="Recipient ID")
    message: str = Field(..., description="Message content")
    notification_type: NotificationType = Field(..., description="Notification type")
    channels: List[NotificationChannel] = Field(..., description="Delivery channels")
    status: NotificationStatus = Field(..., description="Final status")
    created_at: datetime = Field(..., description="Creation timestamp")
    sent_at: Optional[datetime] = Field(None, description="Sent timestamp")
    delivered_at: Optional[datetime] = Field(None, description="Delivered timestamp")
    attempts: int = Field(0, description="Delivery attempts")
    error_message: Optional[str] = Field(None, description="Error message if failed")


class NotificationQueue(BaseModel):
    """Schema for notification queue items"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Queue item ID")
    notification: NotificationCreate = Field(..., description="Notification data")
    priority: int = Field(0, description="Queue priority (higher = more priority)")
    attempts: int = Field(0, description="Processing attempts")
    max_attempts: int = Field(3, description="Maximum attempts")
    next_attempt_at: datetime = Field(default_factory=datetime.utcnow, description="Next attempt time")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class WebhookNotification(BaseModel):
    """Schema for webhook notifications"""
    webhook_url: str = Field(..., description="Webhook URL")
    event_type: str = Field(..., description="Event type")
    payload: Dict[str, Any] = Field(..., description="Webhook payload")
    headers: Optional[Dict[str, str]] = Field(None, description="Custom headers")
    retry_count: int = Field(0, description="Retry attempts")
    max_retries: int = Field(3, description="Maximum retries")
    timeout: int = Field(30, description="Request timeout in seconds")


class NotificationDeliveryReport(BaseModel):
    """Schema for delivery reports"""
    notification_id: str = Field(..., description="Notification ID")
    channel: NotificationChannel = Field(..., description="Delivery channel")
    status: NotificationStatus = Field(..., description="Delivery status")
    delivered_at: Optional[datetime] = Field(None, description="Delivery timestamp")
    error_code: Optional[str] = Field(None, description="Error code if failed")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    delivery_time_ms: Optional[int] = Field(None, description="Delivery time in milliseconds")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Channel-specific metadata")


class BulkNotificationRequest(BaseModel):
    """Schema for bulk notification requests"""
    template_id: Optional[str] = Field(None, description="Template ID to use")
    recipients: List[str] = Field(..., description="List of recipient IDs")
    message: Optional[str] = Field(None, description="Message (if not using template)")
    template_variables: Optional[Dict[str, Any]] = Field(None, description="Template variables")
    notification_type: NotificationType = Field(NotificationType.CUSTOM)
    priority: NotificationPriority = Field(NotificationPriority.NORMAL)
    channels: List[NotificationChannel] = Field([NotificationChannel.TELEGRAM])
    scheduled_at: Optional[datetime] = Field(None, description="Schedule delivery time")
    batch_size: int = Field(100, ge=1, le=1000, description="Processing batch size")


class NotificationAnalytics(BaseModel):
    """Schema for notification analytics"""
    period: str = Field(..., description="Analytics period (hour, day, week, month)")
    total_notifications: int = Field(0, description="Total notifications in period")
    successful_deliveries: int = Field(0, description="Successful deliveries")
    failed_deliveries: int = Field(0, description="Failed deliveries")
    pending_notifications: int = Field(0, description="Pending notifications")
    average_delivery_time: float = Field(0.0, description="Average delivery time in seconds")
    top_notification_types: List[Dict[str, Any]] = Field(default_factory=list)
    channel_performance: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    error_breakdown: Dict[str, int] = Field(default_factory=dict)
    hourly_distribution: List[Dict[str, Any]] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)