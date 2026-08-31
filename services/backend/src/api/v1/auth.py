from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.jwt import create_access_token
from src.auth.otp import issue_otp, verify_otp
from src.database.models import RoleEnum, User
from src.dependencies import get_db_session
from src.security.rate_limiter import check_otp_rate_limit

router = APIRouter()

class OTPRequest(BaseModel):
    email: str

class OTPVerify(BaseModel):
    email: str
    code: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    role: str

@router.post("/otp/request", dependencies=[Depends(check_otp_rate_limit)])
async def request_otp(req: OTPRequest, db: AsyncSession = Depends(get_db_session)):
    """
    Initiates login flow by sending a 6-digit OTP to the user's email.
    Rate-limited by IP to prevent email bombing.
    """
    try:
        await issue_otp(req.email)
        return {"status": "otp_sent", "email": req.email}
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/otp/verify", response_model=TokenResponse)
async def verify_otp_endpoint(req: OTPVerify, db: AsyncSession = Depends(get_db_session)):
    """
    Verifies the OTP. If the user doesn't exist yet, creates them as VIEWER (preventing DB flooding).
    Issues a JWT access token.
    """
    if not verify_otp(req.email, req.code):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired OTP")
        
    stmt = select(User).where(User.email == req.email).limit(1)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        # Create user only AFTER OTP is verified
        user = User(email=req.email, role=RoleEnum.VIEWER.value)
        db.add(user)
        await db.commit()
        await db.refresh(user)
    elif not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")
        
    access_token = create_access_token(
        data={"sub": user.user_id, "role": user.role}
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        role=user.role
    )
