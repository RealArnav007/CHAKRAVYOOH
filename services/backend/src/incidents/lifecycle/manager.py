"""
Incident Lifecycle Manager — B25
Handles lifecycle state transitions: NEW -> DISPATCHED -> RESOLVED.
"""
import logging
import time
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import AuditEvent, Incident, IncidentStatus
from src.realtime.connection_manager import manager as ws_manager
from src.realtime.events import RealtimeEvent, RealtimeEventType

logger = logging.getLogger(__name__)


async def resolve_incident(
    db: AsyncSession, incident_id: str, actor_id: str, notes: str = ""
) -> Incident:
    """
    Marks an incident as RESOLVED and emits a realtime event.
    Only DISPATCHED or NEW incidents can be resolved.
    """
    stmt = select(Incident).where(
        Incident.incident_id == incident_id
    ).with_for_update().limit(1)
    result = await db.execute(stmt)
    incident = result.scalar_one_or_none()

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    if incident.status == IncidentStatus.RESOLVED.value:
        raise HTTPException(status_code=409, detail="Incident already resolved")

    incident.status = IncidentStatus.RESOLVED.value
    incident.updated_at = datetime.now(timezone.utc)

    audit = AuditEvent(
        action="INCIDENT_RESOLVED",
        actor_id=actor_id,
        details={"incident_id": incident_id, "notes": notes}
    )
    db.add(audit)
    await db.commit()
    await db.refresh(incident)

    event = RealtimeEvent(
        event_type=RealtimeEventType.INCIDENT_UPDATED.value,
        payload={
            "incident_id": incident_id,
            "status": "RESOLVED",
            "actor_id": actor_id
        },
        timestamp=int(time.time() * 1000)
    )
    await ws_manager.broadcast(event)

    return incident
