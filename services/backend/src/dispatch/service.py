import time

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import (
    AuditEvent,
    Dispatch,
    DispatchStatus,
    Incident,
    IncidentStatus,
)
from src.realtime.connection_manager import manager as ws_manager
from src.realtime.events import RealtimeEvent, RealtimeEventType


async def dispatch_unit_to_incident(
    db: AsyncSession, incident_id: str, unit_name: str, responder_id: str
) -> Dispatch:
    """
    Creates a new dispatch record and updates the incident status.
    Uses pessimistic locking and state machine checks to prevent concurrent duplicate dispatches.
    """
    stmt = select(Incident).where(Incident.incident_id == incident_id).with_for_update().limit(1)
    result = await db.execute(stmt)
    incident = result.scalar_one_or_none()
    
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    if incident.status != IncidentStatus.NEW.value:
        raise HTTPException(
            status_code=409, 
            detail=f"Cannot dispatch. Incident status is {incident.status}."
        )
        
    dispatch = Dispatch(
        incident_id=incident_id,
        unit_name=unit_name,
        responder_id=responder_id,
        status=DispatchStatus.DISPATCHED.value
    )
    db.add(dispatch)
    
    incident.status = IncidentStatus.DISPATCHED.value
        
    # Audit trail
    audit = AuditEvent(
        action="DISPATCH_CREATED",
        actor_id=responder_id,
        details={"incident_id": incident_id, "unit": unit_name}
    )
    db.add(audit)
    
    await db.commit()
    await db.refresh(dispatch)
    
    # Broadcast event
    event = RealtimeEvent(
        event_type=RealtimeEventType.DISPATCH_UPDATED.value,
        payload={
            "dispatch_id": dispatch.dispatch_id,
            "incident_id": incident_id,
            "unit_name": unit_name,
            "status": dispatch.status
        },
        timestamp=int(time.time() * 1000)
    )
    await ws_manager.broadcast(event)
    
    return dispatch
