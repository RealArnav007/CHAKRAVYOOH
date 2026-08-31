import logging
import random
import time
from email.message import EmailMessage

import aiosmtplib

from src.config import get_settings

logger = logging.getLogger(__name__)

# In-memory OTP store: email -> (otp_code, expires_at_timestamp)
_otp_store: dict[str, tuple[str, float]] = {}

def cleanup_expired_otps():
    """Prevents RAM exhaustion by removing expired OTPs."""
    now = time.time()
    expired_keys = [k for k, v in _otp_store.items() if v[1] < now]
    for k in expired_keys:
        del _otp_store[k]

def generate_otp_code() -> str:
    return f"{random.randint(100000, 999999)}"

async def send_otp_email(email: str, otp: str):
    settings = get_settings()
    
    if settings.MOCK_OTP:
        logger.info(f"[MOCK OTP] Sent {otp} to {email}")
        return

    msg = EmailMessage()
    msg.set_content(f"Your Pukar Command Center login code is: {otp}\n\nThis code expires in 5 minutes.")
    msg["Subject"] = "Pukar Security - Login Code"
    msg["From"] = f"{settings.SMTP_SENDER_EMAIL}"
    msg["To"] = email

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            use_tls=False,
            start_tls=True
        )
        logger.info(f"OTP sent successfully to {email}")
    except Exception as e:
        logger.error(f"Failed to send OTP to {email}: {e}")
        raise ValueError("Failed to send email")

async def issue_otp(email: str):
    cleanup_expired_otps()
    
    otp = generate_otp_code()
    expires_at = time.time() + 300 
    _otp_store[email] = (otp, expires_at)
    
    await send_otp_email(email, otp)

def verify_otp(email: str, provided_otp: str) -> bool:
    cleanup_expired_otps()
    
    if email not in _otp_store:
        return False
        
    stored_otp, expires_at = _otp_store[email]
    
    if time.time() > expires_at:
        del _otp_store[email]
        return False
        
    if stored_otp == provided_otp:
        del _otp_store[email]
        return True
        
    return False
