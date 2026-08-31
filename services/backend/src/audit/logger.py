"""
Structured Audit Logger — B31
Records immutable audit events for security-sensitive actions.
"""
import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import AuditEvent

logger = logging.getLogger(__name__)

# Supported audit action types
class AuditAction:
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    OTP_REQUEST = "OTP_REQUEST"
    OTP_VERIFIED = "OTP_VERIFIED"
    KEY_REGISTER = "KEY_REGISTER"
    SOS_INGESTED = "SOS_INGESTED"
    INCIDENT_UPDATE = "INCIDENT_UPDATE"
    DISPATCH_CREATED = "DISPATCH_CREATED"
    INCIDENT_RESOLVED = "INCIDENT_RESOLVED"
    SESSION_REVOKED = "SESSION_REVOKED"
    PERMISSION_DENIED = "PERMISSION_DENIED"


async def log_event(
    db: AsyncSession,
    action: str,
    actor_id: str | None = None,
    details: dict[str, Any] | None = None
) -> None:
    """
    Persists an immutable audit event to the database.
    Non-blocking — logs a warning on failure but never raises.
    """
    try:
        event = AuditEvent(
            action=action,
            actor_id=actor_id,
            details=details or {}
        )
        db.add(event)
        await db.commit()
        logger.info(f"AUDIT [{action}] actor={actor_id}")
    except Exception as e:
        logger.error(f"Failed to write audit event [{action}]: {e}")
