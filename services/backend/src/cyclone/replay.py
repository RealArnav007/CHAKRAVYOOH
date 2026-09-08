"""
Chakravyooh Demo Replay Engine — Master PRD §42 Final Demo Flow
Streams 4 historical Cyclone Amphan frames over WebSocket to drive the live hackathon pitch.

Frame timeline:
  T-72h → CYCLONE PATTERN DETECTED (Confidence 94%)
  T-48h → CLASSIFIED: Mature Tropical Cyclone, trajectory locked
  T-24h → Risk zones elevated: Puri=EXTREME, Bhubaneswar=HIGH
  T-12h → Cryptographically signed CYCLONE_WARNING generated and broadcast
"""
import asyncio
import time
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, BackgroundTasks, Query
from pydantic import BaseModel

from src.cyclone.contracts import (
    CycloneIntelligence, CycloneIdentification, CycloneClassification,
    CycloneIntensity, CyclonePrediction, CyclonePosition,
    PredictedPathPoint, CycloneUncertainty, CycloneFreshness,
)
from src.cyclone.processor import process_cyclone_intelligence

# ─────────────────────────────────────────────────────────────────────────────
# Historical Cyclone Amphan Replay Frames (Bay of Bengal, May 2020)
# ─────────────────────────────────────────────────────────────────────────────

def _build_frames() -> list[CycloneIntelligence]:
    """Builds the 4 demo frames for the Cyclone Amphan live presentation."""
    now = datetime.now(timezone.utc)

    # Frame 1 — T-72h: Pattern Detected (Confidence 94%)
    frame1 = CycloneIntelligence(
        cyclone_id="CYC-2026-BAY-DEMO",
        name="Replay-Amphan",
        timestamp=now - timedelta(hours=72),
        basin="North Indian Ocean",
        identification=CycloneIdentification(detected=True, confidence=0.94),
        classification=CycloneClassification(stage="DEVELOPING_DISTURBANCE", confidence=0.72),
        intensity=CycloneIntensity(level="DEPRESSION", scale="IMD",
                                   max_wind_kt=35.0, min_pressure_mb=1000.0, confidence=0.68),
        prediction=CyclonePrediction(
            current_position=CyclonePosition(lat=12.5, lon=85.0),
            heading_deg=15.0, speed_kt=8.0, forecast_hours=72,
            predicted_path=[
                PredictedPathPoint(t_plus_h=0, lat=12.5, lon=85.0),
                PredictedPathPoint(t_plus_h=24, lat=15.2, lon=85.8),
                PredictedPathPoint(t_plus_h=48, lat=17.8, lon=86.4),
                PredictedPathPoint(t_plus_h=72, lat=20.0, lon=87.0),
            ],
            confidence=0.78,
            uncertainty=CycloneUncertainty(cone_radius_km=[0.0, 95.0, 160.0, 240.0]),
        ),
        sources=["ibtracs_replay", "era5"],
        tier="tier1",
        freshness=CycloneFreshness(generated_at=now - timedelta(hours=72),
                                    valid_until=now - timedelta(hours=48)),
        extra={"demo_frame": 1, "demo_label": "T-72h: Pattern Detected"},
    )

    # Frame 2 — T-48h: Classification upgraded, trajectory locked
    frame2 = CycloneIntelligence(
        cyclone_id="CYC-2026-BAY-DEMO",
        name="Replay-Amphan",
        timestamp=now - timedelta(hours=48),
        basin="North Indian Ocean",
        identification=CycloneIdentification(detected=True, confidence=0.97),
        classification=CycloneClassification(stage="MATURE_TROPICAL_CYCLONE", confidence=0.92),
        intensity=CycloneIntensity(level="VERY_SEVERE_CYCLONIC_STORM", scale="IMD",
                                   max_wind_kt=75.0, min_pressure_mb=965.0, confidence=0.88),
        prediction=CyclonePrediction(
            current_position=CyclonePosition(lat=15.2, lon=85.8),
            heading_deg=22.0, speed_kt=10.5, forecast_hours=48,
            predicted_path=[
                PredictedPathPoint(t_plus_h=0, lat=15.2, lon=85.8),
                PredictedPathPoint(t_plus_h=12, lat=16.8, lon=86.2),
                PredictedPathPoint(t_plus_h=24, lat=18.5, lon=86.8),
                PredictedPathPoint(t_plus_h=48, lat=21.6, lon=88.3),
            ],
            confidence=0.85,
            uncertainty=CycloneUncertainty(cone_radius_km=[0.0, 62.0, 110.0, 185.0]),
        ),
        sources=["ibtracs_replay", "insat3d_ir", "era5"],
        tier="tier1",
        freshness=CycloneFreshness(generated_at=now - timedelta(hours=48),
                                    valid_until=now - timedelta(hours=24)),
        extra={"demo_frame": 2, "demo_label": "T-48h: Classified — Mature Tropical Cyclone"},
    )

    # Frame 3 — T-24h: Landfall imminent, risk zones triggered
    frame3 = CycloneIntelligence(
        cyclone_id="CYC-2026-BAY-DEMO",
        name="Replay-Amphan",
        timestamp=now - timedelta(hours=24),
        basin="North Indian Ocean",
        identification=CycloneIdentification(detected=True, confidence=0.98),
        classification=CycloneClassification(stage="MATURE_TROPICAL_CYCLONE", confidence=0.95),
        intensity=CycloneIntensity(level="VERY_SEVERE_CYCLONIC_STORM", scale="IMD",
                                   max_wind_kt=85.0, min_pressure_mb=950.0, confidence=0.91),
        prediction=CyclonePrediction(
            current_position=CyclonePosition(lat=18.5, lon=86.8),
            heading_deg=25.0, speed_kt=11.5, forecast_hours=24,
            predicted_path=[
                PredictedPathPoint(t_plus_h=0, lat=18.5, lon=86.8),
                PredictedPathPoint(t_plus_h=6, lat=19.5, lon=87.2),
                PredictedPathPoint(t_plus_h=12, lat=20.4, lon=87.6),
                PredictedPathPoint(t_plus_h=24, lat=21.9, lon=88.4),
            ],
            confidence=0.88,
            uncertainty=CycloneUncertainty(cone_radius_km=[0.0, 46.0, 78.0, 132.0]),
        ),
        sources=["ibtracs_replay", "insat3d_ir", "era5"],
        tier="tier1",
        freshness=CycloneFreshness(generated_at=now - timedelta(hours=24),
                                    valid_until=now),
        extra={
            "demo_frame": 3,
            "demo_label": "T-24h: RISK ZONES ELEVATED — Puri=EXTREME, Bhubaneswar=HIGH",
            "landfall_point": {"lat": 21.65, "lon": 88.35, "eta_hours": 22.5},
        },
    )

    # Frame 4 — T-12h: Warning signed and broadcast
    frame4 = CycloneIntelligence(
        cyclone_id="CYC-2026-BAY-DEMO",
        name="Replay-Amphan",
        timestamp=now - timedelta(hours=12),
        basin="North Indian Ocean",
        identification=CycloneIdentification(detected=True, confidence=0.99),
        classification=CycloneClassification(stage="MATURE_TROPICAL_CYCLONE", confidence=0.97),
        intensity=CycloneIntensity(level="EXTREMELY_SEVERE_CYCLONIC_STORM", scale="IMD",
                                   max_wind_kt=95.0, min_pressure_mb=938.0, confidence=0.94),
        prediction=CyclonePrediction(
            current_position=CyclonePosition(lat=20.4, lon=87.6),
            heading_deg=28.0, speed_kt=12.0, forecast_hours=12,
            predicted_path=[
                PredictedPathPoint(t_plus_h=0, lat=20.4, lon=87.6),
                PredictedPathPoint(t_plus_h=6, lat=21.1, lon=88.0),
                PredictedPathPoint(t_plus_h=12, lat=21.8, lon=88.5),
            ],
            confidence=0.92,
            uncertainty=CycloneUncertainty(cone_radius_km=[0.0, 32.0, 58.0]),
        ),
        sources=["ibtracs_replay", "insat3d_ir", "era5"],
        tier="tier1",
        freshness=CycloneFreshness(generated_at=now - timedelta(hours=12),
                                    valid_until=now + timedelta(hours=12)),
        extra={
            "demo_frame": 4,
            "demo_label": "T-12h: SIGNED WARNING ISSUED — Relay via Chakravyooh mesh",
            "saffir_simpson": "Category 3",
        },
    )

    return [frame1, frame2, frame3, frame4]


async def _run_replay_sequence(interval_s: int):
    """Background task: feeds each historical frame through the full cyclone processing pipeline."""
    frames = _build_frames()
    for i, frame in enumerate(frames, start=1):
        try:
            await process_cyclone_intelligence(frame, frame.model_dump(mode="json"))
        except Exception:
            pass  # Don't let a single frame failure abort the demo
        if i < len(frames):
            await asyncio.sleep(interval_s)


# ─────────────────────────────────────────────────────────────────────────────
# Router Endpoint
# ─────────────────────────────────────────────────────────────────────────────

class ReplayResponse(BaseModel):
    status: str
    message: str
    frames: int
    interval_s: int


def init_replay_routes(router: APIRouter):
    @router.post("/replay/start", response_model=ReplayResponse)
    async def start_demo_replay(
        background_tasks: BackgroundTasks,
        interval_s: int = Query(default=3, ge=1, le=30,
                                description="Seconds between replay frames (1-30)"),
    ):
        """
        Triggers the 4-frame Cyclone Amphan historical replay for the live demo (Master PRD §42).
        Streams frames through the full Risk Engine → Zone Elevation → Signed Alert pipeline.
        Each frame is processed in the background and broadcast live over WebSocket.
        """
        background_tasks.add_task(_run_replay_sequence, interval_s)
        return ReplayResponse(
            status="replay_started",
            message=(
                f"Demo replay initiated — {4} Cyclone Amphan frames will process "
                f"at {interval_s}s intervals. Watch your WebSocket for live events."
            ),
            frames=4,
            interval_s=interval_s,
        )

