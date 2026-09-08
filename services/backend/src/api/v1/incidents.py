
from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.rbac import RequireRole, get_current_user
from src.database.models import Incident, SOSReport, User
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


class OfficerIncidentResponse(BaseModel):
    """Rich incident payload for the Officer Command Portal (Arnav's frontend)."""
    model_config = ConfigDict(from_attributes=True)

    sos_id: str | None = None
    incident_id: str
    severity: str                   # "CRITICAL" | "WARN" | "INFO"
    priority: int                   # 0-100 from ML scorer
    lat: float
    lon: float
    status: str                     # "NEW" | "DISPATCHED" | "RESOLVED"
    category: str
    ai_summary: str                 # groq_rationale snippet (max 500 chars)
    needs_human_review: bool        # ScoreResult v2 — flag for manual override
    injection_suspected: bool       # ScoreResult v2 — prompt injection detected
    escalation_signal: float        # 0.0-1.0 — zone escalation intensity
    false_alarm_likelihood: float   # 0.0-1.0 — chance this is a drill/false alarm
    received_at: int | None         # epoch ms

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


@router.get("/officer/incidents", response_model=list[OfficerIncidentResponse])
async def officer_incidents(
    db: AsyncSession = Depends(get_db_session),
    user: User = Depends(RequireRole(["COMMANDER", "RESPONDER", "ANALYST", "SUPER_ADMIN"]))
):
    """
    Officer Command Center feed for Arnav's portal.
    Joins Incident + SOSReport to expose all ScoreResult v2 ML fields:
    priority, severity, needs_human_review, injection_suspected,
    escalation_signal, false_alarm_likelihood.
    Returns top 50 active incidents ordered by creation time desc.
    """
    stmt = (
        select(Incident, SOSReport)
        .join(SOSReport, SOSReport.incident_id == Incident.incident_id, isouter=True)
        .where(Incident.status != "RESOLVED")
        .order_by(Incident.created_at.desc())
        .limit(50)
    )
    result = await db.execute(stmt)
    rows = result.all()

    seen, out = set(), []
    for inc, sos in rows:
        if inc.incident_id in seen:
            continue
        seen.add(inc.incident_id)
        reasoning = (sos.ai_reasoning or {}) if sos else {}
        out.append(OfficerIncidentResponse(
            sos_id=sos.sos_id if sos else None,
            incident_id=inc.incident_id,
            severity=sos.severity if sos else "WARN",
            priority=int(sos.priority_score or 50) if sos else 50,
            lat=inc.lat,
            lon=inc.lon,
            status=inc.status,
            category=inc.category or (sos.ai_category if sos else "other"),
            ai_summary=str(reasoning.get("groq_rationale", ""))[:500],
            needs_human_review=bool(sos.needs_human_review) if sos else False,
            injection_suspected=bool(sos.injection_suspected) if sos else False,
            escalation_signal=float(sos.escalation_signal or 0.0) if sos else 0.0,
            false_alarm_likelihood=float(sos.false_alarm_likelihood or 0.0) if sos else 0.0,
            received_at=int(sos.received_at.timestamp() * 1000) if (sos and sos.received_at) else None,
        ))
    return out


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
