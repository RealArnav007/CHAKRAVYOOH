from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.rbac import RequireRole
from src.database.models import AuditEvent, User
from src.dependencies import get_db_session

router = APIRouter()


class AuditEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_id: str
    action: str
    actor_id: Optional[str]
    details: Optional[dict]
    timestamp: str


@router.get("/", response_model=List[AuditEventResponse])
async def list_audit_events(
    limit: int = Query(default=100, le=500, description="Max records to return"),
    action: Optional[str] = Query(default=None, description="Filter by action type, e.g. DISPATCH_CREATED"),
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(RequireRole(["SUPER_ADMIN", "COMMANDER"])),
):
    """
    Query the immutable audit log.
    Restricted to SUPER_ADMIN and COMMANDER.
    Supports filtering by action type and pagination via limit.
    """
    stmt = select(AuditEvent).order_by(AuditEvent.timestamp.desc()).limit(limit)
    if action:
        stmt = select(AuditEvent).where(AuditEvent.action == action.upper()).order_by(AuditEvent.timestamp.desc()).limit(limit)

    result = await db.execute(stmt)
    events = result.scalars().all()

    return [
        AuditEventResponse(
            event_id=e.event_id,
            action=e.action,
            actor_id=e.actor_id,
            details=e.details,
            timestamp=e.timestamp.isoformat() if e.timestamp else None,
        )
        for e in events
    ]
