"""Pydantic v2 data models implementing the frozen CycloneIntelligence contract."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
import json
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

try:
    import jsonschema
except ImportError:
    jsonschema = None


# -----------------------------------------------------------------------------
# Controlled Vocabularies / Enums
# -----------------------------------------------------------------------------


class StageEnum(str, Enum):
    """Meteorological life-cycle development stage."""

    NO_SIGNIFICANT_SYSTEM = "NO_SIGNIFICANT_SYSTEM"
    DEVELOPING_DISTURBANCE = "DEVELOPING_DISTURBANCE"
    TROPICAL_DEPRESSION = "TROPICAL_DEPRESSION"
    MATURE_TROPICAL_CYCLONE = "MATURE_TROPICAL_CYCLONE"
    WEAKENING_SYSTEM = "WEAKENING_SYSTEM"
    POST_TROPICAL_REMNANT = "POST_TROPICAL_REMNANT"


class IntensityLevelEnum(str, Enum):
    """IMD basin intensity categorization."""

    DEPRESSION = "DEPRESSION"
    DEEP_DEPRESSION = "DEEP_DEPRESSION"
    CYCLONIC_STORM = "CYCLONIC_STORM"
    SEVERE_CYCLONIC_STORM = "SEVERE_CYCLONIC_STORM"
    VERY_SEVERE_CYCLONIC_STORM = "VERY_SEVERE_CYCLONIC_STORM"
    EXTREMELY_SEVERE_CYCLONIC_STORM = "EXTREMELY_SEVERE_CYCLONIC_STORM"
    SUPER_CYCLONIC_STORM = "SUPER_CYCLONIC_STORM"


class TierEnum(str, Enum):
    """Engine execution tier."""

    TIER1 = "tier1"
    TIER0 = "tier0"
    MIXED = "mixed"


# -----------------------------------------------------------------------------
# Coordinate & Trajectory Models
# -----------------------------------------------------------------------------


class GeoPoint(BaseModel):
    """Geographic coordinate point in WGS84 decimal degrees."""

    model_config = ConfigDict(extra="forbid")

    lat: float = Field(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees [-90, 90]")
    lon: float = Field(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees [-180, 180]")

    @field_validator("lat", "lon")
    @classmethod
    def round_coords(cls, v: float) -> float:
        return round(v, 4)


class TrajectoryPoint(BaseModel):
    """Forecast trajectory step with forward offset."""

    model_config = ConfigDict(extra="forbid")

    t_plus_h: int = Field(..., ge=0, description="Forecast horizon offset in hours (e.g. 0, 6, 12, 24)")
    lat: float = Field(..., ge=-90.0, le=90.0, description="Forecast latitude")
    lon: float = Field(..., ge=-180.0, le=180.0, description="Forecast longitude")

    @field_validator("lat", "lon")
    @classmethod
    def round_coords(cls, v: float) -> float:
        return round(v, 4)


class UncertaintyCone(BaseModel):
    """Spatial uncertainty cone radii."""

    model_config = ConfigDict(extra="forbid")

    cone_radius_km: List[float] = Field(
        ...,
        min_length=1,
        description="Uncertainty cone radii in km, parallel to predicted_path entries.",
    )

    @field_validator("cone_radius_km")
    @classmethod
    def validate_radii(cls, v: List[float]) -> List[float]:
        for r in v:
            if r < 0:
                raise ValueError(f"Cone radius must be non-negative, got {r}")
        if len(v) > 0 and v[0] != 0.0:
            raise ValueError(f"Cone radius at index 0 (current position) must be 0.0, got {v[0]}")
        return [round(r, 2) for r in v]


class PredictionPayload(BaseModel):
    """Trajectory forecast and uncertainty cone."""

    model_config = ConfigDict(extra="forbid")

    current_position: GeoPoint = Field(..., description="Current observed storm center coordinates")
    heading_deg: float = Field(..., ge=0.0, le=360.0, description="Forward motion heading [0, 360]")
    speed_kt: float = Field(..., ge=0.0, description="Forward translation speed in knots")
    forecast_hours: int = Field(..., ge=0, description="Forecast horizon duration in hours")
    predicted_path: List[TrajectoryPoint] = Field(..., min_length=1, description="Time-ordered forecast points")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Trajectory forecast confidence in [0, 1]")
    uncertainty: UncertaintyCone = Field(..., description="Uncertainty cone parallel to path")

    @model_validator(mode="after")
    def validate_path_and_cone(self) -> PredictionPayload:
        # Invariant 1: Path must have at least 1 point and start at t_plus_h == 0
        if not self.predicted_path:
            raise ValueError("predicted_path must not be empty")
        if self.predicted_path[0].t_plus_h != 0:
            raise ValueError(
                f"predicted_path[0].t_plus_h must be 0, got {self.predicted_path[0].t_plus_h}"
            )

        # Invariant 2: Index 0 point must match current_position
        p0 = self.predicted_path[0]
        c0 = self.current_position
        if abs(p0.lat - c0.lat) > 1e-3 or abs(p0.lon - c0.lon) > 1e-3:
            raise ValueError(
                f"predicted_path[0] ({p0.lat}, {p0.lon}) must match current_position ({c0.lat}, {c0.lon})"
            )

        # Invariant 3: predicted_path must be strictly increasing in time
        prev_t = -1
        for idx, pt in enumerate(self.predicted_path):
            if pt.t_plus_h <= prev_t:
                raise ValueError(
                    f"predicted_path must be strictly time-ordered: step {idx} (t={pt.t_plus_h}) <= previous (t={prev_t})"
                )
            prev_t = pt.t_plus_h

        # Invariant 4: cone_radius_km must be parallel (same length) to predicted_path
        cone_len = len(self.uncertainty.cone_radius_km)
        path_len = len(self.predicted_path)
        if cone_len != path_len:
            raise ValueError(
                f"cone_radius_km length ({cone_len}) must match predicted_path length ({path_len})"
            )

        return self


# -----------------------------------------------------------------------------
# Sub-component Models
# -----------------------------------------------------------------------------


class IdentificationPayload(BaseModel):
    """Detection status and calibrated confidence score."""

    model_config = ConfigDict(extra="forbid")

    detected: bool = Field(..., description="System presence indicator")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence score in [0, 1]")


class ClassificationPayload(BaseModel):
    """Lifecycle stage classification and confidence."""

    model_config = ConfigDict(extra="forbid")

    stage: StageEnum = Field(..., description="Life-cycle stage enum")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Classification confidence in [0, 1]")


class IntensityPayload(BaseModel):
    """Intensity estimation on IMD scale."""

    model_config = ConfigDict(extra="forbid")

    level: IntensityLevelEnum = Field(..., description="IMD intensity classification")
    scale: Literal["IMD"] = Field("IMD", description="Meteorological scale, locked to IMD")
    max_wind_kt: float = Field(..., ge=0.0, description="Maximum sustained wind in knots")
    min_pressure_mb: float = Field(..., ge=800.0, le=1050.0, description="Central pressure in millibars")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Intensity confidence in [0, 1]")


# -----------------------------------------------------------------------------
# Master Frozen CycloneIntelligence Model
# -----------------------------------------------------------------------------


class CycloneIntelligence(BaseModel):
    """Master CycloneIntelligence contract payload emitted by Chakravyuh Cyclone Brain."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = Field("1.0", description="Locked schema version")
    cyclone_id: str = Field(..., min_length=1, description="Unique storm identifier")
    name: str = Field(..., min_length=1, description="Cyclone or disturbance name")
    timestamp: str = Field(..., description="ISO-8601 UTC timestamp string (e.g. 2026-09-08T10:00:00Z)")
    basin: str = Field(..., min_length=1, description="Oceanic basin")

    identification: IdentificationPayload
    classification: ClassificationPayload
    intensity: IntensityPayload
    prediction: Optional[PredictionPayload] = Field(
        ..., description="Forecast trajectory and uncertainty. None if detected is false."
    )

    sources: List[str] = Field(..., min_length=1, description="Active input sources")
    model_version: str = Field(..., min_length=1, description="Model release version")
    tier: TierEnum = Field(..., description="Engine execution tier: tier1, tier0, or mixed")
    extra: Dict[str, Any] = Field(default_factory=dict, description="Free-form supplemental metadata")

    @field_validator("timestamp")
    @classmethod
    def validate_iso_timestamp(cls, v: str) -> str:
        # Validate ISO-8601 parsing
        try:
            # Handle trailing 'Z' for UTC
            ts = v.replace("Z", "+00:00") if v.endswith("Z") else v
            datetime.fromisoformat(ts)
        except Exception as e:
            raise ValueError(f"Invalid ISO-8601 UTC timestamp: {v}") from e
        return v

    @model_validator(mode="after")
    def validate_detection_prediction_invariant(self) -> CycloneIntelligence:
        # Invariant: If detected is False, prediction must be None
        if not self.identification.detected and self.prediction is not None:
            raise ValueError("When identification.detected is False, prediction must be null (None)")
        return self

    def to_dict(self) -> Dict[str, Any]:
        """Converts model to serializable dictionary."""
        return self.model_dump(mode="json")

    def to_validated_dict(self) -> Dict[str, Any]:
        """Serializes and validates against JSON Schema."""
        d = self.to_dict()
        schema_path = Path(__file__).resolve().parent / "cyclone_intelligence.schema.json"
        if jsonschema is not None and schema_path.is_file():
            with open(schema_path, "r", encoding="utf-8") as f:
                schema = json.load(f)
            jsonschema.validate(instance=d, schema=schema)
        return d


__all__ = [
    "StageEnum",
    "IntensityLevelEnum",
    "TierEnum",
    "GeoPoint",
    "TrajectoryPoint",
    "UncertaintyCone",
    "PredictionPayload",
    "IdentificationPayload",
    "ClassificationPayload",
    "IntensityPayload",
    "CycloneIntelligence",
]
