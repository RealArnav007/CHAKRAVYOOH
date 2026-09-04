"""
Project Pukar - ML Intelligence Contracts & Shared Schemas
SINGLE SOURCE OF TRUTH for severity and classification outputs.

These fields ride INSIDE the cryptographically signed region of the emergency mesh packet.
Field names, types, and constraints are frozen across:
- Android On-Device Engine (Arnav)
- Cloud Backend Ingestion (Harshit)
- ML Intelligence Pipelines (Rishabh)
"""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class Severity(StrEnum):
    """Frozen severity tiers for tactical dispatch and mesh triage."""
    INFO = "info"
    WARN = "warn"
    CRITICAL = "critical"


# Backwards compatibility alias
SeverityLevel = Severity


class Category(StrEnum):
    """Frozen emergency classification categories."""
    RESCUE = "rescue"
    MEDICAL = "medical"
    FIRE = "fire"
    SHELTER = "shelter"
    OTHER = "other"


# Backwards compatibility alias
EmergencyCategory = Category


class Language(StrEnum):
    """Supported crisis message languages."""
    EN = "en"
    HI = "hi"
    HINGLISH = "hinglish"


class SeverityAssessment(BaseModel):
    """
    On-device ML & Rule scoring assessment.
    Embedded directly into the signed immutable packet header at origin.
    """
    severity: Severity = Field(
        ...,
        description="Assessed severity level (info | warn | critical)"
    )
    regex_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Deterministic regex rule score (0 to 100)"
    )
    local_model_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="On-device TFLite model severity score (0 to 100)"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Model prediction confidence score (0.0 to 1.0)"
    )
    category: Category = Field(
        ...,
        description="Categorized emergency domain (rescue | medical | fire | shelter | other)"
    )
    language: Language = Field(
        default=Language.EN,
        description="Detected/inferred language (en | hi | hinglish)"
    )

    @field_validator("regex_score", "local_model_score")
    @classmethod
    def validate_scores(cls, v: int) -> int:
        if not (0 <= v <= 100):
            raise ValueError(f"Score must be an integer between 0 and 100, got {v}")
        return v

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError(f"Confidence must be a float between 0.0 and 1.0, got {v}")
        return round(float(v), 4)


class SignedSOSHeader(BaseModel):
    """
    Rides inside the signed immutable header created on the origin phone.
    Guaranteed tamper-proof by ECDSA / Ed25519 signature.
    """
    packet_id: str | None = Field(None, description="Unique packet identifier (UUID or hex)")
    device_id: str | None = Field(None, description="Hashed ID of originating phone")
    timestamp: int | None = Field(None, description="Unix timestamp (milliseconds) at origin")
    hop_count: int = Field(0, description="Number of mesh relay hops traversed")

    # Embedded severity assessment fields
    severity: Severity = Field(Severity.WARN, description="On-device assessed severity")
    regex_score: int = Field(ge=0, le=100, default=0, description="On-device regex rule score (0-100)")
    local_model_score: int = Field(ge=0, le=100, default=0, description="On-device TFLite model score (0-100)")
    confidence: float = Field(ge=0.0, le=1.0, default=0.5, description="Model confidence score")
    category: Category = Field(Category.OTHER, description="On-device categorized emergency")
    language: Language = Field(Language.EN, description="Inferred message language")

    def to_assessment(self) -> SeverityAssessment:
        """Converts header fields into a validated SeverityAssessment."""
        return SeverityAssessment(
            severity=self.severity,
            regex_score=self.regex_score,
            local_model_score=self.local_model_score,
            confidence=self.confidence,
            category=self.category,
            language=self.language,
        )


class DecryptedSOSPayload(BaseModel):
    """
    Decrypted SOS message contents, only visible to origin phone and cloud backend.
    """
    text: str = Field(..., description="Raw distress message text (multilingual)")
    lat: float | None = Field(None, description="Latitude from GPS or last known fix")
    lon: float | None = Field(None, description="Longitude from GPS or last known fix")
    sender_name: str | None = Field(None, description="Optional victim name or contact")
    victim_count: int | None = Field(1, description="Estimated count of people in distress")
    has_medical_need: bool = Field(False, description="Flag for medical triage requirement")
    is_trapped: bool = Field(False, description="Flag indicating physical entrapment")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional client telemetry")


class AIReasoningBreakdown(BaseModel):
    """
    Per-factor transparency breakdown rendered on the incident dispatch UI.
    v2: Adds fallback_used + confidence for backend monitoring and UI degraded-mode badge.
    """
    regex_contribution: float = Field(..., description="Weighted contribution from regex rules")
    local_model_contribution: float = Field(..., description="Weighted contribution from on-device TFLite")
    groq_contribution: float = Field(..., description="Weighted contribution from cloud LLM")
    corroboration_bonus: float = Field(0.0, description="Bonus added from nearby corroborating SOS packets")
    vulnerability_bonus: float = Field(0.0, description="Bonus from identified high-risk victims (infants, elderly)")
    time_decay_factor: float = Field(1.0, description="Multiplier based on elapsed time")
    extracted_entities: list[str] = Field(default_factory=list, description="Extracted disaster entities")
    groq_rationale: str | None = Field(
        None,
        max_length=500,  # Hard cap — prevents prompt-injection overflow in the DB JSON column
        description="Human-readable explanation from Groq Llama-3 (max 500 chars)"
    )
    matched_rules: list[str] = Field(default_factory=list, description="List of matched regex rule IDs")
    # Operational metadata (added by Harshit's adapter, not set by Rishabh's PriorityEngine)
    fallback_used: bool = Field(False, description="True when Groq was unavailable and rule-based fallback was used")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Aggregated model confidence score")


# Backwards compatibility alias — pipeline.py imports ReasoningBreakdown
ReasoningBreakdown = AIReasoningBreakdown


class ScoringResult(BaseModel):
    """
    Unified scoring response returned by scorer.score() to Harshit's backend pipeline.
    """
    severity: Severity = Field(..., description="Final resolved severity tier (info | warn | critical)")
    priority_score: float = Field(ge=0.0, le=100.0, description="Final normalized priority score (0.0 - 100.0)")
    category: Category = Field(..., description="Resolved emergency category")
    confidence: float = Field(ge=0.0, le=1.0, description="Aggregated confidence")
    reasoning: AIReasoningBreakdown = Field(..., description="Auditable reasoning breakdown")
