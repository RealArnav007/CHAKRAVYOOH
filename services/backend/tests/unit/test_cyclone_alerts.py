import pytest
from src.cyclone.alerts import generate_alerts
from src.database.models import CycloneZoneRisk
from src.cyclone.contracts import CycloneIntelligence
from unittest.mock import AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_generate_alerts_mesh_payload():
    db = AsyncMock()
    # Mocking db.execute to return no existing alerts
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    db.execute.return_value = mock_result
    
    intel = CycloneIntelligence(
        cyclone_id="CYC-TEST",
        timestamp="2026-09-08T10:00:00Z",
        basin="NIO",
        identification={"detected": True, "confidence": 1.0}
    )
    
    risks = [
        CycloneZoneRisk(zone_id="Z1", zone_name="Puri", risk_level="EXTREME", risk_score=0.9, distance_km=10.0)
    ]
    
    new_alerts, events = await generate_alerts(db, intel, risks)
    
    assert len(new_alerts) == 1
    assert new_alerts[0].priority == "EXTREME"
    assert new_alerts[0].type == "CYCLONE_WARNING"
    assert "Puri" in new_alerts[0].message
    assert len(events) == 1
