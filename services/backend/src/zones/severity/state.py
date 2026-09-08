from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Incident, Zone, ZoneStatus


async def recalculate_zone_severity(db: AsyncSession, zone: Zone) -> None:
    """
    Recalculates a zone's severity based on active incidents inside it.
    Safely handles string priority comparisons by mapping them to integers.
    """
    stmt = select(Incident.priority_level).where(
        Incident.zone_id == zone.zone_id,
        Incident.status != "RESOLVED"
    )
    result = await db.execute(stmt)
    priorities = result.scalars().all()
    
    total_reports = len(priorities)
    
    # Priority mapping to prevent alphabetical sorting bugs (e.g. "MEDIUM" > "CRITICAL")
    prio_map = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
    rev_map = {1: "LOW", 2: "MEDIUM", 3: "HIGH", 4: "CRITICAL"}
    
    if total_reports == 0:
        max_prio_val = 0
    else:
        max_prio_val = max(prio_map.get(p, 1) for p in priorities)
        
    max_priority = rev_map.get(max_prio_val, "LOW")
    
    old_status = zone.status
    
    from src.database.models import CycloneZoneRisk
    
    if total_reports == 0:
        sos_status = ZoneStatus.NORMAL.value
    elif total_reports < 5 and max_priority not in ["HIGH", "CRITICAL"]:
        sos_status = ZoneStatus.EMERGING.value
    elif total_reports < 15 and max_priority != "CRITICAL":
        sos_status = ZoneStatus.HIGH.value
    elif total_reports < 50:
        sos_status = ZoneStatus.CRITICAL.value
    else:
        sos_status = ZoneStatus.EXTREME.value
        
    # Chakravyooh: Enforce No-Downgrade Invariant
    stmt_risk = select(CycloneZoneRisk).where(
        CycloneZoneRisk.zone_id == zone.zone_id
    ).order_by(CycloneZoneRisk.computed_at.desc()).limit(1)
    
    latest_risk = (await db.execute(stmt_risk)).scalars().first()
    
    severity_rank = {
        "NORMAL": 1,
        "EMERGING": 2,
        "HIGH": 3,
        "CRITICAL": 4,
        "EXTREME": 5
    }
    
    final_status = sos_status
    if latest_risk:
        cyclone_status = latest_risk.risk_level
        if severity_rank.get(cyclone_status, 1) > severity_rank.get(sos_status, 1):
            final_status = cyclone_status
            
    if old_status != final_status:
        zone.status = final_status
        zone.updated_at = datetime.now(timezone.utc)
        
        import time
        from src.realtime.events import RealtimeEvent, RealtimeEventType
        from src.realtime.connection_manager import manager as ws_manager
        
        event = RealtimeEvent(
            event_type=RealtimeEventType.ZONE_UPDATED.value,
            payload={
                "zone_id": zone.zone_id,
                "status": zone.status,
                "report_count": zone.report_count
            },
            timestamp=int(time.time() * 1000)
        )
        await ws_manager.broadcast(event)


async def elevate_zone_for_cyclone(zone: Zone, cyclone_risk_level: str) -> tuple[bool, list]:
    """
    Project Chakravyooh: Elevates zone severity based on predicted cyclone risk.
    Enforces the NO-DOWNGRADE Invariant: An SOS-driven CRITICAL zone is never
    downgraded by a lower cyclone score.
    Returns (True, events) if the zone was elevated.
    """
    severity_rank = {
        "NORMAL": 1,
        "EMERGING": 2,
        "HIGH": 3,
        "CRITICAL": 4,
        "EXTREME": 5
    }
    
    current_rank = severity_rank.get(zone.status, 1)
    new_rank = severity_rank.get(cyclone_risk_level, 1)
    
    events_to_broadcast = []
    
    if new_rank > current_rank:
        old_status = zone.status
        zone.status = cyclone_risk_level
        zone.updated_at = datetime.now(timezone.utc)
        
        import time
        from src.realtime.events import RealtimeEvent, RealtimeEventType
        
        # Emit RISK_ZONE_ELEVATED
        event_elevated = RealtimeEvent(
            event_type=RealtimeEventType.RISK_ZONE_ELEVATED.value,
            payload={
                "zone_id": zone.zone_id,
                "old_level": old_status,
                "new_level": zone.status,
                "reason": "cyclone"
            },
            timestamp=int(time.time() * 1000)
        )
        events_to_broadcast.append(event_elevated)
        
        # Also emit standard ZONE_UPDATED so existing SOS command centers see the color change
        event_updated = RealtimeEvent(
            event_type=RealtimeEventType.ZONE_UPDATED.value,
            payload={
                "zone_id": zone.zone_id,
                "status": zone.status,
                "report_count": zone.report_count
            },
            timestamp=int(time.time() * 1000)
        )
        events_to_broadcast.append(event_updated)
        return True, events_to_broadcast
        
    return False, []

