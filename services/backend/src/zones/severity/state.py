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
    
    if total_reports == 0:
        zone.status = ZoneStatus.NORMAL.value
    elif total_reports < 5 and max_priority not in ["HIGH", "CRITICAL"]:
        zone.status = ZoneStatus.EMERGING.value
    elif total_reports < 15 and max_priority != "CRITICAL":
        zone.status = ZoneStatus.HIGH.value
    elif total_reports < 50:
        zone.status = ZoneStatus.CRITICAL.value
    else:
        zone.status = ZoneStatus.EXTREME.value
        
    if old_status != zone.status:
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
