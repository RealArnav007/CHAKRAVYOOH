
from pydantic import BaseModel, Field


class SosPacket(BaseModel):
    # --- Immutable Region ---
    msg_id: str = Field(..., max_length=64, description="UUID v4 - unique per SOS; DEDUP KEY")
    origin_id: str = Field(..., max_length=64, description="Anonymised victim device ID")
    origin_key_id: str = Field(..., max_length=64, description="ID of the key used to sign")
    created_at: int = Field(..., description="Epoch milliseconds")
    nonce: str = Field(..., max_length=64, description="Random nonce for replay protection")
    lat: float = Field(..., ge=-90.0, le=90.0, description="Latitude coordinate")
    lon: float = Field(..., ge=-180.0, le=180.0, description="Longitude coordinate")
    acc: float = Field(..., ge=0.0, description="GPS accuracy radius (meters)")
    trigger_type: str = Field(..., max_length=50, description="e.g., manual, fall, scream")
    request_type: str = Field(..., max_length=50, description="e.g., medical, rescue, fire")
    severity: str = Field(..., max_length=20, description="info | warn | critical")
    regex_score: int = Field(..., ge=0, le=100, description="0-100")
    local_model_score: int = Field(..., ge=0, le=100, description="0-100")
    confidence: float = Field(..., ge=0.0, le=1.0, description="0.0-1.0")
    payload_enc: str = Field(..., description="Base64 or hex encrypted payload")
    
    # --- Mutable Region ---
    ttl: int = Field(..., ge=0, description="Time To Live (remaining hops)")
    hops: int = Field(..., ge=0, description="Hops traversed so far")
    prev_hop_id: str | None = Field(None, max_length=64, description="ID of the forwarding node")
    
    # --- Auth Region ---
    sig: str = Field(..., description="Ed25519 signature over immutable region")


class IngestRequest(BaseModel):
    packet: SosPacket
    received_at: int = Field(..., description="Epoch milliseconds when gateway received it")


class IngestResponse(BaseModel):
    sos_id: str | None = None
    msg_id: str
    status: str
    priority: str | None = None
    request_id: str
