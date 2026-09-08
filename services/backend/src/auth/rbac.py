
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.jwt import verify_token
from src.database.models import Session, User
from src.dependencies import get_db_session

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/otp/verify")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db_session)
) -> User:
    """
    Extracts and verifies the user from the JWT, then validates the session
    is still alive in the database.

    Security: this closes the "soft logout" gap — even if an access token is
    still within its 60-minute expiry window, it is immediately invalid once
    the session has been revoked (by logout, admin action, or key rotation).
    """
    payload = verify_token(token)
    user_id = payload.get("sub")
    session_id = payload.get("session_id")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # --- Session liveness check ---
    # If the JWT contains a session_id, verify it still exists and is active.
    # This ensures that logout / admin revocation takes effect immediately.
    if session_id:
        sess_stmt = select(Session).where(
            Session.session_id == session_id,
            Session.revoked_at.is_(None),
        ).limit(1)
        sess_result = await db.execute(sess_stmt)
        if not sess_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session has been revoked. Please log in again.",
                headers={"WWW-Authenticate": "Bearer"},
            )

    stmt = select(User).where(User.user_id == user_id).limit(1)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive or deleted")

    return user

class RequireRole:
    """Dependency class to enforce RBAC roles."""
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    async def __call__(self, current_user: User = Depends(get_current_user)):
        if current_user.role not in self.allowed_roles and current_user.role != "SUPER_ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Required roles: {self.allowed_roles}"
            )
        return current_user
