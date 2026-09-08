from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.session import get_db
from src.auth.rbac import get_current_user
from src.database.models import User
from src.cyclone.contracts import CycloneIntelligence
from src.cyclone.store import (
    save_intelligence_frame,
    save_zone_risks,
    get_active_cyclones,
    get_zone_risks,
    get_active_alerts
)
from src.cyclone.risk_engine import evaluate_risk
from src.cyclone.alerts import generate_alerts, get_authority_public_key_hex, AUTHORITY_KEY_ID
from src.cyclone.processor import process_cyclone_intelligence
from src.database.session import async_session_maker
from src.realtime.connection_manager import manager as ws_manager
from src.cyclone.events import get_intelligence_events, get_risk_updated_event
from src.zones.severity.state import elevate_zone_for_cyclone
from src.database.models import Zone
from sqlalchemy import select
from src.cyclone.replay import init_replay_routes

router = APIRouter(prefix="/cyclone", tags=["Cyclone Intelligence"])
init_replay_routes(router)


@router.post("/intelligence", status_code=status.HTTP_202_ACCEPTED)
@router.post("/ingest", status_code=status.HTTP_202_ACCEPTED)
async def ingest_intelligence(
    intelligence: CycloneIntelligence,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user)
):
    """
    Project Chakravyooh: Ingests intelligence from the AI engine.
    Idempotent. Processed asynchronously.
    """
    if user.role not in ["admin", "system"]:
        raise HTTPException(status_code=403, detail="Only system accounts can ingest AI intelligence")
        
    # Offload processing to background task to immediately ACK the AI engine
    background_tasks.add_task(process_cyclone_intelligence, intelligence, intelligence.model_dump(mode='json'))
    return {"status": "accepted", "cyclone_id": intelligence.cyclone_id}

@router.get("/active")
async def list_active_cyclones(db: AsyncSession = Depends(get_db)):
    """
    Returns the latest state of all tracked cyclones, including zone risks and alerts.
    """
    cyclones = await get_active_cyclones(db)
    result = []
    
    for c in cyclones:
        risks = await get_zone_risks(db, c.cyclone_id)
        alerts = await get_active_alerts(db, c.cyclone_id)
        
        result.append({
            "cyclone_id": c.cyclone_id,
            "name": c.name,
            "stage": c.stage,
            "intensity_level": c.intensity_level,
            "current_lat": c.current_lat,
            "current_lon": c.current_lon,
            "timestamp": c.timestamp,
            "risks": [
                {
                    "zone_id": r.zone_id,
                    "zone_name": r.zone_name,
                    "risk_level": r.risk_level,
                    "distance_km": r.distance_km,
                    "eta_hours": r.eta_hours
                } for r in risks
            ],
            "alerts": [
                {
                    "alert_id": a.alert_id,
                    "type": a.type,
                    "message": a.message,
                    "priority": a.priority,
                    "zones": a.zone_ids
                } for a in alerts
            ]
        })
        
    return result

@router.get("/alerts")
async def list_alerts(db: AsyncSession = Depends(get_db)):
    """Returns all ACTIVE cyclone warning alerts with signature data for client verification."""
    alerts = await get_active_alerts(db)
    return alerts

@router.get("/alerts/authority-key")
async def get_alert_authority_key():
    """
    Returns the Ed25519 public key used by the Chakravyooh authority to sign all CYCLONE_WARNING
    alerts (Master PRD §22). Android and mesh clients should cache this key and use it to verify
    alert signatures offline before accepting or relaying any warning.
    """
    return {
        "authority_key_id": AUTHORITY_KEY_ID,
        "public_key_hex": get_authority_public_key_hex(),
        "algorithm": "Ed25519",
        "usage": "Verify the `signature` field in CYCLONE_WARNING alerts against this public key.",
    }

@router.get("/{id}")
async def get_cyclone(id: str, db: AsyncSession = Depends(get_db)):
    from src.database.models import CycloneLatest
    stmt = select(CycloneLatest).where(CycloneLatest.cyclone_id == id)
    c = (await db.execute(stmt)).scalars().first()
    if not c:
        raise HTTPException(404, "Cyclone not found")
    return c

@router.get("/{id}/risk")
async def get_cyclone_risk(id: str, db: AsyncSession = Depends(get_db)):
    risks = await get_zone_risks(db, id)
    return risks
