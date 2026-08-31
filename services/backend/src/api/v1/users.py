from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.audit.logger import log_event
from src.auth.rbac import RequireRole, get_current_user
from src.database.models import RoleEnum, User
from src.dependencies import get_db_session
from src.users.service import deactivate_user, get_user_by_id, set_user_role

router = APIRouter()

VALID_ROLES = {r.value for r in RoleEnum}


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    email: str
    role: str
    is_active: bool


class RoleUpdateRequest(BaseModel):
    role: str


@router.get("/", response_model=List[UserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(RequireRole(["SUPER_ADMIN", "COMMANDER"])),
):
    """List all users. Restricted to SUPER_ADMIN and COMMANDER."""
    result = await db.execute(select(User).order_by(User.email))
    return result.scalars().all()


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Returns the current authenticated user's profile."""
    return current_user


@router.patch("/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: str,
    req: RoleUpdateRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(RequireRole(["SUPER_ADMIN"])),
):
    """
    Updates a user's role. SUPER_ADMIN only.
    Emits an audit event on every role change.
    """
    if req.role not in VALID_ROLES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid role '{req.role}'. Valid roles: {sorted(VALID_ROLES)}",
        )

    user = await set_user_role(db, user_id, req.role)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await log_event(
        db,
        action="ROLE_UPDATED",
        actor_id=current_user.user_id,
        details={"target_user_id": user_id, "new_role": req.role},
    )
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate(
    user_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(RequireRole(["SUPER_ADMIN"])),
):
    """
    Soft-deactivates a user (sets is_active=False). SUPER_ADMIN only.
    Does not hard-delete — keeps audit trail intact.
    """
    if user_id == current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot deactivate your own account.",
        )

    user = await deactivate_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await log_event(
        db,
        action="USER_DEACTIVATED",
        actor_id=current_user.user_id,
        details={"target_user_id": user_id},
    )
