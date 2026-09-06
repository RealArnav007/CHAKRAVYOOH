"""
Project Pukar — ML Seam Adapter (interface.py)
================================================
Acts as the integration bridge between Harshit's ingestion pipeline and Rishabh's ML scorer.

Architecture after ScoreResult v2.0.0:
  - Calls `Scorer.score_async()` directly — no more ThreadPoolExecutor wrapping.
    Rishabh's scorer runs guard/normalize/regex/embed/extract/groq CONCURRENTLY
    via asyncio.to_thread internally, which is faster and cleaner.
  - Sanitizes all mutable LLM output fields before DB storage.
  - Returns ScoreResult directly — pipeline.py reads new fields: escalation_signal,
    false_alarm_likelihood, needs_human_review, injection_suspected, correlation_id.
  - Safe fallback (never raises) on any timeout or exception.
"""

import asyncio
import logging
import uuid

from src.ml.contracts import (
    AIReasoningBreakdown,
    Category,
    DecryptedSOSPayload,
    ReasoningBreakdown,  # alias = AIReasoningBreakdown (re-exported for tests)
    ScoreResult,
    Severity,
    SignedSOSHeader,
)
from src.ml.scorer import Scorer
from src.sos.validation.validator import SosPacket

logger = logging.getLogger(__name__)

# Module-level scorer instance — initialised lazily on first use
_scorer: Scorer | None = None

# Hard limits on LLM output fields stored in DB JSON column
_GROQ_RATIONALE_MAX_LEN = 500
_ENTITIES_MAX_COUNT = 20
_ENTITY_ITEM_MAX_LEN = 100
_RULES_MAX_COUNT = 30
_RULE_ITEM_MAX_LEN = 50

# Per-packet hard scoring deadline — budget_sec passed into score_async
# Rishabh's engine respects this and degrades gracefully, so we add a belt-and-suspenders
# outer timeout slightly longer to catch any unexpected hangs.
_SCORE_BUDGET_MS = 1500.0
_OUTER_TIMEOUT_SECONDS = 20.0


# ---------------------------------------------------------------------------
# Safe enum coercion helpers (None-safe)
# ---------------------------------------------------------------------------

def _safe_severity(value: str | None) -> Severity:
    """Coerces a raw string (or None) to a Severity enum, defaulting to WARN."""
    try:
        return Severity(str(value or "warn").lower())
    except ValueError:
        logger.warning("[ML Adapter] Unknown severity value %r — defaulting to WARN", value)
        return Severity.WARN


def _safe_category(value: str | None) -> Category:
    """Coerces a raw string (or None) to a Category enum, defaulting to OTHER."""
    try:
        return Category(str(value or "other").lower())
    except ValueError:
        logger.warning("[ML Adapter] Unknown category value %r — defaulting to OTHER", value)
        return Category.OTHER


# ---------------------------------------------------------------------------
# LLM output sanitizer — applied BEFORE any DB write
# ---------------------------------------------------------------------------

def _sanitize_reasoning(
    raw: "AIReasoningBreakdown | dict",
    confidence: float,
    fallback_used: bool,
) -> dict:
    """
    Sanitizes all LLM-sourced fields and returns a plain dict safe for the DB JSON column.
    Accepts either a Pydantic AIReasoningBreakdown or a raw dict.

    Security guarantees:
    - groq_rationale capped at 500 chars (prompt-injection / overflow)
    - extracted_entities: max 20 items × 100 chars each
    - matched_rules: max 30 items × 50 chars each
    - explanation_bullets: max 10 items × 200 chars each
    """
    if hasattr(raw, "model_dump"):
        r: dict = raw.model_dump()
    elif isinstance(raw, dict):
        r = dict(raw)
    else:
        r = {}

    rationale = r.get("groq_rationale") or r.get("rationale")
    if rationale:
        rationale = str(rationale)[:_GROQ_RATIONALE_MAX_LEN]
    r["groq_rationale"] = rationale

    r["extracted_entities"] = [
        str(e)[:_ENTITY_ITEM_MAX_LEN]
        for e in (r.get("extracted_entities") or [])[:_ENTITIES_MAX_COUNT]
    ]
    r["matched_rules"] = [
        str(rule)[:_RULE_ITEM_MAX_LEN]
        for rule in (r.get("matched_rules") or [])[:_RULES_MAX_COUNT]
    ]
    r["explanation_bullets"] = [
        str(b)[:200]
        for b in (r.get("explanation_bullets") or [])[:10]
    ]

    # Always overwrite these — authoritative, not LLM output
    r["fallback_used"] = fallback_used
    r["confidence"] = round(float(confidence), 4)

    return r


# ---------------------------------------------------------------------------
# SosPacket → SignedSOSHeader conversion
# ---------------------------------------------------------------------------

def _packet_to_header(packet: SosPacket) -> SignedSOSHeader:
    """Maps SosPacket (backend model) → SignedSOSHeader (Rishabh's ML input contract)."""
    return SignedSOSHeader(
        packet_id=packet.msg_id,
        device_id=packet.origin_id,
        timestamp=packet.created_at,
        hop_count=packet.hops,
        severity=_safe_severity(packet.severity),
        regex_score=packet.regex_score,
        local_model_score=packet.local_model_score,
        confidence=packet.confidence,
        category=_safe_category(packet.request_type),
    )


# ---------------------------------------------------------------------------
# Safe rule-based fallback — never raises
# ---------------------------------------------------------------------------

def _make_fallback(packet: SosPacket, reason: str) -> ScoreResult:
    """
    Returns a safe, rule-based ScoreResult when the ML scorer fails or times out.
    Priority computed from on-device signals — no crash, no data loss.
    """
    base = max(packet.regex_score, packet.local_model_score)
    sev = _safe_severity(packet.severity)

    if base > 80 or sev == Severity.CRITICAL:
        priority_int, severity_out = 85, Severity.CRITICAL
    elif base > 50 or sev == Severity.WARN:
        priority_int, severity_out = 55, Severity.WARN
    else:
        priority_int, severity_out = 25, Severity.INFO

    reasoning: dict = {
        "regex_contribution": float(packet.regex_score) * 0.40,
        "local_model_contribution": float(packet.local_model_score) * 0.40,
        "groq_contribution": 0.0,
        "corroboration_bonus": 0.0,
        "vulnerability_bonus": 0.0,
        "time_decay_factor": 1.0,
        "extracted_entities": [],
        "groq_rationale": f"Fallback active: {reason[:200]}",
        "matched_rules": [],
        "explanation_bullets": [f"Rule-based fallback — {reason[:150]}"],
        "fallback_used": True,
        "confidence": round(packet.confidence, 4),
        "groq": "unavailable — rules-only",
        "disagreement_detected": False,
        "disagreement_reason": None,
    }

    return ScoreResult(
        severity=severity_out,
        priority=priority_int,
        category=_safe_category(packet.request_type),
        confidence=packet.confidence,
        reasoning=reasoning,
        needs_human_review=False,
        injection_suspected=False,
        escalation_signal=0.0,
        false_alarm_likelihood=0.0,
    )


def _get_scorer() -> Scorer:
    """Lazy singleton scorer — avoids loading all ML modules at import time."""
    global _scorer
    if _scorer is None:
        _scorer = Scorer()
    return _scorer


# ---------------------------------------------------------------------------
# Public async entry point — called by pipeline.py
# ---------------------------------------------------------------------------

async def score(
    packet: SosPacket,
    decrypted_text: str,
    corroborating_reports_count: int = 0,
    zone_timestamps: list | None = None,
    candidates: list | None = None,
) -> ScoreResult:
    """
    Async adapter entry point.

    Uses Rishabh's native score_async() which runs guard / normalize / regex /
    embed / groq / extract CONCURRENTLY — significantly faster than the old
    run_in_executor(sync_score) approach.

    New optional params:
      - zone_timestamps: epoch floats of recent SOS arrivals in same zone
        (for trend.py escalation detection). Pass None if not yet integrated.
      - candidates: pgvector candidate dicts [{id, embedding}] for dedup.
        Pass None until pgvector column is wired up.
    """
    header = _packet_to_header(packet)
    payload = DecryptedSOSPayload(
        text=decrypted_text,
        lat=packet.lat,
        lon=packet.lon,
        victim_count=1,
        has_medical_need=False,
        is_trapped=False,
    )

    correlation_id = f"corr_{uuid.uuid4().hex[:12]}"

    try:
        raw_result: ScoreResult = await asyncio.wait_for(
            _get_scorer().score_async(
                packet=header,
                decrypted_text=payload,
                corroborating_reports_count=corroborating_reports_count,
                zone_timestamps=zone_timestamps or [],
                candidates=candidates,
                time_budget_ms=_SCORE_BUDGET_MS,
                correlation_id=correlation_id,
                trigger_type=getattr(packet, "trigger_type", None),
            ),
            timeout=_OUTER_TIMEOUT_SECONDS,
        )

        # Sanitize reasoning dict before DB storage
        sanitized_reasoning = _sanitize_reasoning(
            raw=raw_result.reasoning,
            confidence=raw_result.confidence,
            fallback_used=False,
        )

        # Return a clean ScoreResult — all new v2 fields preserved for pipeline.py
        return ScoreResult(
            severity=raw_result.severity,
            priority=int(raw_result.priority),       # canonical int field
            category=raw_result.category,
            confidence=raw_result.confidence,
            reasoning=sanitized_reasoning,
            # --- v2 dispatch intelligence ---
            entities=raw_result.entities,
            briefing=raw_result.briefing,
            recommended_resources=raw_result.recommended_resources,
            # --- correlation / embedding ---
            correlation=raw_result.correlation,
            embedding=raw_result.embedding,
            # --- zone & false-alarm signals ---
            escalation_signal=raw_result.escalation_signal,
            false_alarm_likelihood=raw_result.false_alarm_likelihood,
            false_alarm_reasons=raw_result.false_alarm_reasons,
            # --- ops & security telemetry ---
            needs_human_review=raw_result.needs_human_review,
            injection_suspected=raw_result.injection_suspected,
            injection_reasons=raw_result.injection_reasons,
            correlation_id=raw_result.correlation_id or correlation_id,
        )

    except asyncio.TimeoutError:
        logger.error(
            "[ML Adapter] Scoring timed out after %.1fs | packet=%s — rule-based fallback",
            _OUTER_TIMEOUT_SECONDS, packet.msg_id,
        )
        return _make_fallback(packet, f"Scoring timed out after {_OUTER_TIMEOUT_SECONDS}s")

    except Exception as e:
        logger.error(
            "[ML Adapter] Scoring failed | packet=%s | error_type=%s | error=%s",
            packet.msg_id, type(e).__name__, str(e)[:200],
        )
        return _make_fallback(packet, str(e))
