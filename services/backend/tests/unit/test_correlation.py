import pytest
from datetime import datetime, timezone
from src.database.models import Incident, SOSReport, Zone
from src.incidents.correlation.engine import correlate_incident
from src.incidents.matching.geo_spatial import haversine_distance
from sqlalchemy import select


def test_haversine_distance():
    """Test haversine formula with known coordinates."""
    # New Delhi to a point ~1.1km north
    lat1, lon1 = 28.6139, 77.2090
    lat2, lon2 = 28.6239, 77.2090

    dist = haversine_distance(lat1, lon1, lat2, lon2)
    assert 1100 < dist < 1200

    # Exact same point
    assert haversine_distance(lat1, lon1, lat1, lon1) == 0.0


@pytest.mark.asyncio
async def test_correlate_incident_new(async_db):
    """Test that an SOS report with no nearby incidents creates a new one."""
    # Build a minimal SOSReport (only fields the engine reads directly)
    report = SOSReport(
        msg_id="r1",
        origin_id="o1",
        origin_key_id="ok1",
        created_at=datetime.now(timezone.utc),
        nonce="n1",
        lat=28.6139,
        lon=77.2090,
        acc=5.0,
        trigger_type="manual",
        request_type="medical",
        severity="critical",
        regex_score=80,
        local_model_score=85,
        confidence=0.9,
        payload_enc="enc",
        priority_score=85,
        ai_category="medical",
    )
    async_db.add(report)
    await async_db.flush()

    incident_id = await correlate_incident(async_db, report)
    assert incident_id is not None

    # Verify Incident created
    stmt = select(Incident).where(Incident.incident_id == incident_id)
    inc = (await async_db.execute(stmt)).scalar_one()
    assert inc.lat == 28.6139
    assert inc.lon == 77.2090
    assert inc.priority_level == "CRITICAL"
    assert inc.report_count == 1

    # Verify Zone created and linked
    assert inc.zone_id is not None
    stmt = select(Zone).where(Zone.zone_id == inc.zone_id)
    zone = (await async_db.execute(stmt)).scalar_one()
    # 1 incident with CRITICAL priority: total_reports=1 < 5, but max_priority is CRITICAL
    # Rule: total < 5 AND max NOT in [HIGH, CRITICAL] → EMERGING
    # Since max IS CRITICAL, we skip EMERGING → HIGH (total < 15, max != CRITICAL? no) → CRITICAL
    assert zone.status == "CRITICAL"


@pytest.mark.asyncio
async def test_correlate_incident_existing(async_db):
    """Test that a nearby report joins an existing incident and upgrades priority."""
    # Create baseline incident
    inc = Incident(
        lat=28.6139, lon=77.2090,
        priority_level="MEDIUM",
        report_count=1,
        category="medical",
        created_at=datetime.now(timezone.utc),
    )
    async_db.add(inc)
    await async_db.flush()
    incident_id = inc.incident_id

    # Create nearby report (within ~130m)
    report = SOSReport(
        msg_id="r2",
        origin_id="o2",
        origin_key_id="ok2",
        created_at=datetime.now(timezone.utc),
        nonce="n2",
        lat=28.6150,
        lon=77.2090,
        acc=5.0,
        trigger_type="manual",
        request_type="medical",
        severity="critical",
        regex_score=90,
        local_model_score=90,
        confidence=0.95,
        payload_enc="enc",
        priority_score=90,
        ai_category="medical",
    )
    async_db.add(report)
    await async_db.flush()

    returned_id = await correlate_incident(async_db, report)

    assert returned_id == incident_id

    stmt = select(Incident).where(Incident.incident_id == incident_id)
    refreshed = (await async_db.execute(stmt)).scalar_one()
    assert refreshed.priority_level == "CRITICAL"  # Upgraded from MEDIUM
