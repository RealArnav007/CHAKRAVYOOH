from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models import Alert, CycloneZoneRisk
from src.cyclone.contracts import CycloneIntelligence
from src.realtime.events import RealtimeEvent, RealtimeEventType
from src.realtime.connection_manager import manager as ws_manager
import time

async def generate_alerts(db: AsyncSession, intelligence: CycloneIntelligence, risks: list[CycloneZoneRisk]):
    """
    Generates actionable CYCLONE_WARNING alerts for zones hitting HIGH or EXTREME.
    Returns the list of newly created alerts and the realtime events to broadcast.
    """
    new_alerts = []
    events_to_broadcast = []
    
    # Group high-risk zones
    alert_zones = [r for r in risks if r.risk_level in ["EXTREME", "CRITICAL", "HIGH"]]
    if not alert_zones:
        return new_alerts, events_to_broadcast
        
    cyc_id = intelligence.cyclone_id
    stage = intelligence.classification.stage if intelligence.classification else "Tropical Cyclone"
    
    # We create one unified warning for all affected zones to avoid spamming the mesh
    zone_ids = [r.zone_id for r in alert_zones]
    highest_risk = "HIGH"
    if any(r.risk_level == "EXTREME" for r in alert_zones): highest_risk = "EXTREME"
    elif any(r.risk_level == "CRITICAL" for r in alert_zones): highest_risk = "CRITICAL"
    
    # Check deduplication: is there already an ACTIVE alert for this cyclone with the same priority?
    stmt = select(Alert).where(
        Alert.cyclone_id == cyc_id,
        Alert.status == "ACTIVE",
        Alert.priority == highest_risk
    )
    existing = (await db.execute(stmt)).scalars().first()
    
    if not existing:
        zone_names = ", ".join([r.zone_name or "Unknown" for r in alert_zones[:3]])
        if len(alert_zones) > 3:
            zone_names += " and others"
            
        message = f"CYCLONE WARNING — {stage} approaching {zone_names}. Risk: {highest_risk}. Seek shelter. This warning remains valid if cellular networks fail — relay via Pukar mesh."
        
        alert = Alert(
            type="CYCLONE_WARNING",
            cyclone_id=cyc_id,
            stage=stage,
            message=message,
            zone_ids=zone_ids,
            priority=highest_risk
        )
        db.add(alert)
        await db.flush()
        new_alerts.append(alert)
        
        # Collect PUKAR_ALERT_CREATED event
        event = RealtimeEvent(
            event_type=RealtimeEventType.PUKAR_ALERT_CREATED.value,
            payload={
                "alert_id": alert.alert_id,
                "cyclone_id": alert.cyclone_id,
                "message": alert.message,
                "zones": alert.zone_ids,
                "priority": alert.priority
            },
            timestamp=int(time.time() * 1000)
        )
        events_to_broadcast.append(event)
        
    return new_alerts, events_to_broadcast
