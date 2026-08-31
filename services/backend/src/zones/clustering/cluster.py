import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Incident, Zone
from src.incidents.matching.geo_spatial import haversine_distance
from src.zones.severity.state import recalculate_zone_severity


async def assign_incident_to_zone(db: AsyncSession, incident: Incident) -> None:
    """
    Finds the closest Zone within 2km. If none exists, creates a new Zone.
    Then triggers a Zone Severity recalculation.

    NOTE: Does NOT commit — caller is responsible for the final commit.
    """
    delta = 0.02  # ~2km in degrees

    stmt = select(Zone).where(
        Zone.center_lat.between(incident.lat - delta, incident.lat + delta),
        Zone.center_lon.between(incident.lon - delta, incident.lon + delta)
    )

    result = await db.execute(stmt)
    zones = result.scalars().all()

    best_zone = None
    min_dist = 2000.0

    for z in zones:
        dist = haversine_distance(incident.lat, incident.lon, z.center_lat, z.center_lon)
        if dist <= min_dist:
            min_dist = dist
            best_zone = z

    # Resolve report_count safely — may be a SQLAlchemy expression (atomic increment)
    try:
        report_count = int(incident.report_count) if incident.report_count is not None else 1
    except TypeError:
        report_count = 1

    if best_zone:
        incident.zone_id = best_zone.zone_id
        best_zone.report_count = (best_zone.report_count or 0) + report_count
    else:
        new_zone = Zone(
            name=f"Zone-{str(uuid.uuid4())[:6]}",
            center_lat=incident.lat,
            center_lon=incident.lon,
            report_count=report_count
        )
        db.add(new_zone)
        await db.flush()  # Get zone_id without committing
        incident.zone_id = new_zone.zone_id
        best_zone = new_zone

    # Flush so that zone_id is visible on the incident before severity recalculation
    await db.flush()
    await recalculate_zone_severity(db, best_zone)
    # Caller commits — no db.commit() here
