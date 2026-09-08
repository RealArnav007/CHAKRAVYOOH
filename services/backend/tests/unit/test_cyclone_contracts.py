import pytest
from datetime import datetime, timezone
from src.cyclone.contracts import CycloneIntelligence

def test_valid_cyclone_intelligence_schema():
    payload = {
        "schema_version": "1.0",
        "cyclone_id": "CYC-TEST-001",
        "timestamp": "2026-09-08T10:00:00Z",
        "basin": "North Indian Ocean",
        "identification": {
            "detected": True,
            "confidence": 0.94
        }
    }
    
    model = CycloneIntelligence(**payload)
    assert model.cyclone_id == "CYC-TEST-001"
    assert model.identification.detected is True
    assert model.identification.confidence == 0.94
    assert model.schema_version == "1.0"
    
def test_invalid_cyclone_intelligence_schema():
    payload = {
        "cyclone_id": "CYC-TEST-001",
        # Missing required fields
    }
    with pytest.raises(ValueError):
        CycloneIntelligence(**payload)
