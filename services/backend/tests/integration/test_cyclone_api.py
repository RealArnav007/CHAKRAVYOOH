import pytest
from fastapi.testclient import TestClient
from src.main import app

def test_cyclone_replay_endpoint():
    client = TestClient(app)
    response = client.post("/api/v1/cyclone/replay/start")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "replay_started"
    assert body["frames"] == 4
    assert body["interval_s"] == 3  # Default interval

def test_cyclone_replay_custom_interval():
    client = TestClient(app)
    response = client.post("/api/v1/cyclone/replay/start?interval_s=5")
    assert response.status_code == 200
    body = response.json()
    assert body["interval_s"] == 5

def test_cyclone_alerts_authority_key():
    client = TestClient(app)
    response = client.get("/api/v1/cyclone/alerts/authority-key")
    assert response.status_code == 200
    body = response.json()
    assert body["algorithm"] == "Ed25519"
    assert body["authority_key_id"] == "chakravyooh-authority-v1"
    assert len(body["public_key_hex"]) == 64  # Ed25519 verify key = 32 bytes = 64 hex chars


