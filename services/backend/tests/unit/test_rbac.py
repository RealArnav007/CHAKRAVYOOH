import pytest
from fastapi import HTTPException
from src.auth.rbac import RequireRole
from src.database.models import User

@pytest.mark.asyncio
async def test_require_role_success():
    """Test that a user with the correct role passes."""
    user = User(role="COMMANDER")
    req = RequireRole(["COMMANDER", "RESPONDER"])
    
    # Should return the user
    result = await req(current_user=user)
    assert result == user

@pytest.mark.asyncio
async def test_require_role_super_admin():
    """Test that SUPER_ADMIN overrides allowed roles."""
    user = User(role="SUPER_ADMIN")
    req = RequireRole(["VIEWER"])
    
    result = await req(current_user=user)
    assert result == user

@pytest.mark.asyncio
async def test_require_role_failure():
    """Test that an unauthorized role raises 403 Forbidden."""
    user = User(role="VIEWER")
    req = RequireRole(["COMMANDER"])
    
    with pytest.raises(HTTPException) as exc:
        await req(current_user=user)
        
    assert exc.value.status_code == 403
    assert "Operation not permitted" in exc.value.detail
