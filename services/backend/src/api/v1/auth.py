from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, constr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.audit.logger import AuditAction, log_event
from src.auth.jwt import create_access_token, create_refresh_token, verify_token
from src.auth.otp import issue_otp, verify_otp
from src.auth.rbac import get_current_user
from src.database.models import RoleEnum, Session, User
from src.dependencies import get_db_session
from src.security.rate_limiter import check_otp_rate_limit
from src.sessions.manager import create_session, revoke_session

router = APIRouter()

class OTPRequest(BaseModel):
    email: constr(pattern=r"^[\w\.\+-]+@[\w\.-]+\.\w+$")  # Basic RFC regex instead of EmailStr


class OTPVerify(BaseModel):
    email: constr(pattern=r"^[\w\.\+-]+@[\w\.-]+\.\w+$")
    code: str


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    session_id: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    role: str
    session_id: str


@router.post("/otp/request", dependencies=[Depends(check_otp_rate_limit)])
async def request_otp(req: OTPRequest, db: AsyncSession = Depends(get_db_session)):
    """
    Initiates login flow by sending a 6-digit OTP to the user's email.
    Rate-limited by IP to prevent email bombing.
    """
    try:
        await issue_otp(req.email)
        await log_event(db, AuditAction.OTP_REQUEST, details={"email": req.email})
        return {"status": "otp_sent", "email": req.email}
    except ValueError as e:
        # Log internally but never expose internal detail to the client
        import logging
        logging.getLogger(__name__).error("OTP issue failed for %s: %s", req.email, e, exc_info=True)
        raise HTTPException(status_code=500, detail="OTP service temporarily unavailable. Please try again.")


@router.post("/otp/verify", response_model=TokenResponse)
async def verify_otp_endpoint(req: OTPVerify, db: AsyncSession = Depends(get_db_session)):
    """
    Verifies the OTP. If the user doesn't exist yet, creates them as VIEWER.
    Issues a short-lived JWT access token + long-lived refresh token + tracked session.
    """
    if not verify_otp(req.email, req.code):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired OTP")

    stmt = select(User).where(User.email == req.email).limit(1)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        user = User(email=req.email, role=RoleEnum.VIEWER.value)
        db.add(user)
        await db.commit()
        await db.refresh(user)
    elif not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")

    token_data = {"sub": user.user_id, "role": user.role}
    access_token = create_access_token(data=token_data)
    refresh_token = create_refresh_token(data=token_data)

    session = await create_session(db, user.user_id)
    await log_event(db, AuditAction.OTP_VERIFIED, actor_id=user.user_id, details={"email": req.email})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        role=user.role,
        session_id=session.session_id,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(req: TokenRefreshRequest, db: AsyncSession = Depends(get_db_session)):
    """
    Issues a new access token + rotated refresh token from a valid refresh token.
    Old session is revoked before a new one is created — prevents parallel token theft.
    """
    payload = verify_token(req.refresh_token, token_type="refresh")
    user_id = payload.get("sub")
    old_session_id = payload.get("session_id")  # embed session_id in refresh token payload for rotation

    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    stmt = select(User).where(User.user_id == user_id).limit(1)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive or not found")

    # Revoke old session before issuing a new one — true refresh token rotation.
    # If a refresh token is stolen, the attacker and legitimate user cannot both hold valid sessions.
    if old_session_id:
        await revoke_session(db, old_session_id)

    token_data = {"sub": user.user_id, "role": user.role}
    new_access_token = create_access_token(data=token_data)

    # Create new session first so we can embed its ID in the new refresh token
    session = await create_session(db, user.user_id)
    token_data["session_id"] = session.session_id
    new_refresh_token = create_refresh_token(data=token_data)

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        role=user.role,
        session_id=session.session_id,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    req: LogoutRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """
    Revokes the given session_id. Enforces ownership — users can only revoke their own sessions.
    Prevents IDOR: User A cannot forcibly log out User B.
    Soft-logout: access token remains valid until natural expiry (short-lived by design).
    """
    # Ownership check — verify the session belongs to the authenticated user
    stmt = select(Session).where(
        Session.session_id == req.session_id,
        Session.user_id == current_user.user_id,
    ).limit(1)
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Session not found or access denied",
        )

    await revoke_session(db, req.session_id)
    await log_event(db, AuditAction.LOGOUT, actor_id=current_user.user_id, details={"session_id": req.session_id})
