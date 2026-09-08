import json
import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.config import get_settings

settings = get_settings()
SYSTEM_KEY = settings.CHAKRAVYUH_SYSTEM_API_KEY

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_ingest_landfall_imminent_with_bearer_api_key(client):
    with open("ml/cyclone/fixtures/landfall_imminent.json", "r") as f:
        payload = json.load(f)

    response = client.post(
        "/api/v1/cyclone/intelligence",
        json=payload,
        headers={"Authorization": f"Bearer {SYSTEM_KEY}"}
    )
    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "accepted"
    assert body["cyclone_id"] == "CYC-2020-BAY-001"



def test_ingest_landfall_imminent_with_x_api_key(client):
    with open("ml/cyclone/fixtures/landfall_imminent.json", "r") as f:
        payload = json.load(f)

    response = client.post(
        "/api/v1/cyclone/intelligence",
        json=payload,
        headers={"X-API-Key": SYSTEM_KEY}
    )
    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "accepted"


def test_ingest_without_auth_fails(client):
    with open("ml/cyclone/fixtures/landfall_imminent.json", "r") as f:
        payload = json.load(f)

    response = client.post(
        "/api/v1/cyclone/intelligence",
        json=payload
    )
    assert response.status_code == 401


def test_ingest_with_invalid_key_fails(client):
    with open("ml/cyclone/fixtures/landfall_imminent.json", "r") as f:
        payload = json.load(f)

    response = client.post(
        "/api/v1/cyclone/intelligence",
        json=payload,
        headers={"Authorization": "Bearer totally-invalid-key"}
    )
    assert response.status_code == 401


def test_ingest_early_stage_fixture(client):
    with open("ml/cyclone/fixtures/early_stage.json", "r") as f:
        payload = json.load(f)

    response = client.post(
        "/api/v1/cyclone/intelligence",
        json=payload,
        headers={"Authorization": f"Bearer {SYSTEM_KEY}"}
    )
    assert response.status_code == 202
    assert response.json()["status"] == "accepted"


def test_ingest_no_detect_fixture(client):
    with open("ml/cyclone/fixtures/no_detect.json", "r") as f:
        payload = json.load(f)

    response = client.post(
        "/api/v1/cyclone/intelligence",
        json=payload,
        headers={"Authorization": f"Bearer {SYSTEM_KEY}"}
    )
    assert response.status_code == 202
    assert response.json()["status"] == "accepted"


def test_ingest_amphan_replay_cache_frames(client):
    """Validates that all precomputed replay frames stream cleanly through the API."""
    with open("ml/cyclone/replay/cache/amphan_2020.jsonl", "r") as f:
        frames = [json.loads(line) for line in f if line.strip()]

    assert len(frames) > 0

    for frame in frames:
        response = client.post(
            "/api/v1/cyclone/intelligence",
            json=frame,
            headers={"Authorization": f"Bearer {SYSTEM_KEY}"}
        )
        assert response.status_code == 202

