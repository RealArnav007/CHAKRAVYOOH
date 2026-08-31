
from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.rbac import RequireRole, get_current_user
from src.database.models import Incident, User
from src.dependencies import get_db_session
from src.dispatch.service import dispatch_unit_to_incident

router = APIRouter()

class DispatchRequest(BaseModel):
    unit_name: str

class IncidentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    incident_id: str
    title: str | None
    status: str
    priority_level: str
    lat: float
    lon: float
    zone_id: str | None

@router.get("/", response_model=list[IncidentResponse])
async def list_incidents(
    db: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_current_user)
):
    """List all active incidents."""
    stmt = select(Incident).where(Incident.status != "RESOLVED").order_by(Incident.created_at.desc())
    result = await db.execute(stmt)
    incidents = result.scalars().all()

    return [
        IncidentResponse(
            incident_id=inc.incident_id,
            title=inc.title,
            status=inc.status,
            priority_level=inc.priority_level,
            lat=inc.lat,
            lon=inc.lon,
            zone_id=inc.zone_id
        ) for inc in incidents
    ]

@router.post("/{incident_id}/dispatch")
async def dispatch_unit(
    incident_id: str,
    req: DispatchRequest,
    db: AsyncSession = Depends(get_db_session),
    user: User = Depends(RequireRole(["COMMANDER", "RESPONDER"]))
):
    """
    Dispatch a response unit to an incident.
    Requires COMMANDER or RESPONDER role.
    """
    dispatch = await dispatch_unit_to_incident(db, incident_id, req.unit_name, user.user_id)
    return {"status": "success", "dispatch_id": dispatch.dispatch_id, "incident_status": "DISPATCHED"}
