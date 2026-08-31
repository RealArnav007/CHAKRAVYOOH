import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models import Zone, ZoneStatus, User, RoleEnum
from src.auth.jwt import create_access_token


async def _seed_user(db: AsyncSession) -> str:
    """
    Seeds a real User row into the test DB and returns a valid JWT for it.
    Matches how get_current_user works: it looks up by user_id == sub.
    """
    user = User(
        user_id="zone-test-user-id",
        email="zone-test@example.com",
        role=RoleEnum.VIEWER.value,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    return create_access_token({"sub": user.user_id, "role": user.role, "email": user.email})


@pytest.mark.asyncio
async def test_get_zones_empty(async_client: AsyncClient, async_db: AsyncSession):
    """GET /zones/ returns an empty list when no zones exist."""
    token = await _seed_user(async_db)
    response = await async_client.get(
        "/api/v1/zones/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_zones_populated(async_client: AsyncClient, async_db: AsyncSession):
    """GET /zones/ returns all zones ordered by updated_at desc."""
    token = await _seed_user(async_db)
    z = Zone(
        name="Test Zone",
        status=ZoneStatus.CRITICAL.value,
        center_lat=20.0,
        center_lon=30.0,
        report_count=10,
    )
    async_db.add(z)
    await async_db.commit()
    await async_db.refresh(z)

    response = await async_client.get(
        "/api/v1/zones/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["zone_id"] == z.zone_id
    assert data[0]["status"] == "CRITICAL"
    assert data[0]["report_count"] == 10


@pytest.mark.asyncio
async def test_get_single_zone(async_client: AsyncClient, async_db: AsyncSession):
    """GET /zones/{zone_id} returns the correct zone."""
    token = await _seed_user(async_db)
    z = Zone(
        name="Specific Zone",
        status=ZoneStatus.NORMAL.value,
        center_lat=21.0,
        center_lon=31.0,
        report_count=0,
    )
    async_db.add(z)
    await async_db.commit()
    await async_db.refresh(z)

    response = await async_client.get(
        f"/api/v1/zones/{z.zone_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["zone_id"] == z.zone_id
    assert data["name"] == "Specific Zone"


@pytest.mark.asyncio
async def test_get_zone_not_found(async_client: AsyncClient, async_db: AsyncSession):
    """GET /zones/{zone_id} returns 404 for a non-existent zone."""
    token = await _seed_user(async_db)
    response = await async_client.get(
        "/api/v1/zones/00000000-0000-0000-0000-000000000000",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404

