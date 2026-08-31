from typing import Any

from pydantic import BaseModel

from src.sos.validation.validator import SosPacket


class ReasoningBreakdown(BaseModel):
    """
    Per-factor AI transparency payload — rendered on the incident detail screen.
    Matches §7 of the Master PRD: 'Regex 88 · Groq 94 · Corroboration +8 · Location +3 · Trend +2'
    """
    regex_score: int
    local_model_score: int
    groq_score: int | None
    corroboration_bonus: int
    location_weight: float
    trend_bonus: int
    confidence: float
    fallback_used: bool
    rationale: str


class ScoringResult(BaseModel):
    priority_score: int
    severity: str
    category: str
    reasoning: ReasoningBreakdown


async def score(packet: SosPacket, decrypted_payload: str) -> ScoringResult:
    """
    Rishabh's ML Seam Interface.
    Fuses Regex + Local Model + Groq AI outputs to determine the authoritative operational priority.
    Currently returns a deterministically calculated fallback based on the on-device scores.
    Groq integration is pending (Phase 9 — Rishabh).
    """
    base_score = max(packet.regex_score, packet.local_model_score)

    if base_score > 80 or packet.severity == "critical":
        priority_score = 90
        severity_out = "critical"
    elif base_score > 50 or packet.severity == "warn":
        priority_score = 60
        severity_out = "high"
    else:
        priority_score = 30
        severity_out = "medium"

    category_out = packet.request_type if packet.request_type else "other"

    reasoning = ReasoningBreakdown(
        regex_score=packet.regex_score,
        local_model_score=packet.local_model_score,
        groq_score=None,          # Populated when Groq is live (Phase 9)
        corroboration_bonus=0,    # Populated by incident correlation engine (Phase 10)
        location_weight=1.0,
        trend_bonus=0,
        confidence=packet.confidence,
        fallback_used=True,
        rationale="Groq integration pending (Phase 9). Used deterministic fallback based on on-device scores.",
    )

    return ScoringResult(
        priority_score=priority_score,
        severity=severity_out,
        category=category_out,
        reasoning=reasoning,
    )
