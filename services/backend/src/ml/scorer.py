"""
Project Pukar - Master Scorer Interface
Exposes the score(packet, decrypted_payload) entry point called by Harshit's backend ingestion pipeline.
"""

from typing import Any

from .contracts import (
    DecryptedSOSPayload,
    ScoringResult,
    SignedSOSHeader,
)
from .groq_client import GroqClient
from .priority_engine import PriorityEngine
from .regex_engine import RegexEngine


class Scorer:
    def __init__(
        self,
        regex_engine: RegexEngine | None = None,
        groq_client: GroqClient | None = None,
        priority_engine: PriorityEngine | None = None,
    ):
        self.regex_engine = regex_engine or RegexEngine()
        self.groq_client = groq_client or GroqClient()
        self.priority_engine = priority_engine or PriorityEngine()

    def score(
        self,
        packet: SignedSOSHeader | dict[str, Any],
        decrypted_payload: DecryptedSOSPayload | dict[str, Any],
        corroborating_reports_count: int = 0,
        hours_elapsed: float = 0.0,
    ) -> ScoringResult:
        """
        Unified scoring entry point for Project Pukar backend.
        
        Args:
            packet: The signed immutable header from the origin phone.
            decrypted_payload: The decrypted emergency message text and metadata.
            corroborating_reports_count: Count of nearby reports in the same cluster.
            hours_elapsed: Time elapsed since original message generation.
            
        Returns:
            ScoringResult containing final severity, priority_score (0-100), category, confidence,
            and auditable AI transparency breakdown.
        """
        # Coerce dict inputs to pydantic models if necessary
        if isinstance(packet, dict):
            header = SignedSOSHeader(**packet)
        else:
            header = packet

        if isinstance(decrypted_payload, dict):
            payload = DecryptedSOSPayload(**decrypted_payload)
        else:
            payload = decrypted_payload

        # 1. Evaluate deterministic regex rules on decrypted text
        regex_eval = self.regex_engine.evaluate(payload.text)

        # 2. Evaluate Groq LLM semantic triage (with graceful fallback)
        groq_eval = self.groq_client.analyze_message(payload.text)

        # 3. Fuse multi-factor signals in PriorityEngine
        fusion = self.priority_engine.calculate_priority(
            header=header,
            payload=payload,
            regex_eval=regex_eval,
            groq_eval=groq_eval,
            corroborating_reports_count=corroborating_reports_count,
            hours_elapsed=hours_elapsed,
        )

        return ScoringResult(
            severity=fusion["severity"],
            priority_score=fusion["priority_score"],
            category=fusion["category"],
            confidence=fusion["confidence"],
            reasoning=fusion["reasoning"],
        )


# Global default instance for convenience
_default_scorer = Scorer()


def score(
    packet: SignedSOSHeader | dict[str, Any],
    decrypted_payload: DecryptedSOSPayload | dict[str, Any],
    **kwargs: Any,
) -> ScoringResult:
    """
    Convenience function matching the interface contract:
    score(packet, decrypted_payload) -> ScoringResult
    """
    return _default_scorer.score(packet, decrypted_payload, **kwargs)
