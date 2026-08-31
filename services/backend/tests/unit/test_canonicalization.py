import pytest
import time
from src.sos.validation.validator import SosPacket
from src.security.canonicalization.serializer import serialize_canonical_bytes

def test_canonical_serialization_format():
    """Tests that a packet is serialized correctly according to protocol specs."""
    now_ms = int(time.time() * 1000)
    
    packet = SosPacket(
        msg_id="123e4567-e89b-12d3-a456-426614174000",
        origin_id="device-A",
        origin_key_id="key-A",
        created_at=now_ms,
        nonce="random123",
        lat=28.6139,
        lon=77.2090,
        acc=10.5,
        trigger_type="manual",
        request_type="medical",
        severity="critical",
        regex_score=80,
        local_model_score=90,
        confidence=0.95,
        payload_enc="encrypted_data",
        ttl=5,
        hops=1,
        prev_hop_id="node-B",
        sig="dummy_sig"
    )
    
    result = serialize_canonical_bytes(packet).decode("utf-8")
    
    expected_str = f"123e4567-e89b-12d3-a456-426614174000|device-A|key-A|{now_ms}|random123|28.613900|77.209000|10.50|manual|medical|critical|80|90|0.9500|encrypted_data"
    
    assert result == expected_str
    
def test_canonical_serialization_float_formatting():
    """Validates that floating point numbers are strictly formatted as %.6f, %.2f, %.4f"""
    packet = SosPacket(
        msg_id="abc", origin_id="def", origin_key_id="ghi", created_at=123, nonce="xyz",
        lat=1.0, lon=2.1, acc=5, trigger_type="t", request_type="r", severity="s",
        regex_score=0, local_model_score=0, confidence=1.0, payload_enc="data",
        ttl=0, hops=0, sig="sig"
    )
    
    result = serialize_canonical_bytes(packet).decode("utf-8")
    
    # Check the specific formatted float parts
    parts = result.split("|")
    assert parts[5] == "1.000000"    # lat
    assert parts[6] == "2.100000"    # lon
    assert parts[7] == "5.00"        # acc
    assert parts[13] == "1.0000"     # confidence
