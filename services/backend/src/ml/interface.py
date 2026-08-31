from typing import Any

from pydantic import BaseModel

from src.sos.validation.validator import SosPacket


class ScoringResult(BaseModel):
    priority_score: int
    severity: str
    category: str
    reasoning: dict[str, Any]

async def score(packet: SosPacket, decrypted_payload: str) -> ScoringResult:
    """
    Rishabh's ML Seam Interface.
    Fuses Regex + Local Model + Groq AI outputs to determine the authoritative operational priority.
    Currently returns a deterministically calculated mock response based on the on-device scores,
    acting as the fallback if Groq is unavailable.
    """
    # Base calculation using local model and regex
    base_score = max(packet.regex_score, packet.local_model_score)
    
    # Simple fallback heuristic
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
    
    return ScoringResult(
        priority_score=priority_score,
        severity=severity_out,
        category=category_out,
        reasoning={
            "regex_score": packet.regex_score,
            "local_model_score": packet.local_model_score,
            "confidence": packet.confidence,
            "fallback_used": True,
            "rationale": "Groq integration pending. Used deterministic fallback based on local scores."
        }
    )
