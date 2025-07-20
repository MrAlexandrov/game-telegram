"""
User Manager Service - Authentication Service
"""

from datetime import datetime, timedelta
from typing import Optional
import jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from ..config import settings
from ..crud import UserCRUD, UserSessionCRUD
from ..schemas import UserSessionCreate
from ..models import User


class AuthService:
    """Authentication service"""
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[dict]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
            return payload
        except jwt.PyJWTError:
            return None
    
    async def authenticate_user(self, db: AsyncSession, telegram_id: int) -> Optional[User]:
        """Authenticate user by telegram_id"""
        user = await UserCRUD.get_user_by_telegram_id(db, telegram_id)
        if user and user.is_active:
            await UserCRUD.update_last_seen(db, user.id)
            return user
        return None
    
    async def create_user_session(
        self, 
        db: AsyncSession, 
        user: User, 
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> str:
        """Create user session and return access token"""
        # Create session in database
        session_data = UserSessionCreate(
            user_id=user.id,
            user_agent=user_agent,
            ip_address=ip_address
        )
        session = await UserSessionCRUD.create_session(db, session_data)
        
        # Create JWT token
        token_data = {
            "sub": str(user.id),
            "telegram_id": user.telegram_id,
            "role": user.role,
            "session_id": str(session.id)
        }
        access_token = self.create_access_token(token_data)
        
        return access_token
    
    async def get_current_user(self, db: AsyncSession, token: str) -> Optional[User]:
        """Get current user from token"""
        payload = self.verify_token(token)
        if not payload:
            return None
        
        user_id = payload.get("sub")
        session_id = payload.get("session_id")
        
        if not user_id or not session_id:
            return None
        
        # Verify session is still active
        session = await UserSessionCRUD.get_session_by_token(db, token)
        if not session:
            return None
        
        # Get user
        user = await UserCRUD.get_user_by_id(db, uuid.UUID(user_id))
        if not user or not user.is_active:
            return None
        
        return user
    
    async def logout_user(self, db: AsyncSession, token: str) -> bool:
        """Logout user by invalidating session"""
        return await UserSessionCRUD.invalidate_session(db, token)
    
    async def logout_all_sessions(self, db: AsyncSession, user_id: uuid.UUID) -> int:
        """Logout user from all sessions"""
        return await UserSessionCRUD.invalidate_user_sessions(db, user_id)
    
    def is_admin(self, user: User) -> bool:
        """Check if user is admin"""
        return user.role == "admin"
    
    def require_admin(self, user: User) -> bool:
        """Require admin role"""
        if not self.is_admin(user):
            raise PermissionError("Admin access required")
        return True
    
    @property
    def settings(self):
        """Access to settings"""
        return settings


# Global auth service instance
auth_service = AuthService()