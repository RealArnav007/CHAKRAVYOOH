import pytest
from src.database.models import User
from sqlalchemy import select

@pytest.mark.asyncio
async def test_otp_auth_workflow(async_client, async_db):
    """
    Tests the complete Auth workflow:
    1. Request OTP (auto-creates User)
    2. Verify OTP (generates JWT)
    3. Use JWT to access protected route (e.g., incidents list)
    """
    # 1. Request OTP
    resp = await async_client.post("/api/v1/auth/otp/request", json={"email": "test@example.com"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "otp_sent"
    
    # We use MOCK_OTP = True in conftest, so it just returns. 
    # But wait, OTP generation is internal. We need to extract the OTP from the in-memory store.
    from src.auth.otp import _otp_store
    assert "test@example.com" in _otp_store
    otp_code, _ = _otp_store["test@example.com"]
    
    # 2. Verify OTP
    resp2 = await async_client.post("/api/v1/auth/otp/verify", json={"email": "test@example.com", "code": otp_code})
    assert resp2.status_code == 200
    data = resp2.json()
    assert "access_token" in data
    assert data["role"] == "VIEWER"
    
    token = data["access_token"]
    
    # 3. Access protected route (GET /api/v1/incidents/)
    headers = {"Authorization": f"Bearer {token}"}
    resp3 = await async_client.get("/api/v1/incidents/", headers=headers)
    assert resp3.status_code == 200
    assert isinstance(resp3.json(), list)
