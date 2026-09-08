import pytest
from src.database.models import Zone
from src.zones.severity.state import elevate_zone_for_cyclone

@pytest.mark.asyncio
async def test_no_downgrade_invariant():
    z = Zone(zone_id="Z1", status="CRITICAL")
    
    elevated, _ = await elevate_zone_for_cyclone(z, "LOW")
    assert not elevated
    assert z.status == "CRITICAL" # Should not downgrade
    
    elevated, _ = await elevate_zone_for_cyclone(z, "EXTREME")
    assert elevated
    assert z.status == "EXTREME" # Should upgrade
