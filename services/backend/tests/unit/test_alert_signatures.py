"""
Tests -- Cryptographically Signed Alerts (Master PRD S22)
Verifies Ed25519 signing and tamper detection in alert generation.
"""
import json
import pytest
import nacl.encoding
import nacl.signing
import nacl.exceptions

from src.cyclone.alerts import (
    _get_authority_signing_key,
    _sign_alert_canonical,
    get_authority_public_key_hex,
    AUTHORITY_KEY_ID,
)
from datetime import datetime, timezone, timedelta


def test_authority_public_key_is_deterministic():
    key1 = get_authority_public_key_hex()
    key2 = get_authority_public_key_hex()
    assert key1 == key2
    assert len(key1) == 64  # Ed25519 verify key = 32 bytes = 64 hex chars



def test_alert_signature_is_valid():
    valid_until = datetime.now(timezone.utc) + timedelta(hours=24)
    sig_hex = _sign_alert_canonical(
        alert_id="ALT-test-001",
        version=1,
        cyclone_id="CYC-2026-BAY-TEST",
        priority="EXTREME",
        message="TEST WARNING -- Seek shelter.",
        zone_ids=["Z-A", "Z-B"],
        valid_until=valid_until,
    )
    canonical = json.dumps({
        "alert_id": "ALT-test-001",
        "version": 1,
        "cyclone_id": "CYC-2026-BAY-TEST",
        "priority": "EXTREME",
        "message": "TEST WARNING -- Seek shelter.",
        "zone_ids": sorted(["Z-A", "Z-B"]),
        "valid_until": valid_until.isoformat(),
        "authority_key_id": AUTHORITY_KEY_ID,
    }, sort_keys=True, separators=(",", ":"))

    pub_key_hex = get_authority_public_key_hex()
    verify_key = nacl.signing.VerifyKey(bytes.fromhex(pub_key_hex))
    sig_bytes = bytes.fromhex(sig_hex)
    verify_key.verify(canonical.encode(), sig_bytes)


def test_tampered_alert_fails_verification():
    valid_until = datetime.now(timezone.utc) + timedelta(hours=24)
    sig_hex = _sign_alert_canonical(
        alert_id="ALT-test-002",
        version=1,
        cyclone_id="CYC-2026-BAY-TEST",
        priority="HIGH",
        message="Original safe message.",
        zone_ids=["Z-C"],
        valid_until=valid_until,
    )
    tampered = json.dumps({
        "alert_id": "ALT-test-002",
        "version": 1,
        "cyclone_id": "CYC-2026-BAY-TEST",
        "priority": "EXTREME",
        "message": "Original safe message.",
        "zone_ids": sorted(["Z-C"]),
        "valid_until": valid_until.isoformat(),
        "authority_key_id": AUTHORITY_KEY_ID,
    }, sort_keys=True, separators=(",", ":"))

    pub_key_hex = get_authority_public_key_hex()
    verify_key = nacl.signing.VerifyKey(bytes.fromhex(pub_key_hex))
    sig_bytes = bytes.fromhex(sig_hex)
    with pytest.raises(nacl.exceptions.BadSignatureError):
        verify_key.verify(tampered.encode(), sig_bytes)


def test_signature_is_128_hex_chars():
    valid_until = datetime.now(timezone.utc) + timedelta(hours=24)
    sig_hex = _sign_alert_canonical(
        alert_id="ALT-test-003",
        version=1,
        cyclone_id="CYC-2026-TEST",
        priority="HIGH",
        message="Verify length.",
        zone_ids=["Z-D"],
        valid_until=valid_until,
    )
    assert len(sig_hex) == 128
