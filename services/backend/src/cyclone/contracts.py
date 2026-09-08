from datetime import datetime
from typing import Any, List, Literal, Optional
from pydantic import BaseModel, Field

# ─────────────────────────────────────────────────────────────────────────────
# Coordinate & Trajectory Models
# ─────────────────────────────────────────────────────────────────────────────

class CyclonePosition(BaseModel):
    lat: float
    lon: float

class CycloneIdentification(BaseModel):
    detected: bool
    confidence: float = Field(ge=0.0, le=1.0)

class CycloneClassification(BaseModel):
    stage: str
    confidence: float = Field(ge=0.0, le=1.0)

class CycloneIntensity(BaseModel):
    level: str
    scale: str
    max_wind_kt: float
    min_pressure_mb: float
    confidence: float = Field(ge=0.0, le=1.0)

class PredictedPathPoint(BaseModel):
    t_plus_h: int
    lat: float
    lon: float

class CycloneUncertainty(BaseModel):
    cone_radius_km: List[float]

class CyclonePrediction(BaseModel):
    current_position: CyclonePosition
    heading_deg: float
    speed_kt: float
    forecast_hours: int
    predicted_path: List[PredictedPathPoint]
    confidence: float = Field(ge=0.0, le=1.0)
    uncertainty: CycloneUncertainty

# ─────────────────────────────────────────────────────────────────────────────
# Master PRD §17 — Freshness Metadata
# ─────────────────────────────────────────────────────────────────────────────

class CycloneFreshness(BaseModel):
    """Temporal validity window for intelligence data. Prevents stale predictions driving alerts."""
    generated_at: datetime
    valid_until: Optional[datetime] = None

# ─────────────────────────────────────────────────────────────────────────────
# Master Frozen CycloneIntelligence Contract (§17)
# Compatible with Rishabh's ML schema (tier, name required, freshness)
# ─────────────────────────────────────────────────────────────────────────────

class CycloneIntelligence(BaseModel):
    schema_version: str = "1.0"
    cyclone_id: str
    name: str = "Unknown"                          # Required by Rishabh's ML schema (min_length=1)
    timestamp: datetime
    basin: str

    identification: CycloneIdentification
    classification: Optional[CycloneClassification] = None
    intensity: Optional[CycloneIntensity] = None
    prediction: Optional[CyclonePrediction] = None

    sources: List[str] = Field(default_factory=list)
    model_version: str = "Chakravyooh-brain-0.1"

    # Master PRD §17 — Engine execution tier (matches Rishabh's ML schema)
    tier: Literal["tier1", "tier0", "mixed"] = "tier1"

    # Master PRD §17 — Freshness metadata (optional, provided by Rishabh's ML output)
    freshness: Optional[CycloneFreshness] = None

    extra: dict[str, Any] = Field(default_factory=dict)

# ─────────────────────────────────────────────────────────────────────────────
# Risk Engine Output Contract
# ─────────────────────────────────────────────────────────────────────────────

class ZoneRiskSnapshot(BaseModel):
    zone_id: str
    name: str
    risk: str
    score: float
    eta_hours: Optional[float] = None

