"""Unit tests for motion features, environmental imputation, and multi-modal fused sample creation."""

import json
from pathlib import Path
import numpy as np
import pytest

from ml.cyclone.features.environmental import (
    DEFAULT_IMPUTER_MEDIANS,
    ENV_FEATURE_NAMES,
    extract_environmental_features,
)
from ml.cyclone.features.fusion import (
    DEFAULT_HORIZONS,
    FusedSample,
    make_fused_sample,
)
from ml.cyclone.features.motion import (
    MOTION_FEATURE_NAMES,
    extract_motion_features,
)


SPEC_FILE = Path(__file__).resolve().parent.parent / "features" / "feature_spec.json"


# -----------------------------------------------------------------------------
# Feature Spec Consistency Tests
# -----------------------------------------------------------------------------


def test_feature_spec_matches_code_constants():
    """Asserts feature_spec.json exactly mirrors code definitions."""
    assert SPEC_FILE.is_file(), f"feature_spec.json missing at {SPEC_FILE}"
    with open(SPEC_FILE, "r", encoding="utf-8") as f:
        spec = json.load(f)

    assert spec["motion_features"] == MOTION_FEATURE_NAMES
    assert spec["environmental_features"] == ENV_FEATURE_NAMES
    assert spec["forecast_horizons_hours"] == DEFAULT_HORIZONS
    assert len(spec["motion_features"]) == 16
    assert len(spec["environmental_features"]) == 6


# -----------------------------------------------------------------------------
# Motion Feature Extractor Tests
# -----------------------------------------------------------------------------


def test_motion_feature_extraction():
    """Asserts motion feature extraction produces 16-d float32 vector with correct dynamics."""
    sample = {
        "lat": 18.5,
        "lon": 86.8,
        "wind_kt": 85.0,
        "pres_mb": 950.0,
        "storm_speed_kt": 12.0,
        "heading_deg": 25.0,
        "history": [
            {"t_offset_h": -24.0, "lat": 14.0, "lon": 85.0, "wind_kt": 55.0, "pres_mb": 980.0, "speed_kt": 10.0, "heading_deg": 15.0},
            {"t_offset_h": -12.0, "lat": 16.0, "lon": 85.8, "wind_kt": 70.0, "pres_mb": 965.0, "speed_kt": 11.0, "heading_deg": 20.0},
            {"t_offset_h": -6.0, "lat": 17.2, "lon": 86.3, "wind_kt": 80.0, "pres_mb": 955.0, "speed_kt": 11.5, "heading_deg": 22.0},
            {"t_offset_h": 0.0, "lat": 18.5, "lon": 86.8, "wind_kt": 85.0, "pres_mb": 950.0, "speed_kt": 12.0, "heading_deg": 25.0},
        ],
    }

    vec = extract_motion_features(sample)

    assert isinstance(vec, np.ndarray)
    assert vec.shape == (16,)
    assert vec.dtype == np.float32

    # Verify specific dynamics
    # dv_6h = 85 - 80 = 5.0 kt
    assert abs(vec[4] - 5.0) < 1e-4
    # dv_12h = 85 - 70 = 15.0 kt
    assert abs(vec[5] - 15.0) < 1e-4
    # dv_24h = 85 - 55 = 30.0 kt
    assert abs(vec[6] - 30.0) < 1e-4

    # dp_6h = 950 - 955 = -5.0 mb
    assert abs(vec[7] - (-5.0)) < 1e-4

    # Coriolis parameter is positive in northern hemisphere
    coriolis_val = vec[14]
    assert coriolis_val > 0.0


# -----------------------------------------------------------------------------
# Environmental Feature Imputation Tests
# -----------------------------------------------------------------------------


def test_environmental_feature_imputation():
    """Asserts environmental extractor imputes NaNs with medians and preserves real values."""
    sample_with_nans = {
        "env": {
            "sst_c": 29.2,            # Real value
            "shear_ms": float("nan"), # Missing -> should impute 12.0
            "rh500": 70.0,            # Real value
            "vort850": None,          # Missing -> should impute 15.0
            "mslp_mb": 1004.0,        # Real value
            "wind10m_ms": float("nan"),# Missing -> should impute 8.0
        }
    }

    vec = extract_environmental_features(sample_with_nans)

    assert isinstance(vec, np.ndarray)
    assert vec.shape == (6,)
    assert vec.dtype == np.float32

    # Check that no NaNs remain
    assert not np.isnan(vec).any()

    # Check preserved vs imputed values
    assert abs(vec[0] - 29.2) < 1e-4                        # sst_c preserved
    assert abs(vec[1] - DEFAULT_IMPUTER_MEDIANS["shear_ms"]) < 1e-4 # shear imputed
    assert abs(vec[2] - 70.0) < 1e-4                        # rh500 preserved
    assert abs(vec[3] - DEFAULT_IMPUTER_MEDIANS["vort850"]) < 1e-4  # vort imputed
    assert abs(vec[4] - 1004.0) < 1e-4                      # mslp preserved
    assert abs(vec[5] - DEFAULT_IMPUTER_MEDIANS["wind10m_ms"]) < 1e-4 # wind10m imputed


# -----------------------------------------------------------------------------
# Fused Sample & Masked Horizons Tests
# -----------------------------------------------------------------------------


def test_fused_sample_future_horizons_and_masking():
    """Asserts fused sample correctly populates targets and masks out-of-bounds horizons near storm end."""
    sample = {
        "storm_id": "AMPHAN_2020",
        "time": "2020-05-19T12:00:00Z",
        "lat": 18.5,
        "lon": 86.8,
        "wind_kt": 85.0,
        "pres_mb": 950.0,
        "storm_speed_kt": 12.0,
        "heading_deg": 25.0,
        "history": [
            {"t_offset_h": 0.0, "lat": 18.5, "lon": 86.8, "wind_kt": 85.0, "pres_mb": 950.0, "speed_kt": 12.0, "heading_deg": 25.0}
        ],
    }

    # Case 1: Storm ends after 24h (48h and 72h horizons missing)
    future_lookup_near_end = {
        6: (19.45, 87.20),
        12: (20.40, 87.65),
        24: (21.90, 88.40),
        # 48h and 72h absent (e.g. post-landfall dissipation)
    }

    fused = make_fused_sample(
        sample=sample,
        storm_future_lookup=future_lookup_near_end,
        horizons=[6, 12, 24, 48, 72],
        history_steps=8,
    )

    assert isinstance(fused, FusedSample)
    assert fused.env_vector.shape == (6,)
    assert fused.motion_vector.shape == (16,)
    assert fused.track_sequence.shape == (8, 7)

    masks = fused.targets["horizon_masks"]
    assert np.array_equal(masks, [True, True, True, False, False])

    deltas = fused.targets["future_deltas"]
    assert deltas.shape == (5, 2)
    # Delta at +6h: (19.45 - 18.50 = 0.95, 87.20 - 86.80 = 0.40)
    assert abs(deltas[0, 0] - 0.95) < 1e-3
    assert abs(deltas[0, 1] - 0.40) < 1e-3
    # Deltas for masked out steps should be 0.0
    assert deltas[3, 0] == 0.0 and deltas[3, 1] == 0.0
    assert deltas[4, 0] == 0.0 and deltas[4, 1] == 0.0

    # Multi-task target types
    assert fused.targets["wind_kt"] == 85.0
    assert fused.targets["pres_mb"] == 950.0
    assert fused.targets["imd_level_idx"] == 4  # VERY_SEVERE_CYCLONIC_STORM
    assert fused.targets["stage_idx"] == 3      # MATURE_TROPICAL_CYCLONE
    assert fused.targets["detected"] == 1.0
