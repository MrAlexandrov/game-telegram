"""
User Manager Service - Authentication Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from ..schemas import UserLogin, TokenResponse, UserResponse
from ..services.database import get_db
from ..services.auth import auth_service
from ..models import User

router = APIRouter()
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Dependency to get current authenticated user"""
    token = credentials.credentials
    user = await auth_service.get_current_user(db, token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Dependency to get current authenticated admin user"""
    if not auth_service.is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


@router.post("/login", response_model=TokenResponse)
async def login(
    user_data: UserLogin,
    db: AsyncSession = Depends(get_db),
    user_agent: Optional[str] = Header(None),
    x_forwarded_for: Optional[str] = Header(None)
):
    """Login user and return access token"""
    user = await auth_service.authenticate_user(db, user_data.telegram_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials or user not found"
        )
    
    # Extract IP address
    ip_address = x_forwarded_for.split(',')[0].strip() if x_forwarded_for else None
    
    # Create session and token
    access_token = await auth_service.create_user_session(
        db, user, user_agent, ip_address
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=auth_service.settings.JWT_EXPIRE_MINUTES * 60
    )


@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Logout current user"""
    token = credentials.credentials
    success = await auth_service.logout_user(db, token)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to logout"
        )
    
    return {"message": "Successfully logged out"}


@router.post("/logout-all")
async def logout_all(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Logout user from all sessions"""
    count = await auth_service.logout_all_sessions(db, current_user.id)
    return {"message": f"Logged out from {count} sessions"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    user_agent: Optional[str] = Header(None),
    x_forwarded_for: Optional[str] = Header(None)
):
    """Refresh access token"""
    # Extract IP address
    ip_address = x_forwarded_for.split(',')[0].strip() if x_forwarded_for else None
    
    # Create new session and token
    access_token = await auth_service.create_user_session(
        db, current_user, user_agent, ip_address
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=auth_service.settings.JWT_EXPIRE_MINUTES * 60
    )