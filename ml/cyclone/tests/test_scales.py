"""Unit tests for meteorological scale converters, lifecycle stage classifier, and track cleaning QC."""

import pandas as pd
import pytest

from ml.cyclone.preprocess.clean import clean_tracks
from ml.cyclone.preprocess.scales import (
    lifecycle_stage,
    wind_kt_to_imd_level,
    wind_kt_to_saffir_simpson,
)
from ml.cyclone.schema.models import IntensityLevelEnum, StageEnum

# -----------------------------------------------------------------------------
# IMD Intensity Scale Boundary Tests
# -----------------------------------------------------------------------------


@pytest.mark.parametrize(
    "wind_kt,expected_level",
    [
        (10.0, IntensityLevelEnum.DEPRESSION),
        (17.0, IntensityLevelEnum.DEPRESSION),
        (27.0, IntensityLevelEnum.DEPRESSION),
        (28.0, IntensityLevelEnum.DEEP_DEPRESSION),
        (33.0, IntensityLevelEnum.DEEP_DEPRESSION),
        (34.0, IntensityLevelEnum.CYCLONIC_STORM),
        (47.0, IntensityLevelEnum.CYCLONIC_STORM),
        (48.0, IntensityLevelEnum.SEVERE_CYCLONIC_STORM),
        (63.0, IntensityLevelEnum.SEVERE_CYCLONIC_STORM),
        (64.0, IntensityLevelEnum.VERY_SEVERE_CYCLONIC_STORM),
        (89.0, IntensityLevelEnum.VERY_SEVERE_CYCLONIC_STORM),
        (90.0, IntensityLevelEnum.EXTREMELY_SEVERE_CYCLONIC_STORM),
        (119.0, IntensityLevelEnum.EXTREMELY_SEVERE_CYCLONIC_STORM),
        (120.0, IntensityLevelEnum.SUPER_CYCLONIC_STORM),
        (145.0, IntensityLevelEnum.SUPER_CYCLONIC_STORM),
    ],
)
def test_imd_intensity_threshold_boundaries(wind_kt, expected_level):
    """Asserts each exact IMD category boundary converts to the correct enum."""
    assert wind_kt_to_imd_level(wind_kt) == expected_level


# -----------------------------------------------------------------------------
# Saffir-Simpson Scale Boundary Tests
# -----------------------------------------------------------------------------


@pytest.mark.parametrize(
    "wind_kt,expected_str",
    [
        (25.0, "Tropical Depression"),
        (33.9, "Tropical Depression"),
        (34.0, "Tropical Storm"),
        (63.0, "Tropical Storm"),
        (64.0, "Category 1"),
        (82.0, "Category 1"),
        (83.0, "Category 2"),
        (95.0, "Category 2"),
        (96.0, "Category 3"),
        (112.0, "Category 3"),
        (113.0, "Category 4"),
        (136.0, "Category 4"),
        (137.0, "Category 5"),
        (160.0, "Category 5"),
    ],
)
def test_saffir_simpson_threshold_boundaries(wind_kt, expected_str):
    """Asserts Saffir-Simpson category string mapping across all intensity tiers."""
    assert wind_kt_to_saffir_simpson(wind_kt) == expected_str


# -----------------------------------------------------------------------------
# Lifecycle Stage Transition Tests
# -----------------------------------------------------------------------------


def test_lifecycle_stage_transitions():
    """Asserts life-cycle stage classifications across realistic evolution phases."""
    # 1. Developing disturbance: winds rising from 15 to 25 kt
    history_early = pd.DataFrame([{"wind_kt": 15.0}, {"wind_kt": 20.0}])
    row_early = {"wind_kt": 25.0, "nature": "TS"}
    assert lifecycle_stage(row_early, history_early) == StageEnum.DEVELOPING_DISTURBANCE

    # 2. Tropical Depression: steady at 25 kt
    history_dep = pd.DataFrame([{"wind_kt": 25.0}, {"wind_kt": 25.0}])
    row_dep = {"wind_kt": 25.0, "nature": "TS"}
    assert lifecycle_stage(row_dep, history_dep) == StageEnum.TROPICAL_DEPRESSION

    # 3. Mature tropical cyclone: 75 kt (Very Severe Cyclonic Storm)
    row_mature = {"wind_kt": 75.0, "nature": "TS"}
    assert lifecycle_stage(row_mature) == StageEnum.MATURE_TROPICAL_CYCLONE

    # 4. Weakening system: peak was 110 kt, now down to 65 kt (> 15 kt decline)
    history_weak = pd.DataFrame([{"wind_kt": 90.0}, {"wind_kt": 110.0}, {"wind_kt": 85.0}])
    row_weak = {"wind_kt": 65.0, "nature": "TS"}
    assert lifecycle_stage(row_weak, history_weak) == StageEnum.WEAKENING_SYSTEM

    # 5. Post-tropical remnant: extratropical transition
    row_et = {"wind_kt": 40.0, "nature": "ET"}
    assert lifecycle_stage(row_et) == StageEnum.POST_TROPICAL_REMNANT


# -----------------------------------------------------------------------------
# Track Cleaning and Quality Control Tests
# -----------------------------------------------------------------------------


def test_clean_tracks_qc_and_interpolation():
    """Asserts clean_tracks deduplicates, interpolates short gaps, clips outliers, and reports QC."""
    test_data = pd.DataFrame(
        [
            # Row 0
            {
                "storm_id": "STORM_A",
                "time": "2020-05-16 00:00:00",
                "lat": 12.0,
                "lon": 85.0,
                "wind_kt": 30.0,
                "pres_mb": 1000.0,
            },
            # Row 1: Duplicate timestamp (should be dropped)
            {
                "storm_id": "STORM_A",
                "time": "2020-05-16 00:00:00",
                "lat": 12.0,
                "lon": 85.0,
                "wind_kt": 30.0,
                "pres_mb": 1000.0,
            },
            # Row 2: Missing wind and pressure (1-step gap -> should be interpolated)
            {
                "storm_id": "STORM_A",
                "time": "2020-05-16 03:00:00",
                "lat": 12.5,
                "lon": 85.2,
                "wind_kt": None,
                "pres_mb": None,
            },
            # Row 3
            {
                "storm_id": "STORM_A",
                "time": "2020-05-16 06:00:00",
                "lat": 13.0,
                "lon": 85.4,
                "wind_kt": 40.0,
                "pres_mb": 990.0,
            },
            # Row 4: Physical outlier wind (-10 kt -> should be clipped to 0) & pressure (1050 mb -> clipped to 1030)
            {
                "storm_id": "STORM_A",
                "time": "2020-05-16 09:00:00",
                "lat": 13.5,
                "lon": 85.6,
                "wind_kt": -10.0,
                "pres_mb": 1050.0,
            },
        ]
    )

    cleaned_df, qc = clean_tracks(test_data)

    # Assertions
    assert len(cleaned_df) == 4
    assert qc["duplicates_dropped"] == 1
    assert qc["total_rows_interpolated"] >= 1
    assert qc["total_rows_clipped"] >= 1

    # Check interpolated value at step 03:00:00
    row_interp = cleaned_df.iloc[1]
    assert row_interp["qc_interpolated"] is True or row_interp["qc_interpolated"] == 1
    assert row_interp["wind_kt"] == 35.0  # Linear midpoint between 30 and 40
    assert row_interp["pres_mb"] == 995.0  # Linear midpoint between 1000 and 990

    # Check clipped values at step 09:00:00
    row_clipped = cleaned_df.iloc[3]
    assert row_clipped["qc_clipped"] is True or row_clipped["qc_clipped"] == 1
    assert row_clipped["wind_kt"] == 0.0
    assert row_clipped["pres_mb"] == 1030.0
