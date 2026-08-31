from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Incident, IncidentStatus, SOSReport
from src.incidents.matching.geo_spatial import haversine_distance
from src.zones.clustering.cluster import assign_incident_to_zone


async def correlate_incident(db: AsyncSession, report: SOSReport) -> str:
    """
    Finds a matching open incident within 500m and 2 hours.
    If none found, creates a new Incident.
    Assigns the incident to a Zone, then commits once.
    Returns the incident_id.
    """
    time_threshold = datetime.now(timezone.utc) - timedelta(hours=2)
    delta = 0.005

    stmt = select(Incident).where(
        Incident.status != IncidentStatus.RESOLVED.value,
        Incident.created_at >= time_threshold,
        Incident.lat.between(report.lat - delta, report.lat + delta),
        Incident.lon.between(report.lon - delta, report.lon + delta)
    ).with_for_update()

    result = await db.execute(stmt)
    active_incidents = result.scalars().all()

    best_incident = None
    min_dist = 500.0
    safe_category = report.ai_category or "unknown"

    for inc in active_incidents:
        if inc.category != safe_category and inc.category is not None:
            continue
        dist = haversine_distance(report.lat, report.lon, inc.lat, inc.lon)
        if dist <= min_dist:
            min_dist = dist
            best_incident = inc

    if best_incident:
        # Atomic increment via expression
        best_incident.report_count = Incident.report_count + 1
        best_incident.updated_at = datetime.now(timezone.utc)

        priorities = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
        inc_prio_val = priorities.get(best_incident.priority_level, 0)

        rep_prio_val, rep_prio_level = 1, "LOW"
        if report.priority_score and report.priority_score > 80:
            rep_prio_val, rep_prio_level = 4, "CRITICAL"
        elif report.priority_score and report.priority_score > 50:
            rep_prio_val, rep_prio_level = 3, "HIGH"
        elif report.priority_score and report.priority_score > 30:
            rep_prio_val, rep_prio_level = 2, "MEDIUM"

        if rep_prio_val > inc_prio_val:
            best_incident.priority_level = rep_prio_level

        # Assign zone (no commit inside)
        await assign_incident_to_zone(db, best_incident)
        # Single commit for both incident update + zone assignment
        await db.commit()
        return best_incident.incident_id

    else:
        rep_prio_level = "LOW"
        if report.priority_score and report.priority_score > 80:
            rep_prio_level = "CRITICAL"
        elif report.priority_score and report.priority_score > 50:
            rep_prio_level = "HIGH"
        elif report.priority_score and report.priority_score > 30:
            rep_prio_level = "MEDIUM"

        new_inc = Incident(
            title=f"{safe_category.capitalize()} Emergency",
            description=report.payload_decrypted[:200] if report.payload_decrypted else "No payload",
            category=safe_category,
            priority_level=rep_prio_level,
            lat=report.lat,
            lon=report.lon,
            report_count=1
        )
        db.add(new_inc)
        await db.flush()  # Get incident_id without committing yet

        # Assign zone (flushes internally, no commit)
        await assign_incident_to_zone(db, new_inc)
        # Single commit for both new incident + zone assignment
        await db.commit()
        return new_inc.incident_id
