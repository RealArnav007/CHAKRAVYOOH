"""
Project Pukar — ML Seam Adapter (interface.py)
================================================
Acts as the ONLY integration point between Harshit's ingestion pipeline and Rishabh's ML scorer.

Responsibilities:
  1. Convert SosPacket  → SignedSOSHeader  (field rename + Severity/Category enum coercion)
  2. Wrap decrypted_text: str → DecryptedSOSPayload(text=...)
  3. Run Rishabh's SYNC scorer inside an asyncio thread executor (keeps pipeline non-blocking)
  4. Apply a 15-second hard timeout on the Groq API call
  5. Sanitize LLM output (rationale cap, entity list cap, type enforcement)
  6. Map AIReasoningBreakdown → final ScoringResult with fallback_used + confidence populated
  7. Provide a safe rule-based FallbackScoringResult on any exception or timeout
"""

import asyncio
import logging

from src.ml.contracts import (
    AIReasoningBreakdown,
    Category,
    DecryptedSOSPayload,
    ReasoningBreakdown,  # alias = AIReasoningBreakdown (for pipeline.py compat)
    ScoringResult,
    Severity,
    SignedSOSHeader,
)
from src.ml.scorer import Scorer
from src.sos.validation.validator import SosPacket

logger = logging.getLogger(__name__)

# Module-level scorer instance (initialised once at import time, reused across requests)
_scorer = Scorer()

# Hard limits on LLM output fields stored in DB JSON column
_GROQ_RATIONALE_MAX_LEN = 500
_ENTITIES_MAX_COUNT = 20
_ENTITY_ITEM_MAX_LEN = 100
_RULES_MAX_COUNT = 30
_RULE_ITEM_MAX_LEN = 50

# Groq API hard timeout (seconds) — prevents async event loop stalls
_GROQ_TIMEOUT_SECONDS = 15.0


# ---------------------------------------------------------------------------
# Safe enum coercion helpers
# ---------------------------------------------------------------------------

def _safe_severity(value: str) -> Severity:
    """Coerces a raw string to a Severity enum, defaulting to WARN on unknown values."""
    try:
        return Severity(value.lower())
    except ValueError:
        logger.warning(f"[ML Adapter] Unknown severity value '{value}' — defaulting to WARN")
        return Severity.WARN


def _safe_category(value: str) -> Category:
    """Coerces a raw string to a Category enum, defaulting to OTHER on unknown values."""
    try:
        return Category(value.lower())
    except ValueError:
        logger.warning(f"[ML Adapter] Unknown category value '{value}' — defaulting to OTHER")
        return Category.OTHER


# ---------------------------------------------------------------------------
# LLM output sanitizer — applied BEFORE any DB write
# ---------------------------------------------------------------------------

def _sanitize_reasoning(
    raw: AIReasoningBreakdown,
    confidence: float,
    fallback_used: bool,
) -> AIReasoningBreakdown:
    """
    Enforces hard limits on all LLM-sourced fields before they reach the DB JSON column.
    Prevents prompt-injection overflow, XSS vectors, and memory exhaustion.
    """
    rationale = raw.groq_rationale
    if rationale:
        rationale = rationale[:_GROQ_RATIONALE_MAX_LEN]

    # Type-enforce every item — LLM output can contain non-string values
    entities = [
        str(e)[:_ENTITY_ITEM_MAX_LEN]
        for e in (raw.extracted_entities or [])[:_ENTITIES_MAX_COUNT]
    ]
    rules = [
        str(r)[:_RULE_ITEM_MAX_LEN]
        for r in (raw.matched_rules or [])[:_RULES_MAX_COUNT]
    ]

    return AIReasoningBreakdown(
        regex_contribution=raw.regex_contribution,
        local_model_contribution=raw.local_model_contribution,
        groq_contribution=raw.groq_contribution,
        corroboration_bonus=raw.corroboration_bonus,
        vulnerability_bonus=raw.vulnerability_bonus,
        time_decay_factor=raw.time_decay_factor,
        extracted_entities=entities,
        groq_rationale=rationale,
        matched_rules=rules,
        fallback_used=fallback_used,
        confidence=round(confidence, 4),
    )


# ---------------------------------------------------------------------------
# SosPacket → SignedSOSHeader conversion
# ---------------------------------------------------------------------------

def _packet_to_header(packet: SosPacket) -> SignedSOSHeader:
    """
    Maps SosPacket (backend Pydantic model) → SignedSOSHeader (Rishabh's ML model).
    Applies safe enum coercion so no raw string can propagate into the scorer.
    """
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
# Fallback ScoringResult — returned on timeout or any scoring exception
# ---------------------------------------------------------------------------

def _make_fallback(packet: SosPacket, reason: str) -> ScoringResult:
    """
    Returns a safe, rule-based ScoringResult when the ML scorer fails or times out.
    Priority is computed from on-device scores — no crash, no data loss.
    """
    base = max(packet.regex_score, packet.local_model_score)
    if base > 80 or packet.severity == "critical":
        priority_score, severity_out = 85.0, Severity.CRITICAL
    elif base > 50 or packet.severity == "warn":
        priority_score, severity_out = 55.0, Severity.WARN
    else:
        priority_score, severity_out = 25.0, Severity.INFO

    reasoning = AIReasoningBreakdown(
        regex_contribution=float(packet.regex_score) * 0.40,
        local_model_contribution=float(packet.local_model_score) * 0.40,
        groq_contribution=0.0,
        corroboration_bonus=0.0,
        vulnerability_bonus=0.0,
        time_decay_factor=1.0,
        extracted_entities=[],
        groq_rationale=f"Fallback active: {reason[:200]}",
        matched_rules=[],
        fallback_used=True,
        confidence=packet.confidence,
    )

    return ScoringResult(
        severity=severity_out,
        priority_score=priority_score,
        category=_safe_category(packet.request_type),
        confidence=packet.confidence,
        reasoning=reasoning,
    )


# ---------------------------------------------------------------------------
# Public async entry point — called by pipeline.py
# ---------------------------------------------------------------------------

async def score(
    packet: SosPacket,
    decrypted_text: str,
    corroborating_reports_count: int = 0,
) -> ScoringResult:
    """
    Async adapter entry point.  Called by pipeline.py as:
        score_result = await score(packet, decrypted_text, corroborating_reports_count)

    Internally:
      - Converts packet → SignedSOSHeader
      - Wraps decrypted_text → DecryptedSOSPayload
      - Runs Rishabh's sync scorer in a thread executor (non-blocking)
      - Enforces a 15-second timeout on the Groq API call
      - Sanitizes all LLM output before returning
      - Falls back safely on any failure
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

    loop = asyncio.get_event_loop()

    try:
        raw_result: ScoringResult = await asyncio.wait_for(
            loop.run_in_executor(
                None,
                lambda: _scorer.score(
                    header,
                    payload,
                    corroborating_reports_count=corroborating_reports_count,
                ),
            ),
            timeout=_GROQ_TIMEOUT_SECONDS,
        )

        sanitized_reasoning = _sanitize_reasoning(
            raw=raw_result.reasoning,
            confidence=raw_result.confidence,
            fallback_used=False,
        )

        return ScoringResult(
            severity=raw_result.severity,
            priority_score=raw_result.priority_score,
            category=raw_result.category,
            confidence=raw_result.confidence,
            reasoning=sanitized_reasoning,
        )

    except asyncio.TimeoutError:
        logger.error(
            f"[ML Adapter] Groq scoring timed out after {_GROQ_TIMEOUT_SECONDS}s "
            f"for packet {packet.msg_id} — using rule-based fallback."
        )
        return _make_fallback(packet, f"Groq API timed out after {_GROQ_TIMEOUT_SECONDS}s")

    except Exception as e:
        logger.error(f"[ML Adapter] Scoring failed for packet {packet.msg_id}: {e}")
        return _make_fallback(packet, str(e))
