"""Unit tests for Tier-0 Identification, Stage Classification, and Intensity Estimation baselines."""

from ml.cyclone.models.baseline_classify import classify
from ml.cyclone.models.baseline_identify import identify
from ml.cyclone.models.baseline_intensity import intensity
from ml.cyclone.schema.models import (
    ClassificationPayload,
    IdentificationPayload,
    IntensityLevelEnum,
    IntensityPayload,
    StageEnum,
)

# -----------------------------------------------------------------------------
# Tier-0 Identification Tests
# -----------------------------------------------------------------------------


def test_identify_calibrated_confidence():
    """Asserts identification produces smooth, honest confidence scores across intensity regimes."""
    # Case 1: Quiet open ocean (wind 8 kt, no history)
    quiet_sample = {"wind_kt": 8.0, "pres_mb": 1010.0, "history": []}
    quiet_res = identify(quiet_sample)
    assert quiet_res["detected"] is False
    assert 0.05 <= quiet_res["confidence"] < 0.25

    # Case 2: Borderline convective disturbance (wind 16.5 kt)
    border_sample = {"wind_kt": 16.5, "pres_mb": 1007.0, "history": []}
    border_res = identify(border_sample)
    # Borderline case should have confidence around ~0.45-0.55 (not overconfident)
    assert 0.40 <= border_res["confidence"] <= 0.60

    # Case 3: Clear tropical depression (wind 25 kt, organized 18h history)
    dep_sample = {
        "wind_kt": 25.0,
        "pres_mb": 1000.0,
        "history": [
            {"t_offset_h": -18.0},
            {"t_offset_h": -12.0},
            {"t_offset_h": -6.0},
            {"t_offset_h": 0.0},
        ],
    }
    dep_res = identify(dep_sample)
    assert dep_res["detected"] is True
    assert 0.70 <= dep_res["confidence"] <= 0.90

    # Case 4: Severe mature cyclone (wind 75 kt)
    severe_sample = {
        "wind_kt": 75.0,
        "pres_mb": 960.0,
        "history": [{"t_offset_h": -6.0}, {"t_offset_h": 0.0}],
    }
    severe_res = identify(severe_sample)
    assert severe_res["detected"] is True
    assert severe_res["confidence"] >= 0.90

    # Invariant: Monotonic confidence growth with wind margin
    assert (
        quiet_res["confidence"]
        < border_res["confidence"]
        < dep_res["confidence"]
        < severe_res["confidence"]
    )

    # Invariant: Never a constant 1.0
    for res in [quiet_res, border_res, dep_res, severe_res]:
        assert res["confidence"] < 1.0
        # Contract validation
        IdentificationPayload.model_validate(res)


# -----------------------------------------------------------------------------
# Tier-0 Classification Tests
# -----------------------------------------------------------------------------


def test_classify_boundary_penalty_and_stages():
    """Asserts stage classifier applies boundary uncertainty penalty and maps stages correctly."""
    # Case 1: Right at boundary (33.8 kt is ~0.2 kt away from 34.0 kt Cyclonic Storm threshold)
    boundary_sample = {"wind_kt": 33.8, "nature": "TS", "history": []}
    boundary_res = classify(boundary_sample)

    # Case 2: Deep inside category (42.0 kt is 8 kt away from 34 kt and 6 kt from 48 kt)
    interior_sample = {"wind_kt": 42.0, "nature": "TS", "history": []}
    interior_res = classify(interior_sample)

    # The interior sample must have strictly higher confidence than the borderline sample
    assert interior_res["confidence"] > boundary_res["confidence"]
    assert 0.55 <= boundary_res["confidence"] <= 0.75
    assert interior_res["confidence"] >= 0.85

    # Case 3: Mature stage
    mature_sample = {"wind_kt": 85.0, "nature": "TS", "history": []}
    mature_res = classify(mature_sample)
    assert mature_res["stage"] == StageEnum.MATURE_TROPICAL_CYCLONE

    # Invariant: Never constant 1.0 and valid Pydantic model
    for res in [boundary_res, interior_res, mature_res]:
        assert 0.0 <= res["confidence"] < 1.0
        ClassificationPayload.model_validate(res)


# -----------------------------------------------------------------------------
# Tier-0 Intensity Tests
# -----------------------------------------------------------------------------


def test_intensity_baseline():
    """Asserts intensity estimator maps to IMD levels and scales appropriately."""
    # Case 1: Very Severe Cyclonic Storm
    vscs_sample = {"wind_kt": 75.0, "pres_mb": 960.0}
    vscs_res = intensity(vscs_sample)
    assert vscs_res["level"] == IntensityLevelEnum.VERY_SEVERE_CYCLONIC_STORM
    assert vscs_res["scale"] == "IMD"
    assert vscs_res["max_wind_kt"] == 75.0
    assert vscs_res["min_pressure_mb"] == 960.0
    assert 0.85 <= vscs_res["confidence"] <= 0.94

    # Case 2: Super Cyclonic Storm
    sucs_sample = {"wind_kt": 130.0, "pres_mb": 915.0}
    sucs_res = intensity(sucs_sample)
    assert sucs_res["level"] == IntensityLevelEnum.SUPER_CYCLONIC_STORM

    # Case 3: Boundary penalty (33.8 kt near 34 kt)
    edge_sample = {"wind_kt": 33.8, "pres_mb": 998.0}
    edge_res = intensity(edge_sample)
    assert edge_res["confidence"] < vscs_res["confidence"]

    # Invariant: Never constant 1.0 and valid Pydantic model
    for res in [vscs_res, sucs_res, edge_res]:
        assert 0.0 <= res["confidence"] < 1.0
        IntensityPayload.model_validate(res)
