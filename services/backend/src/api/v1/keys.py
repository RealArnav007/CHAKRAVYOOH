import nacl.encoding
import nacl.public
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.dependencies import get_db_session
from src.keys.registry import register_device_keys

router = APIRouter()

class KeyRegistrationRequest(BaseModel):
    origin_id: str
    origin_key_id: str
    ed25519_public_key: str
    x25519_public_key: str

class KeyRegistrationResponse(BaseModel):
    status: str
    origin_key_id: str

@router.post("/register", response_model=KeyRegistrationResponse)
async def register_keys(
    request: KeyRegistrationRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Registers a device's public keypair during onboarding.
    The `origin_key_id` becomes the trust anchor for verifying SOS packets.
    """
    await register_device_keys(
        db,
        origin_key_id=request.origin_key_id,
        origin_id=request.origin_id,
        ed25519_pub=request.ed25519_public_key,
        x25519_pub=request.x25519_public_key
    )
    return KeyRegistrationResponse(status="registered", origin_key_id=request.origin_key_id)

@router.get("/backend-pubkey")
async def get_backend_pubkey():
    """
    Returns the backend's X25519 public key.
    Android clients use this to encrypt (SealedBox) the SOS payload before transmission.
    """
    settings = get_settings()
    priv_key_hex = settings.BACKEND_X25519_PRIVATE_KEY
    if not priv_key_hex:
        raise HTTPException(status_code=500, detail="Backend encryption key not configured")
        
    private_key = nacl.public.PrivateKey(priv_key_hex, encoder=nacl.encoding.HexEncoder)
    pub_key_hex = private_key.public_key.encode(encoder=nacl.encoding.HexEncoder).decode('utf-8')
    
    return {"backend_x25519_public_key": pub_key_hex}
