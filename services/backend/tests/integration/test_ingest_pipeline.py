import pytest
import time
import nacl.encoding
from src.sos.validation.validator import SosPacket
from src.security.canonicalization.serializer import serialize_canonical_bytes
from src.database.models import DeviceKey
from sqlalchemy import select

@pytest.mark.asyncio
async def test_full_ingestion_pipeline(async_client, async_db, crypto_keys, monkeypatch):
    """
    End-to-end test of the SOS Ingestion Pipeline.
    Tests Validation -> Dedup -> Replay -> Signature -> Decryption -> Persistence.
    """
    # 1. Register the device key in the database
    device_key = DeviceKey(
        origin_key_id="test-key-id",
        origin_id="test-origin",
        ed25519_public_key=crypto_keys["device_verify"],
        x25519_public_key="dummy"
    )
    async_db.add(device_key)
    await async_db.commit()
    
    # Override settings for decryption
    from src.config import get_settings
    settings = get_settings()
    monkeypatch.setattr(settings, "BACKEND_X25519_PRIVATE_KEY", crypto_keys["backend_priv"])
    
    # 2. Encrypt a payload
    backend_pub = nacl.public.PublicKey(crypto_keys["backend_pub"], encoder=nacl.encoding.HexEncoder)
    sealed_box = nacl.public.SealedBox(backend_pub)
    encrypted_payload = sealed_box.encrypt(b"Help, fire!")
    payload_enc_hex = nacl.encoding.HexEncoder.encode(encrypted_payload).decode("utf-8")
    
    # 3. Create the packet
    now_ms = int(time.time() * 1000)
    packet_dict = {
        "msg_id": "test-sos-uuid-1",
        "origin_id": "test-origin",
        "origin_key_id": "test-key-id",
        "created_at": now_ms,
        "nonce": "test-nonce",
        "lat": 1.0,
        "lon": 1.0,
        "acc": 5.0,
        "trigger_type": "manual",
        "request_type": "fire",
        "severity": "critical",
        "regex_score": 90,
        "local_model_score": 85,
        "confidence": 0.99,
        "payload_enc": payload_enc_hex,
        "ttl": 5,
        "hops": 0,
        "sig": ""
    }
    
    packet = SosPacket(**packet_dict)
    
    # 4. Sign the packet
    canonical_bytes = serialize_canonical_bytes(packet)
    signed = crypto_keys["device_sign_obj"].sign(canonical_bytes)
    packet_dict["sig"] = nacl.encoding.HexEncoder.encode(signed.signature).decode("utf-8")
    
    # 5. Send the request
    req_payload = {
        "packet": packet_dict,
        "received_at": now_ms
    }
    
    # Need to pass Gateway-Id for rate limit
    headers = {"X-Gateway-Id": "gateway-1"}
    
    response = await async_client.post("/api/v1/sos/ingest", json=req_payload, headers=headers)
    
    # Should be successful
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "accepted"
    assert "sos_id" in data
    
    # 6. Verify idempotent duplicate handling
    response2 = await async_client.post("/api/v1/sos/ingest", json=req_payload, headers=headers)
    assert response2.status_code == 200
    assert response2.json()["status"] == "duplicate"
