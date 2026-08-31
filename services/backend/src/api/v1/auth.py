from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.audit.logger import AuditAction, log_event
from src.auth.jwt import create_access_token, create_refresh_token, verify_token
from src.auth.otp import issue_otp, verify_otp
from src.database.models import RoleEnum, User
from src.dependencies import get_db_session
from src.security.rate_limiter import check_otp_rate_limit
from src.sessions.manager import create_session, revoke_session

router = APIRouter()


class OTPRequest(BaseModel):
    email: str


class OTPVerify(BaseModel):
    email: str
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
        raise HTTPException(status_code=500, detail=str(e))


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
    Rejects access tokens used as refresh tokens (type enforcement in verify_token).
    """
    payload = verify_token(req.refresh_token, token_type="refresh")
    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    stmt = select(User).where(User.user_id == user_id).limit(1)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive or not found")

    token_data = {"sub": user.user_id, "role": user.role}
    new_access_token = create_access_token(data=token_data)
    new_refresh_token = create_refresh_token(data=token_data)

    # New session for the rotated token pair
    session = await create_session(db, user.user_id)

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        role=user.role,
        session_id=session.session_id,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(req: LogoutRequest, db: AsyncSession = Depends(get_db_session)):
    """
    Revokes the given session_id. The client must discard both tokens.
    Soft-logout: access token remains valid until natural expiry (short-lived by design).
    """
    await revoke_session(db, req.session_id)
    await log_event(db, AuditAction.LOGOUT, details={"session_id": req.session_id})
