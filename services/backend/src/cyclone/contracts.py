from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, Field

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

class CycloneIntelligence(BaseModel):
    schema_version: str = "1.0"
    cyclone_id: str
    name: Optional[str] = None
    timestamp: datetime
    basin: str
    identification: CycloneIdentification
    classification: Optional[CycloneClassification] = None
    intensity: Optional[CycloneIntensity] = None
    prediction: Optional[CyclonePrediction] = None
    sources: List[str] = Field(default_factory=list)
    model_version: str = "Chakravyooh-brain-0.1"
    extra: dict[str, Any] = Field(default_factory=dict)

class ZoneRiskSnapshot(BaseModel):
    zone_id: str
    name: str
    risk: str
    score: float
    eta_hours: Optional[float] = None
