from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.rbac import get_current_user
from src.database.models import User, Zone
from src.dependencies import get_db_session

router = APIRouter()

class ZoneResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    zone_id: str
    name: str | None
    status: str
    center_lat: float
    center_lon: float
    radius_m: float
    report_count: int

@router.get("/", response_model=List[ZoneResponse])
async def list_zones(
    db: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_current_user)
):
    """List all geographic zones and their severity state."""
    stmt = select(Zone).order_by(Zone.updated_at.desc())
    result = await db.execute(stmt)
    zones = result.scalars().all()

    return [
        ZoneResponse(
            zone_id=z.zone_id,
            name=z.name,
            status=z.status,
            center_lat=z.center_lat,
            center_lon=z.center_lon,
            radius_m=z.radius_m,
            report_count=z.report_count
        ) for z in zones
    ]

@router.get("/{zone_id}", response_model=ZoneResponse)
async def get_zone(
    zone_id: str,
    db: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_current_user)
):
    """Get a specific zone by its ID."""
    stmt = select(Zone).where(Zone.zone_id == zone_id).limit(1)
    result = await db.execute(stmt)
    zone = result.scalar_one_or_none()
    
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
        
    return ZoneResponse(
        zone_id=zone.zone_id,
        name=zone.name,
        status=zone.status,
        center_lat=zone.center_lat,
        center_lon=zone.center_lon,
        radius_m=zone.radius_m,
        report_count=zone.report_count
    )
