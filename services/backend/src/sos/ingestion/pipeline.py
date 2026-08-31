import logging
import time
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import SOSReport
from src.incidents.correlation.engine import correlate_incident
from src.keys.registry import get_device_public_keys
from src.ml.interface import score
from src.realtime.connection_manager import manager as ws_manager
from src.realtime.events import RealtimeEvent, RealtimeEventType
from src.security.encryption.x25519_box import decrypt_payload
from src.security.replay.checker import is_packet_expired
from src.security.signatures.ed25519 import verify_packet_signature
from src.sos.deduplication.dedup import is_duplicate_msg
from src.sos.validation.validator import IngestRequest, IngestResponse

logger = logging.getLogger(__name__)

async def process_sos_ingestion(db: AsyncSession, request: IngestRequest, gateway_id: str) -> IngestResponse:
    packet = request.packet
    
    # 1. Replay Check
    if is_packet_expired(packet.created_at):
        logger.warning(f"Packet {packet.msg_id} rejected: EXPIRED/REPLAY")
        raise HTTPException(status_code=410, detail="PACKET_EXPIRED")
        
    # 2. Deduplication Check
    if await is_duplicate_msg(db, packet.msg_id):
        logger.info(f"Packet {packet.msg_id} already processed. Idempotent return.")
        return IngestResponse(
            msg_id=packet.msg_id,
            status="duplicate",
            request_id=f"req-{packet.msg_id}"
        )
        
    # 3. Key Lookup & Signature Verification
    device_key = await get_device_public_keys(db, packet.origin_key_id)
    if not device_key:
        logger.warning(f"Key {packet.origin_key_id} not found for packet {packet.msg_id}")
        raise HTTPException(status_code=401, detail="UNKNOWN_KEY")
        
    if not verify_packet_signature(packet, device_key.ed25519_public_key):
        logger.warning(f"Packet {packet.msg_id} failed Ed25519 signature verification")
        raise HTTPException(status_code=401, detail="BAD_SIGNATURE")
        
    # 4. Decryption
    try:
        decrypted_text = decrypt_payload(packet.payload_enc)
    except Exception as e:
        logger.error(f"Decryption failed for packet {packet.msg_id}: {e}")
        raise HTTPException(status_code=422, detail="DECRYPTION_FAILED")
        
    # 5. ML Scoring & Priority Fusion
    try:
        score_result = await score(packet, decrypted_text)
    except Exception as e:
        logger.error(f"ML Scoring failed for packet {packet.msg_id}: {e}")
        from src.ml.interface import ReasoningBreakdown, ScoringResult
        score_result = ScoringResult(
            priority_score=50,
            severity=packet.severity,
            category=packet.request_type or "unknown",
            reasoning=ReasoningBreakdown(
                regex_score=packet.regex_score,
                local_model_score=packet.local_model_score,
                groq_score=None,
                corroboration_bonus=0,
                location_weight=1.0,
                trend_bonus=0,
                confidence=packet.confidence,
                fallback_used=True,
                rationale=f"Scoring error: {str(e)[:120]}",
            )
        )

    # 6. Persistence (SOSReport)
    packet_dt = datetime.fromtimestamp(packet.created_at / 1000.0, tz=timezone.utc)
    
    report = SOSReport(
        msg_id=packet.msg_id,
        origin_id=packet.origin_id,
        origin_key_id=packet.origin_key_id,
        created_at=packet_dt,
        nonce=packet.nonce,
        lat=packet.lat,
        lon=packet.lon,
        acc=packet.acc,
        trigger_type=packet.trigger_type,
        request_type=packet.request_type,
        severity=packet.severity,
        regex_score=packet.regex_score,
        local_model_score=packet.local_model_score,
        confidence=packet.confidence,
        payload_enc=packet.payload_enc,
        payload_decrypted=decrypted_text,
        priority_score=score_result.priority_score,
        ai_category=score_result.category,
        # .model_dump() converts ReasoningBreakdown → plain dict for SQLAlchemy JSON column
        ai_reasoning=score_result.reasoning.model_dump(),
        gateway_id=gateway_id
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    
    # 7. Incident Correlation
    incident_id = await correlate_incident(db, report)
    report.incident_id = incident_id
    await db.commit()
    
    # 8. WebSocket Broadcast
    event = RealtimeEvent(
        event_type=RealtimeEventType.NEW_SOS,
        payload={
            "sos_id": report.sos_id,
            "incident_id": incident_id,
            "priority": score_result.priority_score,
            "category": score_result.category,
            "lat": report.lat,
            "lon": report.lon
        },
        timestamp=int(time.time() * 1000)
    )
    await ws_manager.broadcast(event)
    
    return IngestResponse(
        sos_id=report.sos_id,
        msg_id=packet.msg_id,
        status="accepted",
        priority=str(score_result.priority_score),
        request_id=str(uuid.uuid4())
    )
