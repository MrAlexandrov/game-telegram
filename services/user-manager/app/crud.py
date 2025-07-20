"""
User Manager Service - CRUD Operations
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.exc import IntegrityError
from typing import Optional, List
import uuid
from datetime import datetime, timedelta
import secrets

from .models import User, UserSession
from .schemas import UserCreate, UserUpdate, UserSessionCreate
from .config import settings


class UserCRUD:
    """CRUD operations for User model"""
    
    @staticmethod
    async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
        """Create a new user"""
        try:
            user = User(
                telegram_id=user_data.telegram_id,
                username=user_data.username,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                role=user_data.role,
                language_code=user_data.language_code
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            return user
        except IntegrityError:
            await db.rollback()
            raise ValueError("User with this telegram_id already exists")
    
    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
        """Get user by ID"""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_by_telegram_id(db: AsyncSession, telegram_id: int) -> Optional[User]:
        """Get user by Telegram ID"""
        result = await db.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_user(db: AsyncSession, user_id: uuid.UUID, user_data: UserUpdate) -> Optional[User]:
        """Update user"""
        update_data = user_data.model_dump(exclude_unset=True)
        if not update_data:
            return await UserCRUD.get_user_by_id(db, user_id)
        
        update_data["updated_at"] = datetime.utcnow()
        
        await db.execute(
            update(User)
            .where(User.id == user_id)
            .values(**update_data)
        )
        await db.commit()
        return await UserCRUD.get_user_by_id(db, user_id)
    
    @staticmethod
    async def update_last_seen(db: AsyncSession, user_id: uuid.UUID) -> None:
        """Update user's last seen timestamp"""
        await db.execute(
            update(User)
            .where(User.id == user_id)
            .values(last_seen=datetime.utcnow())
        )
        await db.commit()
    
    @staticmethod
    async def delete_user(db: AsyncSession, user_id: uuid.UUID) -> bool:
        """Delete user"""
        result = await db.execute(delete(User).where(User.id == user_id))
        await db.commit()
        return result.rowcount > 0
    
    @staticmethod
    async def get_users(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[User]:
        """Get list of users"""
        result = await db.execute(
            select(User)
            .offset(skip)
            .limit(limit)
            .order_by(User.created_at.desc())
        )
        return result.scalars().all()
    
    @staticmethod
    async def is_admin(db: AsyncSession, user_id: uuid.UUID) -> bool:
        """Check if user is admin"""
        result = await db.execute(
            select(User.role).where(User.id == user_id)
        )
        role = result.scalar_one_or_none()
        return role == "admin"


class UserSessionCRUD:
    """CRUD operations for UserSession model"""
    
    @staticmethod
    async def create_session(db: AsyncSession, session_data: UserSessionCreate) -> UserSession:
        """Create a new user session"""
        session_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
        
        session = UserSession(
            user_id=session_data.user_id,
            session_token=session_token,
            expires_at=expires_at,
            user_agent=session_data.user_agent,
            ip_address=session_data.ip_address
        )
        
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session
    
    @staticmethod
    async def get_session_by_token(db: AsyncSession, session_token: str) -> Optional[UserSession]:
        """Get session by token"""
        result = await db.execute(
            select(UserSession)
            .where(UserSession.session_token == session_token)
            .where(UserSession.is_active == True)
            .where(UserSession.expires_at > datetime.utcnow())
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def invalidate_session(db: AsyncSession, session_token: str) -> bool:
        """Invalidate session"""
        result = await db.execute(
            update(UserSession)
            .where(UserSession.session_token == session_token)
            .values(is_active=False, updated_at=datetime.utcnow())
        )
        await db.commit()
        return result.rowcount > 0
    
    @staticmethod
    async def invalidate_user_sessions(db: AsyncSession, user_id: uuid.UUID) -> int:
        """Invalidate all user sessions"""
        result = await db.execute(
            update(UserSession)
            .where(UserSession.user_id == user_id)
            .values(is_active=False, updated_at=datetime.utcnow())
        )
        await db.commit()
        return result.rowcount
    
    @staticmethod
    async def cleanup_expired_sessions(db: AsyncSession) -> int:
        """Clean up expired sessions"""
        result = await db.execute(
            delete(UserSession)
            .where(UserSession.expires_at < datetime.utcnow())
        )
        await db.commit()
        return result.rowcount