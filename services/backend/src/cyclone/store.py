from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models import CycloneIntelligenceRecord, CycloneLatest, CycloneZoneRisk, Alert

async def save_intelligence_frame(db: AsyncSession, intelligence_json: dict) -> tuple[bool, CycloneLatest]:
    """
    Saves a new intelligence frame atomically using ON CONFLICT DO NOTHING.
    Upserts the latest pointer atomically using ON CONFLICT DO UPDATE.
    """
    cyc_id = intelligence_json.get("cyclone_id")
    raw_ts = intelligence_json.get("timestamp")
    
    # Ensure timestamp is a Python datetime object for SQLAlchemy DateTime columns
    if isinstance(raw_ts, str):
        ts = datetime.fromisoformat(raw_ts.replace("Z", "+00:00"))
    elif isinstance(raw_ts, datetime):
        ts = raw_ts
    else:
        ts = datetime.now(timezone.utc)
    
    # 1. Atomic Insert for History
    stmt_record = insert(CycloneIntelligenceRecord).values(
        cyclone_id=cyc_id,
        timestamp=ts,
        model_version=intelligence_json.get("model_version", "Chakravyooh-brain-0.1"),
        raw_json=intelligence_json
    ).on_conflict_do_nothing(
        index_elements=["cyclone_id", "timestamp"]
    )
    result = await db.execute(stmt_record)
    
    if result.rowcount == 0:
        # Idempotency check: Already processed this frame
        stmt_latest = select(CycloneLatest).where(CycloneLatest.cyclone_id == cyc_id)
        latest = (await db.execute(stmt_latest)).scalars().first()
        return False, latest

    # 2. Atomic Upsert for Latest State
    ident = intelligence_json.get("identification", {})
    cls = intelligence_json.get("classification", {})
    intense = intelligence_json.get("intensity", {})
    pred = intelligence_json.get("prediction", {})
    curr = pred.get("current_position", {}) if pred else {}
    
    upsert_values = dict(
        name=intelligence_json.get("name"),
        stage=cls.get("stage") if cls else None,
        intensity_level=intense.get("level") if intense else None,
        confidence=ident.get("confidence") if ident else None,
        current_lat=curr.get("lat"),
        current_lon=curr.get("lon"),
        timestamp=ts,
        raw_json=intelligence_json
    )
    
    stmt_latest = insert(CycloneLatest).values(
        cyclone_id=cyc_id,
        **upsert_values
    ).on_conflict_do_update(
        index_elements=["cyclone_id"],
        set_=upsert_values
    )
    await db.execute(stmt_latest)
    
    latest = (await db.execute(select(CycloneLatest).where(CycloneLatest.cyclone_id == cyc_id))).scalars().first()
    return True, latest

async def get_active_cyclones(db: AsyncSession):
    stmt = select(CycloneLatest)
    return (await db.execute(stmt)).scalars().all()

async def get_zone_risks(db: AsyncSession, cyclone_id: str):
    stmt = select(CycloneZoneRisk).where(CycloneZoneRisk.cyclone_id == cyclone_id)
    return (await db.execute(stmt)).scalars().all()

async def save_zone_risks(db: AsyncSession, risks: list[CycloneZoneRisk]):
    for risk in risks:
        db.add(risk)

async def get_active_alerts(db: AsyncSession, cyclone_id: str = None):
    stmt = select(Alert).where(Alert.status == "ACTIVE")
    if cyclone_id:
        stmt = stmt.where(Alert.cyclone_id == cyclone_id)
    return (await db.execute(stmt)).scalars().all()
