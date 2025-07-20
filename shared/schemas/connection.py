"""
Shared Connection Schemas
Schemas for player connection system with QR codes and game codes
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid
import re


class ConnectionStatus(str, Enum):
    """Connection status types"""
    PENDING = "pending"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    REJECTED = "rejected"


class GameCodeStatus(str, Enum):
    """Game code status types"""
    ACTIVE = "active"
    EXPIRED = "expired"
    USED = "used"
    DISABLED = "disabled"


class ConnectionMethod(str, Enum):
    """Connection method types"""
    QR_CODE = "qr_code"
    MANUAL_CODE = "manual_code"
    DEEP_LINK = "deep_link"
    INVITE_LINK = "invite_link"


class GameCodeCreate(BaseModel):
    """Schema for creating a game code"""
    session_id: uuid.UUID = Field(..., description="Session ID")
    code_length: int = Field(6, ge=4, le=10, description="Code length")
    expires_in_minutes: int = Field(60, ge=5, le=1440, description="Expiration time in minutes")
    max_uses: Optional[int] = Field(None, ge=1, description="Maximum number of uses")
    description: Optional[str] = Field(None, max_length=255, description="Code description")


class GameCodeResponse(BaseModel):
    """Schema for game code response"""
    code: str = Field(..., description="Generated game code")
    session_id: uuid.UUID = Field(..., description="Session ID")
    qr_code_url: Optional[str] = Field(None, description="QR code image URL")
    deep_link: str = Field(..., description="Deep link for connection")
    expires_at: datetime = Field(..., description="Expiration timestamp")
    max_uses: Optional[int] = Field(None, description="Maximum uses allowed")
    current_uses: int = Field(0, description="Current number of uses")
    status: GameCodeStatus = Field(GameCodeStatus.ACTIVE, description="Code status")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @validator('code')
    def validate_code_format(cls, v):
        if not re.match(r'^[A-Z0-9]{4,10}$', v):
            raise ValueError('Code must contain only uppercase letters and numbers')
        return v


class ConnectionRequest(BaseModel):
    """Schema for connection request"""
    game_code: str = Field(..., description="Game code to connect with")
    user_id: uuid.UUID = Field(..., description="User ID")
    display_name: str = Field(..., min_length=1, max_length=50, description="Player display name")
    connection_method: ConnectionMethod = Field(..., description="Connection method used")
    user_agent: Optional[str] = Field(None, description="User agent string")
    ip_address: Optional[str] = Field(None, description="IP address")

    @validator('game_code')
    def validate_game_code(cls, v):
        code = v.strip().upper()
        if not re.match(r'^[A-Z0-9]{4,10}$', code):
            raise ValueError('Invalid game code format')
        return code

    @validator('display_name')
    def validate_display_name(cls, v):
        name = v.strip()
        if not name:
            raise ValueError('Display name cannot be empty')
        # Remove excessive whitespace
        return ' '.join(name.split())


class ConnectionResponse(BaseModel):
    """Schema for connection response"""
    success: bool = Field(..., description="Connection success status")
    session_id: Optional[uuid.UUID] = Field(None, description="Session ID if successful")
    participant_id: Optional[uuid.UUID] = Field(None, description="Participant ID if successful")
    session_info: Optional[Dict[str, Any]] = Field(None, description="Session information")
    player_number: Optional[int] = Field(None, description="Player number in session")
    total_players: Optional[int] = Field(None, description="Total players in session")
    error_code: Optional[str] = Field(None, description="Error code if failed")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    connection_id: uuid.UUID = Field(default_factory=uuid.uuid4, description="Unique connection ID")
    connected_at: datetime = Field(default_factory=datetime.utcnow)


class SessionInfoResponse(BaseModel):
    """Schema for session information response"""
    session_id: uuid.UUID = Field(..., description="Session ID")
    session_code: str = Field(..., description="Session code")
    title: str = Field(..., description="Session title")
    description: Optional[str] = Field(None, description="Session description")
    game_type: str = Field(..., description="Game type")
    game_title: Optional[str] = Field(None, description="Game title")
    status: str = Field(..., description="Session status")
    max_players: int = Field(..., description="Maximum players allowed")
    current_players: int = Field(..., description="Current number of players")
    allow_late_join: bool = Field(..., description="Allow late joining")
    question_time_limit: int = Field(..., description="Time limit per question")
    admin_name: Optional[str] = Field(None, description="Admin display name")
    created_at: datetime = Field(..., description="Session creation time")
    started_at: Optional[datetime] = Field(None, description="Session start time")


class ConnectionValidation(BaseModel):
    """Schema for connection validation"""
    game_code: str = Field(..., description="Game code to validate")
    user_id: Optional[uuid.UUID] = Field(None, description="User ID for duplicate check")

    @validator('game_code')
    def validate_game_code(cls, v):
        return v.strip().upper()


class ConnectionValidationResponse(BaseModel):
    """Schema for connection validation response"""
    valid: bool = Field(..., description="Whether the code is valid")
    session_info: Optional[SessionInfoResponse] = Field(None, description="Session info if valid")
    error_code: Optional[str] = Field(None, description="Error code if invalid")
    error_message: Optional[str] = Field(None, description="Error message if invalid")
    can_join: bool = Field(False, description="Whether user can join")
    reason: Optional[str] = Field(None, description="Reason if cannot join")


class DeepLinkData(BaseModel):
    """Schema for deep link data"""
    game_code: str = Field(..., description="Game code")
    session_id: Optional[uuid.UUID] = Field(None, description="Session ID")
    referrer: Optional[str] = Field(None, description="Referrer information")
    utm_source: Optional[str] = Field(None, description="UTM source")
    utm_medium: Optional[str] = Field(None, description="UTM medium")
    utm_campaign: Optional[str] = Field(None, description="UTM campaign")

    @validator('game_code')
    def validate_game_code(cls, v):
        return v.strip().upper()


class QRCodeRequest(BaseModel):
    """Schema for QR code generation request"""
    session_id: uuid.UUID = Field(..., description="Session ID")
    game_code: str = Field(..., description="Game code")
    title: Optional[str] = Field(None, description="Game title for QR code")
    include_text: bool = Field(True, description="Include text with QR code")
    size: int = Field(300, ge=100, le=1000, description="QR code size in pixels")
    format: str = Field("PNG", description="Image format")

    @validator('format')
    def validate_format(cls, v):
        if v.upper() not in ['PNG', 'JPEG', 'JPG']:
            raise ValueError('Format must be PNG or JPEG')
        return v.upper()


class QRCodeResponse(BaseModel):
    """Schema for QR code response"""
    qr_code_data: str = Field(..., description="Base64 encoded QR code image")
    deep_link: str = Field(..., description="Deep link URL")
    game_code: str = Field(..., description="Game code")
    expires_at: Optional[datetime] = Field(None, description="Code expiration time")
    format: str = Field(..., description="Image format")
    size: int = Field(..., description="Image size")


class ConnectionStats(BaseModel):
    """Schema for connection statistics"""
    session_id: uuid.UUID = Field(..., description="Session ID")
    total_connections: int = Field(0, description="Total connection attempts")
    successful_connections: int = Field(0, description="Successful connections")
    failed_connections: int = Field(0, description="Failed connections")
    unique_users: int = Field(0, description="Unique users attempted")
    connection_methods: Dict[str, int] = Field(default_factory=dict, description="Connection methods used")
    error_codes: Dict[str, int] = Field(default_factory=dict, description="Error code frequencies")
    peak_concurrent: int = Field(0, description="Peak concurrent connections")
    average_connection_time: Optional[float] = Field(None, description="Average connection time in seconds")
    last_connection: Optional[datetime] = Field(None, description="Last connection timestamp")


class ConnectionEvent(BaseModel):
    """Schema for connection events"""
    event_id: uuid.UUID = Field(default_factory=uuid.uuid4, description="Event ID")
    session_id: uuid.UUID = Field(..., description="Session ID")
    user_id: Optional[uuid.UUID] = Field(None, description="User ID")
    event_type: str = Field(..., description="Event type")
    connection_method: Optional[ConnectionMethod] = Field(None, description="Connection method")
    game_code: Optional[str] = Field(None, description="Game code used")
    success: bool = Field(..., description="Whether event was successful")
    error_code: Optional[str] = Field(None, description="Error code if failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional event data")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent")


class BulkConnectionRequest(BaseModel):
    """Schema for bulk connection operations"""
    session_id: uuid.UUID = Field(..., description="Session ID")
    user_ids: List[uuid.UUID] = Field(..., min_items=1, max_items=50, description="User IDs to connect")
    display_names: Optional[List[str]] = Field(None, description="Display names for users")
    connection_method: ConnectionMethod = Field(ConnectionMethod.INVITE_LINK, description="Connection method")
    
    @validator('display_names')
    def validate_display_names_length(cls, v, values):
        if v is not None and 'user_ids' in values:
            if len(v) != len(values['user_ids']):
                raise ValueError('Display names list must match user_ids length')
        return v


class BulkConnectionResponse(BaseModel):
    """Schema for bulk connection response"""
    total_requested: int = Field(..., description="Total connections requested")
    successful: int = Field(..., description="Successful connections")
    failed: int = Field(..., description="Failed connections")
    results: List[ConnectionResponse] = Field(..., description="Individual connection results")
    session_info: Optional[SessionInfoResponse] = Field(None, description="Session information")


# Error codes for connection system
CONNECTION_ERROR_CODES = {
    "INVALID_CODE": "Invalid or malformed game code",
    "CODE_NOT_FOUND": "Game code not found",
    "CODE_EXPIRED": "Game code has expired",
    "CODE_DISABLED": "Game code has been disabled",
    "CODE_MAX_USES": "Game code has reached maximum uses",
    "SESSION_NOT_FOUND": "Game session not found",
    "SESSION_FULL": "Game session is full",
    "SESSION_ENDED": "Game session has ended",
    "SESSION_NOT_STARTED": "Game session has not started yet",
    "ALREADY_CONNECTED": "User is already connected to this session",
    "USER_BANNED": "User is banned from this session",
    "INVALID_USER": "Invalid user information",
    "RATE_LIMITED": "Too many connection attempts",
    "SYSTEM_ERROR": "Internal system error",
    "VALIDATION_ERROR": "Request validation failed",
    "UNAUTHORIZED": "Unauthorized access attempt",
    "DUPLICATE_NAME": "Display name already taken in session",
    "LATE_JOIN_DISABLED": "Late joining is disabled for this session"
}