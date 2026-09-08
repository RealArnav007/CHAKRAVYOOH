import pytest
from fastapi.testclient import TestClient
from src.main import app

def test_cyclone_replay_endpoint():
    client = TestClient(app)
    response = client.post("/api/v1/cyclone/replay/start")
    assert response.status_code == 200
    assert response.json() == {"status": "replay_started", "message": "Demo replay sequence initiated."}
