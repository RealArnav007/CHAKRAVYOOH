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


class NeedCategory(StrEnum):
    """Specific response needs identified in distress text."""
    RESCUE = "rescue"
    MEDICAL = "medical"
    FIRE = "fire"
    SHELTER = "shelter"
    EVACUATION = "evacuation"


class MobilityStatus(StrEnum):
    """Physical entrapment or mobility state of victims."""
    TRAPPED = "trapped"
    MOBILE = "mobile"
    UNKNOWN = "unknown"


class ResourceCategory(StrEnum):
    """Recommended emergency response resource categories."""
    AMBULANCE = "ambulance"
    RESCUE_TEAM = "rescue_team"
    FIRE_TRUCK = "fire_truck"
    EVACUATION = "evacuation"
    MEDICAL_SUPPLIES = "medical_supplies"


class Briefing(BaseModel):
    """
    Commander incident briefing summary and recommended tactical resources.
    Rendered on Arnav's incident detail screen.
    """
    headline: str = Field(..., description="Actionable <=18 word dispatcher headline summary")
    recommended_resources: list[ResourceCategory] = Field(
        default_factory=list,
        description="Ordered tactical units recommended for dispatch"
    )
    confidence: float = Field(
        default=0.90,
        ge=0.0,
        le=1.0,
        description="Confidence of the briefing synthesis (0.0 to 1.0)"
    )

    def __getitem__(self, item: str) -> Any:
        """Allow dict-like subscript access."""
        if hasattr(self, item):
            return getattr(self, item)
        raise KeyError(item)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary representation."""
        return {
            "headline": self.headline,
            "recommended_resources": [
                r.value if isinstance(r, ResourceCategory) else str(r)
                for r in self.recommended_resources
            ],
            "confidence": self.confidence,
        }


class Entities(BaseModel):
    """
    Structured dispatch-ready intelligence extracted from SOS free-text.
    Headline demo feature for real-time situational awareness.
    """
    people_count: int | None = Field(default=None, ge=0, description="Count of people in distress")
    injuries: list[str] = Field(default_factory=list, description="Specific injuries or medical conditions identified")
    hazards: list[str] = Field(default_factory=list, description="Active hazards (structural_collapse, fire, flood, gas_leak, etc.)")
    needs: list[NeedCategory] = Field(default_factory=list, description="Actionable response needs (rescue, medical, fire, shelter, evacuation)")
    landmarks: list[str] = Field(default_factory=list, description="Geographic or structural reference points mentioned")
    mobility: MobilityStatus = Field(default=MobilityStatus.UNKNOWN, description="Mobility / entrapment status (trapped, mobile, unknown)")
    vulnerable: list[str] = Field(default_factory=list, description="Identified vulnerable populations (child, elderly, disabled, pregnant)")

    def __getitem__(self, item: str) -> Any:
        """Allow dict-like subscript access."""
        if hasattr(self, item):
            return getattr(self, item)
        raise KeyError(item)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary representation."""
        return {
            "people_count": self.people_count,
            "injuries": list(self.injuries),
            "hazards": list(self.hazards),
            "needs": [n.value if isinstance(n, NeedCategory) else str(n) for n in self.needs],
            "landmarks": list(self.landmarks),
            "mobility": self.mobility.value if isinstance(self.mobility, MobilityStatus) else str(self.mobility),
            "vulnerable": list(self.vulnerable),
        }


# Alias for backward compatibility
ExtractedEntities = Entities


class CorrelationVerdict(BaseModel):
    """
    Verdict indicating whether a new report matches an existing incident cluster.
    Returned to Harshit's correlation pipeline.
    """
    match_id: str | None = Field(default=None, description="Matched incident or report ID if duplicate/corroborating")
    similarity: float = Field(default=0.0, ge=0.0, le=1.0, description="Highest cosine similarity score among candidates")
    is_duplicate: bool = Field(default=False, description="True if similarity >= threshold")
    cluster_hint: str | None = Field(default=None, description="Suggested cluster title or category hint")

    def __getitem__(self, item: str) -> Any:
        """Allow dict-like subscript access."""
        if hasattr(self, item):
            return getattr(self, item)
        raise KeyError(item)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary representation."""
        return {
            "match_id": self.match_id,
            "similarity": round(float(self.similarity), 4),
            "is_duplicate": self.is_duplicate,
            "cluster_hint": self.cluster_hint,
        }


class EscalationState(StrEnum):
    """Categorical macro state of zone distress escalation."""
    QUIET = "quiet"
    STEADY = "steady"
    ESCALATING = "escalating"
    SURGING = "surging"
    IGNITED = "ignited"


class EscalationResult(BaseModel):
    """
    Zone escalation assessment from sliding-window report arrival rates.
    Powers the 'zone ignites' dynamic severity escalation in Harshit's zone engine.
    """
    rate_per_min: float = Field(default=0.0, ge=0.0, description="Recent arrival rate (reports per minute)")
    acceleration: float = Field(default=0.0, description="Change in arrival rate comparing recent vs prior baseline window")
    escalation_signal: float = Field(default=0.0, ge=0.0, le=1.0, description="Normalized zone escalation multiplier (0.0 to 1.0)")
    state_hint: str = Field(default="quiet", description="Categorical escalation state (quiet, steady, escalating, surging, ignited)")
    report_count: int = Field(default=0, ge=0, description="Total reports analyzed within observation window")
    recent_count: int = Field(default=0, ge=0, description="Reports in the recent window")
    prior_count: int = Field(default=0, ge=0, description="Reports in the prior baseline window")

    def __getitem__(self, item: str) -> Any:
        """Allow dict-like subscript access."""
        if hasattr(self, item):
            return getattr(self, item)
        raise KeyError(item)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary representation."""
        return {
            "rate_per_min": round(float(self.rate_per_min), 3),
            "acceleration": round(float(self.acceleration), 3),
            "escalation_signal": round(float(self.escalation_signal), 3),
            "state_hint": self.state_hint,
            "report_count": self.report_count,
            "recent_count": self.recent_count,
            "prior_count": self.prior_count,
        }


class FalseAlarmResult(BaseModel):
    """
    Content-based false-alarm and mock drill assessment.
    Complements envelope-level cryptographic signature and mesh rate-limiting checks.
    POLICY: NEVER auto-suppress. Emits likelihood and reasons for commander review.
    """
    false_alarm_likelihood: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Estimated probability that message is a test, drill, or accidental alert (0.0 to 1.0)"
    )
    reasons: list[str] = Field(
        default_factory=list,
        description="Auditable triggers and matched pattern descriptions explaining the score"
    )
    is_likely_drill: bool = Field(
        default=False,
        description="Boolean advisory flag if false_alarm_likelihood >= drill threshold (e.g. 0.65)"
    )

    def __getitem__(self, item: str) -> Any:
        """Allow dict-like subscript access."""
        if hasattr(self, item):
            return getattr(self, item)
        raise KeyError(item)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict representation."""
        return {
            "false_alarm_likelihood": round(float(self.false_alarm_likelihood), 3),
            "reasons": list(self.reasons),
            "is_likely_drill": self.is_likely_drill,
        }


class NormalizedText(BaseModel):
    """
    Normalized multilingual text representation.
    Guarantees original verbatim text is never overwritten.
    """
    original: str = Field(..., description="Verbatim original distress message text")
    canonical_en: str = Field(..., description="Canonical English working copy for internal ML triage")
    language: Language = Field(default=Language.EN, description="Detected or inferred language (en | hi | hinglish)")

    def __getitem__(self, item: str) -> Any:
        """Allow dict-like access: result['original'], result['canonical_en'], result['language']"""
        if hasattr(self, item):
            return getattr(self, item)
        raise KeyError(item)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict representation."""
        return {
            "original": self.original,
            "canonical_en": self.canonical_en,
            "language": self.language.value if isinstance(self.language, Language) else str(self.language),
        }


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
    """
    regex_contribution: float = Field(..., description="Weighted contribution from regex rules")
    local_model_contribution: float = Field(..., description="Weighted contribution from on-device TFLite")
    groq_contribution: float = Field(..., description="Weighted contribution from cloud LLM")
    corroboration_bonus: float = Field(0.0, description="Bonus added from nearby corroborating SOS packets")
    vulnerability_bonus: float = Field(0.0, description="Bonus from identified high-risk victims (infants, elderly)")
    time_decay_factor: float = Field(1.0, description="Multiplier based on elapsed time")
    extracted_entities: list[str] = Field(default_factory=list, description="Extracted disaster entities")
    groq_rationale: str | None = Field(None, description="Human-readable explanation from Groq Llama-3")
    matched_rules: list[str] = Field(default_factory=list, description="List of matched regex rule IDs")

    # Ingested origin features (re-verified server-side)
    origin_severity: str | None = Field(None, description="Origin packet reported severity")
    origin_regex_score: int | None = Field(None, description="Origin packet reported regex score")
    origin_local_model_score: int | None = Field(None, description="Origin packet reported local model score")
    origin_confidence: float | None = Field(None, description="Origin packet reported confidence")
    origin_category: str | None = Field(None, description="Origin packet reported category")
    server_regex_score: int | None = Field(None, description="Server recomputed regex score from decrypted text")

    # Disagreement detection & Life-Safety Policy Resolution
    disagreement_detected: bool = Field(False, description="Flag indicating significant score disparity among triage sources")
    disagreement_reason: str | None = Field(None, description="Diagnostic explanation if disagreement is detected")
    disagreement_policy_applied: str | None = Field(None, description="Explicit life-safety policy applied on signal conflict (e.g. SAFER_SIDE_ESCALATION)")

    # Confidence-Aware Fusion & Human Review Abstention (Arnav's UI Badge)
    needs_human_review: bool = Field(False, description="Abstention flag when aggregate confidence is low or unresolved signal conflict exists")
    abstention_reason: str | None = Field(None, description="Human-readable reason when human triage verification is required")
    source_confidences: dict[str, float] = Field(default_factory=dict, description="Dynamic per-source confidence weights used during fusion")

    # Groq status & resilience fallback indicator
    groq: str | None = Field(None, description="Groq execution status (e.g. 'unavailable — rules-only' or 'active')")

    # Spatial & Temporal incident layer factor breakdown (Harshit's correlation layer)
    location_modifier: float = Field(0.0, description="Spatial hazard / floodplain risk bonus or penalty")
    trend_modifier: float = Field(0.0, description="Temporal surge / cluster acceleration bonus")
    per_report_severity: str | None = Field(None, description="Per-report standalone assessed severity (distinct from cluster incident priority)")
    incident_priority: int | None = Field(None, description="Fused cluster incident operational dispatch priority (0-100)")

    # Prompt injection guard detection telemetry
    injection_suspected: bool = Field(False, description="Flag indicating potential prompt injection or adversarial text detected in SOS payload")
    injection_reasons: list[str] = Field(default_factory=list, description="List of detected prompt injection pattern categories or signatures")

    # Content-based false alarm & mock drill detection
    false_alarm_likelihood: float = Field(0.0, ge=0.0, le=1.0, description="Estimated false-alarm / drill probability")
    false_alarm_reasons: list[str] = Field(default_factory=list, description="Reasons flagged for potential false alarm")

    # Human-readable incident screen explanation bullets for Arnav's UI
    explanation_bullets: list[str] = Field(default_factory=list, description="Human-readable 'Why is this critical?' bullet points for Arnav's incident screen")
    factors: dict[str, Any] = Field(default_factory=dict, description="Consolidated per-factor numerical contribution summary")



class ScoreResult(BaseModel):
    """
    Unified, versioned public scoring contract returned to Harshit's ingestion pipeline.
    Combines on-device telemetry, deterministic rules, cloud Groq triage, entity extraction,
    incident correlation, zone escalation, false-alarm analysis, and briefing synthesis.
    """
    # Schema Versioning (SemVer)
    schema_version: str = Field(default="2.0.0", description="Semantic contract version for backend & frontend backwards compatibility")

    # Baseline Core Triage (Immutable Seam)
    severity: Severity = Field(..., description="Final resolved severity tier (info | warn | critical)")
    priority: int = Field(..., ge=0, le=100, description="Calibrated integer priority score (0 to 100)")
    category: Category = Field(..., description="Resolved emergency category (rescue | medical | fire | shelter | other)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Aggregated confidence score (0.0 to 1.0)")
    reasoning: dict[str, Any] = Field(default_factory=dict, description="Auditable multi-factor reasoning breakdown")

    # Dispatch Intelligence & Tactical Briefing (Arnav's UI)
    entities: Entities | None = Field(default=None, description="Structured dispatch intelligence extracted from distress text")
    briefing: Briefing | None = Field(default=None, description="Tactical dispatcher briefing headline and recommended resources")
    recommended_resources: list[ResourceCategory] = Field(
        default_factory=list,
        description="Derived tactical units for immediate dispatch (ambulance, rescue_team, fire_truck, evacuation, medical_supplies)"
    )

    # Incident Semantic Correlation & Deduplication (Harshit's pgvector Seam)
    correlation: CorrelationVerdict | None = Field(
        default=None,
        description="Semantic correlation verdict matching nearby incident candidates (match_id, similarity, is_duplicate, cluster_hint)"
    )
    embedding: list[float] | None = Field(
        default=None,
        description="Normalized 384-dimensional dense semantic vector for PostgreSQL pgvector storage"
    )

    # Zone Escalation & Content False-Alarm Analysis
    escalation_signal: float = Field(default=0.0, ge=0.0, le=1.0, description="Zone distress escalation intensity multiplier (0.0 to 1.0)")
    false_alarm_likelihood: float = Field(default=0.0, ge=0.0, le=1.0, description="Estimated probability of false alarm / test drill (0.0 to 1.0)")
    false_alarm_reasons: list[str] = Field(default_factory=list, description="Triggers flagged for false alarm / drill")

    # Operational Safety & Security Telemetry
    needs_human_review: bool = Field(default=False, description="Commander review flag displayed as a badge on Arnav's incident screen")
    injection_suspected: bool = Field(default=False, description="Flag indicating potential prompt injection or adversarial text detected in SOS payload")
    injection_reasons: list[str] = Field(default_factory=list, description="Triggers flagged for prompt injection")
    correlation_id: str | None = Field(default=None, description="Unique trace correlation ID for end-to-end report observability")

    @property
    def priority_score(self) -> float:
        """Alias for backward compatibility."""
        return float(self.priority)


class GroqTriageResult(BaseModel):
    """
    Structured semantic triage response from the Groq online teacher.
    """
    severity: Severity = Field(..., description="Resolved severity tier (info | warn | critical)")
    category: Category = Field(..., description="Resolved emergency domain (rescue | medical | fire | shelter | other)")
    urgency: int = Field(..., ge=1, le=5, description="Calibrated urgency tier (1 to 5)")
    entities: list[str] = Field(default_factory=list, description="Extracted disaster entities")
    rationale: str = Field(..., description="Actionable operational dispatcher rationale")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model prediction confidence score (0.0 to 1.0)")
    injection_suspected: bool = Field(False, description="Flag indicating potential prompt injection detected in distress text")
    injection_reasons: list[str] = Field(default_factory=list, description="List of detected injection pattern categories")

    @field_validator("urgency")
    @classmethod
    def validate_urgency(cls, v: int) -> int:
        if not (1 <= v <= 5):
            raise ValueError(f"Urgency must be between 1 and 5, got {v}")
        return int(v)

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {v}")
        return round(float(v), 4)

    @property
    def urgency_score(self) -> int:
        """Translates 1-5 integer urgency into 0-100 scale for priority engine fusion."""
        mapping = {1: 20, 2: 40, 3: 60, 4: 80, 5: 100}
        return mapping.get(self.urgency, min(100, max(0, self.urgency * 20)))


# Aliases for backward compatibility
ScoringResult = ScoreResult
ReasoningBreakdown = AIReasoningBreakdown  # test_ml_adapter + interface.py import this
