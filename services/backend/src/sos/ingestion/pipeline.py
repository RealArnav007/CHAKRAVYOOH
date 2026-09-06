import json
import logging
import time
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy import select as sa_select
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

# Hard limits applied before DB writes
_PAYLOAD_DECRYPTED_MAX_LEN = 10_000   # prevent oversized text column writes
_AI_REASONING_MAX_JSON_BYTES = 50_000  # 50 KB cap on the JSON reasoning blob


async def process_sos_ingestion(db: AsyncSession, request: IngestRequest, gateway_id: str) -> IngestResponse:
    packet = request.packet

    # 1. Replay Check
    if is_packet_expired(packet.created_at):
        logger.warning("Packet %s rejected: EXPIRED/REPLAY", packet.msg_id)
        raise HTTPException(status_code=410, detail="PACKET_EXPIRED")

    # 2. Deduplication Check
    if await is_duplicate_msg(db, packet.msg_id):
        logger.info("Packet %s already processed — idempotent return.", packet.msg_id)
        return IngestResponse(
            msg_id=packet.msg_id,
            status="duplicate",
            request_id=f"req-{packet.msg_id}"
        )

    # 3. Key Lookup & Signature Verification
    device_key = await get_device_public_keys(db, packet.origin_key_id)
    if not device_key:
        logger.warning("Key %s not found for packet %s", packet.origin_key_id, packet.msg_id)
        raise HTTPException(status_code=401, detail="UNKNOWN_KEY")

    if not verify_packet_signature(packet, device_key.ed25519_public_key):
        logger.warning("Packet %s failed Ed25519 signature verification", packet.msg_id)
        raise HTTPException(status_code=401, detail="BAD_SIGNATURE")

    # 4. Decryption
    try:
        decrypted_text = decrypt_payload(packet.payload_enc)
    except Exception as e:
        logger.error("Decryption failed for packet %s: %s", packet.msg_id, type(e).__name__)
        raise HTTPException(status_code=422, detail="DECRYPTION_FAILED")

    # Truncate decrypted text before any storage or LLM use (DoS / column overflow guard)
    if decrypted_text and len(decrypted_text) > _PAYLOAD_DECRYPTED_MAX_LEN:
        logger.warning(
            "Packet %s payload_decrypted truncated (%d → %d chars)",
            packet.msg_id, len(decrypted_text), _PAYLOAD_DECRYPTED_MAX_LEN,
        )
        decrypted_text = decrypted_text[:_PAYLOAD_DECRYPTED_MAX_LEN]

    # 5. ML Scoring & Priority Fusion
    # Count nearby reports in the same cluster (2h window, ~500m radius).
    # The Priority Engine uses this to boost priority of dense incident clusters.
    # Note: current packet is not yet committed — count is already accurate, no adjustment needed.
    cluster_window = datetime.now(timezone.utc) - timedelta(hours=2)
    cluster_radius = 0.005  # ≈ 555m at equator (rough bbox; exact calc inside PriorityEngine)
    corr_count_result = await db.execute(
        sa_select(func.count()).where(
            SOSReport.lat.between(packet.lat - cluster_radius, packet.lat + cluster_radius),
            SOSReport.lon.between(packet.lon - cluster_radius, packet.lon + cluster_radius),
            SOSReport.created_at >= cluster_window,
        )
    )
    corroborating_count = corr_count_result.scalar() or 0  # packet not yet inserted — count is exact

    # score() adapter handles all fallbacks internally — never raises
    score_result = await score(
        packet,
        decrypted_text,
        corroborating_reports_count=corroborating_count,
        zone_timestamps=None,   # TODO: fetch recent zone timestamps for escalation detection
        candidates=None,        # TODO: pass pgvector candidates when pgvector column is wired
    )

    # Normalise reasoning to dict (adapter always returns dict, but guard defensively)
    reasoning: dict = (
        score_result.reasoning
        if isinstance(score_result.reasoning, dict)
        else score_result.reasoning.model_dump()
    )

    # Apply JSON size cap before DB write (50KB hard limit on ai_reasoning column)
    raw_json = json.dumps(reasoning)
    if len(raw_json) > _AI_REASONING_MAX_JSON_BYTES:
        logger.warning(
            "Packet %s ai_reasoning JSON too large (%d bytes) — storing truncated sentinel",
            packet.msg_id, len(raw_json),
        )
        reasoning = {
            "error": "reasoning_overflow",
            "fallback_used": True,
            "confidence": reasoning.get("confidence", 0.0),
        }

    # Security alerts — log before DB write
    if reasoning.get("disagreement_detected"):
        logger.warning(
            "[Security] Score disagreement | packet=%s | reason=%s | policy=%s",
            packet.msg_id,
            reasoning.get("disagreement_reason", "unknown"),
            reasoning.get("disagreement_policy_applied", "none"),
        )
    if score_result.injection_suspected:
        logger.warning(
            "[Security] Prompt injection suspected | packet=%s | reasons=%s",
            packet.msg_id, score_result.injection_reasons,
        )

    # 6. Persistence
    # Use score_result.priority (int 0–100) as the canonical field throughout.
    # priority_score (Float column) stores the same value for backward compat with existing queries.
    packet_dt = datetime.fromtimestamp(packet.created_at / 1000.0, tz=timezone.utc)
    priority_int: int = score_result.priority  # canonical int 0–100

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
        priority_score=float(priority_int),    # Float column — explicit cast from canonical int
        ai_category=str(score_result.category),  # StrEnum → plain string
        ai_reasoning=reasoning,
        # ScoreResult v2.0.0 intelligence fields
        escalation_signal=score_result.escalation_signal,
        false_alarm_likelihood=score_result.false_alarm_likelihood,
        needs_human_review=score_result.needs_human_review,
        injection_suspected=score_result.injection_suspected,
        ai_correlation_id=score_result.correlation_id,
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
    # Includes new v2 intelligence signals for Arnav's UI badges
    event = RealtimeEvent(
        event_type=RealtimeEventType.NEW_SOS,
        payload={
            "sos_id": report.sos_id,
            "incident_id": incident_id,
            "priority": priority_int,                        # int — dispatch queue sorting
            "category": str(score_result.category),          # StrEnum → plain string for JSON
            "lat": report.lat,
            "lon": report.lon,
            # v2 intelligence signals — drives Arnav's incident screen badges
            "needs_human_review": score_result.needs_human_review,
            "injection_suspected": score_result.injection_suspected,
            "false_alarm_likelihood": round(score_result.false_alarm_likelihood, 3),
            "escalation_signal": round(score_result.escalation_signal, 3),
        },
        timestamp=int(time.time() * 1000)
    )
    await ws_manager.broadcast(event)

    return IngestResponse(
        sos_id=report.sos_id,
        msg_id=packet.msg_id,
        status="accepted",
        priority=str(priority_int),   # str("85") not str("85.0")
        request_id=str(uuid.uuid4())
    )
