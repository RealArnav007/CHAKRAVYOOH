"""
User Service — handles user lookup and management.
"""
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User

logger = logging.getLogger(__name__)


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    stmt = select(User).where(User.email == email).limit(1)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: str) -> User | None:
    stmt = select(User).where(User.user_id == user_id).limit(1)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def set_user_role(db: AsyncSession, user_id: str, role: str) -> User | None:
    """Updates a user's role. Used by SUPER_ADMIN for role assignment."""
    user = await get_user_by_id(db, user_id)
    if user:
        user.role = role
        await db.commit()
        await db.refresh(user)
    return user


async def deactivate_user(db: AsyncSession, user_id: str) -> User | None:
    user = await get_user_by_id(db, user_id)
    if user:
        user.is_active = False
        await db.commit()
        await db.refresh(user)
    return user
