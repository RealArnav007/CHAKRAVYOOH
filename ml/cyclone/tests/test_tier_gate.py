"""Unit tests for per-field Tier-1 / Tier-0 gating, provenance tracking, and graceful degradation."""

from __future__ import annotations

import pytest

from ml.cyclone.fusion.tier_gate import (
    gate_and_assemble_cyclone_intelligence,
)
from ml.cyclone.schema.models import (
    CycloneIntelligence,
    IntensityLevelEnum,
    TierEnum,
)


@pytest.fixture
def dummy_tier1_output() -> dict:
    return {
        "cyclone_id": "CYC-2026-NIO-001",
        "name": "TEST-SYSTEM",
        "basin": "North Indian Ocean",
        "identification": {
            "detected": True,
            "confidence": 0.94,
        },
        "classification": {
            "stage": "VERY_SEVERE_CYCLONIC_STORM",
            "confidence": 0.88,
        },
        "intensity": {
            "level": "VERY_SEVERE_CYCLONIC_STORM",
            "scale": "IMD",
            "max_wind_kt": 75.0,
            "min_pressure_mb": 970.0,
            "confidence": 0.85,
        },
        "prediction": {
            "current_position": {"lat": 15.0, "lon": 85.0},
            "heading_deg": 35.0,
            "speed_kt": 12.0,
            "forecast_hours": 72,
            "predicted_path": [
                {"t_plus_h": 0, "lat": 15.0, "lon": 85.0},
                {"t_plus_h": 6, "lat": 15.6, "lon": 85.4},
                {"t_plus_h": 12, "lat": 16.3, "lon": 85.9},
                {"t_plus_h": 24, "lat": 17.8, "lon": 86.8},
                {"t_plus_h": 48, "lat": 20.4, "lon": 88.1},
                {"t_plus_h": 72, "lat": 22.9, "lon": 89.2},
            ],
            "confidence": 0.82,
            "max_log_var": 1.2,
            "uncertainty": {"cone_radius_km": [0.0, 45.0, 75.0, 130.0, 210.0, 295.0]},
        },
    }


@pytest.fixture
def dummy_tier0_output() -> dict:
    return {
        "cyclone_id": "CYC-2026-NIO-001",
        "name": "TEST-SYSTEM",
        "basin": "North Indian Ocean",
        "identification": {
            "detected": True,
            "confidence": 0.50,
        },
        "classification": {
            "stage": "TROPICAL_DEPRESSION",
            "confidence": 0.50,
        },
        "intensity": {
            "level": "DEPRESSION",
            "scale": "IMD",
            "max_wind_kt": 25.0,
            "min_pressure_mb": 1000.0,
            "confidence": 0.50,
        },
        "prediction": {
            "current_position": {"lat": 15.0, "lon": 85.0},
            "heading_deg": 0.0,
            "speed_kt": 10.0,
            "forecast_hours": 72,
            "predicted_path": [
                {"t_plus_h": 0, "lat": 15.0, "lon": 85.0},
                {"t_plus_h": 6, "lat": 15.1, "lon": 85.1},
                {"t_plus_h": 12, "lat": 15.2, "lon": 85.2},
                {"t_plus_h": 24, "lat": 15.4, "lon": 85.4},
                {"t_plus_h": 48, "lat": 15.8, "lon": 85.8},
                {"t_plus_h": 72, "lat": 16.2, "lon": 86.2},
            ],
            "confidence": 0.50,
            "uncertainty": {"cone_radius_km": [0.0, 40.0, 70.0, 125.0, 200.0, 280.0]},
        },
    }


def test_tier_gate_all_tier1_confident(dummy_tier1_output: dict, dummy_tier0_output: dict) -> None:
    """Tests that full confident multi-modal inputs select Tier-1 across all fields."""
    inputs = {
        "image_available": True,
        "env_available": True,
        "track_available": True,
        "current_position": {"lat": 15.0, "lon": 85.0},
    }

    result = gate_and_assemble_cyclone_intelligence(
        tier1_payload=dummy_tier1_output,
        tier0_payload=dummy_tier0_output,
        inputs=inputs,
    )

    assert isinstance(result, CycloneIntelligence)
    assert result.tier == TierEnum.TIER1
    prov = result.extra["provenance"]["sources"]
    assert prov["identification"] == "tier1"
    assert prov["classification"] == "tier1"
    assert prov["intensity"] == "tier1"
    assert prov["prediction"] == "tier1"


def test_tier_gate_low_confidence_fallback(
    dummy_tier1_output: dict, dummy_tier0_output: dict
) -> None:
    """Tests per-field fallback to Tier-0 when confidence is below configured threshold."""
    inputs = {
        "image_available": True,
        "env_available": True,
        "track_available": True,
        "current_position": {"lat": 15.0, "lon": 85.0},
    }

    # Artificially lower stage and intensity confidences
    dummy_tier1_output["classification"]["confidence"] = 0.40  # Below min 0.60
    dummy_tier1_output["intensity"]["confidence"] = 0.35  # Below min 0.60

    result = gate_and_assemble_cyclone_intelligence(
        tier1_payload=dummy_tier1_output,
        tier0_payload=dummy_tier0_output,
        inputs=inputs,
    )

    assert result.tier == TierEnum.MIXED
    prov = result.extra["provenance"]["sources"]
    assert prov["identification"] == "tier1"
    assert prov["classification"] == "tier0"
    assert prov["intensity"] == "tier0"
    assert prov["prediction"] == "tier1"

    # Intensity level should match Tier-0
    assert result.intensity.level == IntensityLevelEnum.DEPRESSION


def test_tier_gate_excessive_track_variance_fallback(
    dummy_tier1_output: dict, dummy_tier0_output: dict
) -> None:
    """Tests track fallback to Tier-0 when predicted log-variance ceiling is exceeded."""
    inputs = {
        "image_available": True,
        "env_available": True,
        "track_available": True,
        "current_position": {"lat": 15.0, "lon": 85.0},
    }

    # Set excessive log-variance
    dummy_tier1_output["prediction"]["max_log_var"] = 7.5  # Exceeds ceiling 5.0

    result = gate_and_assemble_cyclone_intelligence(
        tier1_payload=dummy_tier1_output,
        tier0_payload=dummy_tier0_output,
        inputs=inputs,
    )

    assert result.tier == TierEnum.MIXED
    prov = result.extra["provenance"]["sources"]
    assert prov["prediction"] == "tier0"
    assert "exceeded ceiling" in result.extra["provenance"]["reasons"]["prediction"]


def test_tier_gate_missing_image_graceful_degradation(
    dummy_tier1_output: dict, dummy_tier0_output: dict
) -> None:
    """Tests that missing satellite image gracefully uses env+track without failing."""
    inputs = {
        "image_available": False,  # Image missing
        "env_available": True,
        "track_available": True,
        "current_position": {"lat": 15.0, "lon": 85.0},
    }

    result = gate_and_assemble_cyclone_intelligence(
        tier1_payload=dummy_tier1_output,
        tier0_payload=dummy_tier0_output,
        inputs=inputs,
    )

    assert isinstance(result, CycloneIntelligence)
    assert result.tier in [TierEnum.TIER1, TierEnum.MIXED]
    assert "insat3d_ir" not in result.sources
    assert "era5" in result.sources
    assert "ibtracs_track" in result.sources


def test_tier_gate_missing_era5_graceful_degradation(
    dummy_tier1_output: dict, dummy_tier0_output: dict
) -> None:
    """Tests that missing ERA5 environment gracefully uses image+track."""
    inputs = {
        "image_available": True,
        "env_available": False,  # ERA5 missing
        "track_available": True,
        "current_position": {"lat": 15.0, "lon": 85.0},
    }

    result = gate_and_assemble_cyclone_intelligence(
        tier1_payload=dummy_tier1_output,
        tier0_payload=dummy_tier0_output,
        inputs=inputs,
    )

    assert isinstance(result, CycloneIntelligence)
    assert "era5" not in result.sources
    assert "insat3d_ir" in result.sources


def test_tier_gate_missing_everything_except_track(
    dummy_tier1_output: dict, dummy_tier0_output: dict
) -> None:
    """Tests that missing both image and env triggers complete Tier-0 fallback."""
    inputs = {
        "image_available": False,
        "env_available": False,
        "track_available": True,
        "current_position": {"lat": 15.0, "lon": 85.0},
    }

    result = gate_and_assemble_cyclone_intelligence(
        tier1_payload=dummy_tier1_output,
        tier0_payload=dummy_tier0_output,
        inputs=inputs,
    )

    assert result.tier == TierEnum.TIER0
    prov = result.extra["provenance"]["sources"]
    assert all(v == "tier0" for v in prov.values())


def test_tier_gate_not_detected_invariant(
    dummy_tier1_output: dict, dummy_tier0_output: dict
) -> None:
    """Tests that when identification.detected is False, prediction is strictly None."""
    inputs = {
        "image_available": True,
        "env_available": True,
        "track_available": True,
        "current_position": {"lat": 15.0, "lon": 85.0},
    }
    dummy_tier1_output["identification"]["detected"] = False
    dummy_tier1_output["identification"]["confidence"] = 0.95

    result = gate_and_assemble_cyclone_intelligence(
        tier1_payload=dummy_tier1_output,
        tier0_payload=dummy_tier0_output,
        inputs=inputs,
    )

    assert result.identification.detected is False
    assert result.prediction is None
    # Validates JSON schema invariant
    assert result.to_validated_dict()


def test_tier_gate_malformed_inputs_never_raises(dummy_tier0_output: dict) -> None:
    """Tests that completely corrupted/invalid payloads never raise and emit a valid Tier-0 object."""
    corrupted_tier1 = {
        "identification": {"detected": "invalid_bool", "confidence": "non_numeric"},
        "intensity": {"max_wind_kt": -999.0, "min_pressure_mb": 2000.0},
        "prediction": {"predicted_path": "invalid_structure"},
    }

    result = gate_and_assemble_cyclone_intelligence(
        tier1_payload=corrupted_tier1,  # type: ignore
        tier0_payload=dummy_tier0_output,
        inputs={"current_position": {"lat": 15.0, "lon": 85.0}},
    )

    assert isinstance(result, CycloneIntelligence)
    assert result.tier == TierEnum.TIER0
    assert result.intensity.max_wind_kt >= 0.0
