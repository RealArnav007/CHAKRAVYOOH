import logging

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import DeviceKey

logger = logging.getLogger(__name__)

async def get_device_public_keys(db: AsyncSession, origin_key_id: str) -> DeviceKey | None:
    """
    Retrieves the Ed25519 and X25519 public keys registered for a given origin_key_id.
    """
    stmt = select(DeviceKey).where(DeviceKey.origin_key_id == origin_key_id).limit(1)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def register_device_keys(
    db: AsyncSession, origin_key_id: str, origin_id: str, ed25519_pub: str, x25519_pub: str
) -> DeviceKey:
    """
    Registers a new device keypair identity.
    Returns 409 Conflict if the key ID already exists.
    """
    new_key = DeviceKey(
        origin_key_id=origin_key_id,
        origin_id=origin_id,
        ed25519_public_key=ed25519_pub,
        x25519_public_key=x25519_pub
    )
    db.add(new_key)
    try:
        await db.commit()
        await db.refresh(new_key)
        return new_key
    except IntegrityError:
        await db.rollback()
        logger.warning(f"Key registration collision for origin_key_id={origin_key_id}")
        raise HTTPException(status_code=409, detail="KEY_ALREADY_REGISTERED")
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to register device keys: {e}")
        raise HTTPException(status_code=500, detail="INTERNAL_ERROR")
