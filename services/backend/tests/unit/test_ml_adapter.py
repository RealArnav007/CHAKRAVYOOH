import asyncio
import time
import unittest.mock as mock

import pytest

from src.ml.contracts import Category, ReasoningBreakdown, Severity, ScoringResult
from src.ml.interface import (
    _make_fallback,
    _safe_category,
    _safe_severity,
    _sanitize_reasoning,
    score,
)
from src.sos.validation.validator import SosPacket


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_packet(
    severity: str = "warn",
    regex_score: int = 60,
    local_model_score: int = 55,
    confidence: float = 0.75,
    request_type: str = "rescue",
) -> SosPacket:
    """Builds a minimal valid SosPacket for adapter tests."""
    return SosPacket(
        msg_id="test-msg-001",
        origin_id="device-abc",
        origin_key_id="key-abc",
        created_at=int(time.time() * 1000),
        nonce="deadbeef",
        lat=28.6139,
        lon=77.2090,
        acc=10.0,
        trigger_type="manual",
        request_type=request_type,
        severity=severity,
        regex_score=regex_score,
        local_model_score=local_model_score,
        confidence=confidence,
        payload_enc="aabbcc",
        ttl=5,
        hops=2,
        prev_hop_id=None,
        sig="fakesig",
    )


# ── Test 1 — Happy path: adapter returns a valid ScoringResult ────────────────

@pytest.mark.asyncio
async def test_score_returns_scoring_result():
    """score() must return a ScoringResult with plausible values in Groq-fallback mode."""
    packet = _make_packet()
    result = await score(packet, "People trapped under rubble near sector 12")

    assert isinstance(result, ScoringResult)
    assert 0.0 <= result.priority_score <= 100.0
    assert result.severity in list(Severity)
    assert result.category in list(Category)
    assert 0.0 <= result.confidence <= 1.0
    assert isinstance(result.reasoning.fallback_used, bool)


# ── Test 2 — Timeout: adapter falls back gracefully on Groq stall ─────────────

@pytest.mark.asyncio
async def test_score_fallback_on_groq_timeout():
    """When the executor times out, score() must return a safe fallback — never raise."""
    packet = _make_packet(severity="critical", regex_score=90, local_model_score=88)

    async def _slow_coro():
        await asyncio.sleep(30)  # simulate a hung Groq call

    with mock.patch("src.ml.interface._scorer") as mock_scorer:
        mock_scorer.score.side_effect = lambda *a, **kw: time.sleep(30)
        with mock.patch("src.ml.interface._GROQ_TIMEOUT_SECONDS", 0.1):
            result = await score(packet, "Mayday mayday building collapsed")

    assert isinstance(result, ScoringResult)
    assert result.reasoning.fallback_used is True
    assert "timed out" in (result.reasoning.groq_rationale or "").lower()


# ── Test 3 — Enum coercion: unknown severity string is safely handled ─────────

def test_enum_coercion_invalid_severity():
    """Unknown severity string must coerce to WARN, not raise ValueError."""
    result = _safe_severity("GARBAGE_VALUE_99")
    assert result is Severity.WARN


# ── Test 4 — Enum coercion: unknown category string is safely handled ─────────

def test_enum_coercion_invalid_category():
    """An unexpected request_type from Android must coerce to OTHER, not raise."""
    result = _safe_category("sql_injection'; DROP TABLE sos_reports;--")
    assert result is Category.OTHER


# ── Test 5 — Sanitizer: groq_rationale is capped at 500 chars ────────────────

def test_groq_rationale_truncation():
    """_sanitize_reasoning must truncate a >500-char LLM rationale to exactly 500 chars."""
    long_rationale = "A" * 1000
    # Use model_construct to bypass Pydantic's max_length validator —
    # the sanitizer runs BEFORE the data hits a validated model, so we
    # need to test its truncation on raw (potentially unchecked) input.
    raw = ReasoningBreakdown.model_construct(
        regex_contribution=12.0,
        local_model_contribution=11.0,
        groq_contribution=30.0,
        corroboration_bonus=0.0,
        vulnerability_bonus=0.0,
        time_decay_factor=1.0,
        extracted_entities=[],
        groq_rationale=long_rationale,
        matched_rules=[],
        fallback_used=False,
        confidence=0.9,
    )
    sanitized = _sanitize_reasoning(raw, confidence=0.9, fallback_used=False)
    assert len(sanitized.groq_rationale) == 500


# ── Test 6 — Sanitizer: extracted_entities are capped and type-enforced ───────

def test_entity_list_sanitization():
    """extracted_entities list must be capped at 20 items, each at 100 chars."""
    long_entity = "X" * 200
    many_entities = [long_entity] * 50  # 50 items, each 200 chars

    raw = ReasoningBreakdown(
        regex_contribution=5.0,
        local_model_contribution=5.0,
        groq_contribution=20.0,
        extracted_entities=many_entities,
        fallback_used=False,
        confidence=0.7,
    )
    sanitized = _sanitize_reasoning(raw, confidence=0.7, fallback_used=False)

    assert len(sanitized.extracted_entities) == 20
    assert all(len(e) <= 100 for e in sanitized.extracted_entities)


# ── Test 7 — Fallback: fallback ScoringResult is valid on exception ───────────

def test_make_fallback_on_critical_packet():
    """_make_fallback must produce CRITICAL severity when on-device scores are high."""
    packet = _make_packet(severity="critical", regex_score=92, local_model_score=88)
    result = _make_fallback(packet, "Test forced fallback")

    assert result.severity is Severity.CRITICAL
    assert result.reasoning.fallback_used is True
    assert "Fallback active" in (result.reasoning.groq_rationale or "")
    assert 0.0 <= result.priority_score <= 100.0
