"""
User Manager Service - Pydantic Schemas
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
import uuid


class UserBase(BaseModel):
    """Base user schema"""
    telegram_id: int = Field(..., description="Telegram user ID")
    username: Optional[str] = Field(None, description="Telegram username")
    first_name: Optional[str] = Field(None, description="User's first name")
    last_name: Optional[str] = Field(None, description="User's last name")
    language_code: Optional[str] = Field("en", description="User's language code")


class UserCreate(UserBase):
    """Schema for creating a user"""
    role: str = Field("player", description="User role (player/admin)")


class UserUpdate(BaseModel):
    """Schema for updating a user"""
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    language_code: Optional[str] = None


class UserResponse(UserBase):
    """Schema for user response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_seen: Optional[datetime] = None


class UserLogin(BaseModel):
    """Schema for user login"""
    telegram_id: int = Field(..., description="Telegram user ID")


class TokenResponse(BaseModel):
    """Schema for token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserSessionCreate(BaseModel):
    """Schema for creating user session"""
    user_id: uuid.UUID
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None


class UserSessionResponse(BaseModel):
    """Schema for user session response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    user_id: uuid.UUID
    session_token: str
    expires_at: datetime
    is_active: bool
    created_at: datetime


class AdminCheckResponse(BaseModel):
    """Schema for admin check response"""
    is_admin: bool
    user_id: uuid.UUID
    role: str


class HealthResponse(BaseModel):
    """Schema for health check response"""
    status: str
    timestamp: datetime
    version: str
    database: str