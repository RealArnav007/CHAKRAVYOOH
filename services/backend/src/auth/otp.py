import logging
import secrets
import time
from email.message import EmailMessage

import aiosmtplib

from src.config import get_settings

logger = logging.getLogger(__name__)

# In-memory OTP store: email -> (otp_code, expires_at_timestamp)
_otp_store: dict[str, tuple[str, float]] = {}

# Brute-force lockout: email -> (failed_attempts, lockout_until_timestamp)
_lockout_store: dict[str, tuple[int, float]] = {}
MAX_ATTEMPTS = 5
LOCKOUT_SECONDS = 900  # 15 minutes


def cleanup_expired_otps():
    """Prevents RAM exhaustion by removing expired OTPs and lockouts."""
    now = time.time()
    expired_keys = [k for k, v in _otp_store.items() if v[1] < now]
    for k in expired_keys:
        del _otp_store[k]
    expired_locks = [k for k, v in _lockout_store.items() if v[1] < now]
    for k in expired_locks:
        del _lockout_store[k]


def generate_otp_code() -> str:
    """Generates a 6-digit OTP using a cryptographically secure source."""
    # secrets.randbelow(900000) gives [0, 900000) → add 100000 → [100000, 999999]
    return str(secrets.randbelow(900000) + 100000)


def _is_locked_out(email: str) -> bool:
    """Returns True if the email is under brute-force lockout."""
    if email in _lockout_store:
        attempts, locked_until = _lockout_store[email]
        if locked_until > time.time():
            return True
        del _lockout_store[email]
    return False


def _record_failed_attempt(email: str) -> None:
    """Increments the failed-attempt counter; locks out after MAX_ATTEMPTS."""
    attempts, _ = _lockout_store.get(email, (0, 0))
    attempts += 1
    if attempts >= MAX_ATTEMPTS:
        _lockout_store[email] = (attempts, time.time() + LOCKOUT_SECONDS)
        logger.warning(f"OTP brute-force lockout triggered for {email}")
    else:
        _lockout_store[email] = (attempts, 0)


def _clear_lockout(email: str) -> None:
    """Clears lockout state on successful verification."""
    _lockout_store.pop(email, None)


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

    # Check lockout before anything else
    if _is_locked_out(email):
        logger.warning(f"OTP verify blocked — lockout active for {email}")
        return False

    if email not in _otp_store:
        _record_failed_attempt(email)
        return False

    stored_otp, expires_at = _otp_store[email]

    if time.time() > expires_at:
        del _otp_store[email]
        _record_failed_attempt(email)
        return False

    if stored_otp == provided_otp:
        del _otp_store[email]
        _clear_lockout(email)
        return True

    # Wrong code — record failed attempt
    _record_failed_attempt(email)
    return False
