"""
User Manager Service - Database Service
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import AsyncGenerator

from ..models.database import AsyncSessionLocal, engine


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_database_health() -> bool:
    """Check database connection health"""
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
            return True
    except Exception:
        return False


async def init_database():
    """Initialize database tables"""
    from ..models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_database():
    """Close database connections"""
    await engine.dispose()