import pytest
import time
import nacl.encoding
from src.sos.validation.validator import SosPacket
from src.security.canonicalization.serializer import serialize_canonical_bytes
from src.security.signatures.ed25519 import verify_packet_signature

def test_signature_verification_success(crypto_keys):
    """Test valid Ed25519 signature verification."""
    now_ms = int(time.time() * 1000)
    packet = SosPacket(
        msg_id="uuid-1", origin_id="dev-1", origin_key_id="key-1", created_at=now_ms, nonce="nonce-1",
        lat=1.1, lon=2.2, acc=10, trigger_type="t", request_type="r", severity="s",
        regex_score=50, local_model_score=50, confidence=0.5, payload_enc="data",
        ttl=5, hops=0, sig=""
    )
    
    canonical_bytes = serialize_canonical_bytes(packet)
    
    # Sign it using the device's private key
    signing_key = crypto_keys["device_sign_obj"]
    signed = signing_key.sign(canonical_bytes)
    
    # Put signature into the packet
    packet.sig = nacl.encoding.HexEncoder.encode(signed.signature).decode("utf-8")
    
    # Verify using the public key
    assert verify_packet_signature(packet, crypto_keys["device_verify"]) is True

def test_signature_verification_failure_tampered(crypto_keys):
    """Test that modifying the packet body invalidates the signature."""
    now_ms = int(time.time() * 1000)
    packet = SosPacket(
        msg_id="uuid-1", origin_id="dev-1", origin_key_id="key-1", created_at=now_ms, nonce="nonce-1",
        lat=1.1, lon=2.2, acc=10, trigger_type="t", request_type="r", severity="s",
        regex_score=50, local_model_score=50, confidence=0.5, payload_enc="data",
        ttl=5, hops=0, sig=""
    )
    
    canonical_bytes = serialize_canonical_bytes(packet)
    signed = crypto_keys["device_sign_obj"].sign(canonical_bytes)
    packet.sig = nacl.encoding.HexEncoder.encode(signed.signature).decode("utf-8")
    
    # Tamper with the data (e.g. change latitude)
    packet.lat = 9.9
    
    # Should fail
    assert verify_packet_signature(packet, crypto_keys["device_verify"]) is False
