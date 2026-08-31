"""
Session Manager — B18
Tracks user sessions: session_id, user_id, last_activity, expires_at, revoked_at.
"""
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Session

logger = logging.getLogger(__name__)


async def create_session(db: AsyncSession, user_id: str, expire_days: int = 7) -> Session:
    """Creates a new tracked session for a user."""
    session = Session(
        user_id=user_id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=expire_days)
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def revoke_session(db: AsyncSession, session_id: str) -> None:
    """Marks a session as revoked (logout)."""
    stmt = select(Session).where(Session.session_id == session_id).limit(1)
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    if session:
        session.revoked_at = datetime.now(timezone.utc)
        await db.commit()


async def is_session_valid(db: AsyncSession, session_id: str) -> bool:
    """Returns True if the session exists, is not revoked, and is not expired."""
    stmt = select(Session).where(Session.session_id == session_id).limit(1)
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()

    if not session:
        return False
    if session.revoked_at is not None:
        return False
    if session.expires_at < datetime.now(timezone.utc):
        return False
    return True
