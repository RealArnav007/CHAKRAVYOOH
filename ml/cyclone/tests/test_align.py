"""Unit tests for spherical geometry, temporal track resampling, and multi-source colocalization."""

import math
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from ml.cyclone.ingest.satellite import load_image_index
from ml.cyclone.preprocess.align import resample_track
from ml.cyclone.preprocess.colocalize import build_samples
from ml.cyclone.preprocess.geo import (
    calculate_speed_and_heading,
    haversine_distance_km,
    haversine_distance_nm,
    initial_bearing_deg,
)


DATA_DIR = Path(__file__).resolve().parent.parent / "data"


# -----------------------------------------------------------------------------
# Spherical Geodesic Navigation Tests
# -----------------------------------------------------------------------------


def test_haversine_and_bearing_known_city_pairs():
    """Asserts haversine distance and initial bearing on standard benchmark coordinate pairs."""
    # Pair 1: New York to London
    ny_lat, ny_lon = 40.7128, -74.0060
    lon_lat, lon_lon = 51.5074, -0.1278

    dist_ny_lon = haversine_distance_km(ny_lat, ny_lon, lon_lat, lon_lon)
    bearing_ny_lon = initial_bearing_deg(ny_lat, ny_lon, lon_lat, lon_lon)

    assert 5550.0 < dist_ny_lon < 5600.0  # Approx 5570 km
    assert 48.0 < bearing_ny_lon < 54.0   # Approx 51 deg

    # Pair 2: Chennai to Kolkata (Bay of Bengal cyclone corridor)
    chn_lat, chn_lon = 13.0827, 80.2707
    kol_lat, kol_lon = 22.5726, 88.3639

    dist_chn_kol = haversine_distance_km(chn_lat, chn_lon, kol_lat, kol_lon)
    bearing_chn_kol = initial_bearing_deg(chn_lat, chn_lon, kol_lat, kol_lon)

    assert 1350.0 < dist_chn_kol < 1390.0  # Approx 1366 km
    assert 34.0 < bearing_chn_kol < 40.0   # Approx 37 deg

    # Pair 3: Cardinal Directions (Due North & Due East from Equator)
    dist_north = haversine_distance_km(0.0, 0.0, 1.0, 0.0)
    bearing_north = initial_bearing_deg(0.0, 0.0, 1.0, 0.0)
    assert 110.0 < dist_north < 112.0
    assert abs(bearing_north - 0.0) < 1e-4

    dist_east = haversine_distance_km(0.0, 0.0, 0.0, 1.0)
    bearing_east = initial_bearing_deg(0.0, 0.0, 0.0, 1.0)
    assert 110.0 < dist_east < 112.0
    assert abs(bearing_east - 90.0) < 1e-4


# -----------------------------------------------------------------------------
# Track Resampling & Motion Vector Tests
# -----------------------------------------------------------------------------


def test_resample_track_regular_spacing_and_motion():
    """Asserts resample_track produces exact equidistant time grids with computed velocity vectors."""
    # Create irregular raw track observations (every 3-9 hours)
    irregular_data = pd.DataFrame([
        {"storm_id": "TEST_STORM", "time": "2020-05-16 00:00:00", "lat": 10.0, "lon": 85.0, "wind_kt": 30.0, "pres_mb": 1000.0},
        {"storm_id": "TEST_STORM", "time": "2020-05-16 03:00:00", "lat": 10.5, "lon": 85.0, "wind_kt": 35.0, "pres_mb": 995.0},
        {"storm_id": "TEST_STORM", "time": "2020-05-16 12:00:00", "lat": 12.0, "lon": 85.0, "wind_kt": 50.0, "pres_mb": 980.0},
        {"storm_id": "TEST_STORM", "time": "2020-05-16 21:00:00", "lat": 13.5, "lon": 85.0, "wind_kt": 65.0, "pres_mb": 965.0},
    ])

    resampled_6h = resample_track(irregular_data, step_hours=6)

    assert not resampled_6h.empty
    assert (resampled_6h["storm_id"] == "TEST_STORM").all()

    # Verify regular 6-hour temporal intervals
    time_diffs = resampled_6h["time"].diff().dropna()
    for td in time_diffs:
        assert td.total_seconds() == 6 * 3600

    # Due North trajectory: heading should be approximately 0.0 deg
    headings = resampled_6h["heading_deg"]
    for hdg in headings:
        assert abs(hdg - 0.0) < 1.0 or abs(hdg - 360.0) < 1.0

    # Speeds should be positive and realistic
    speeds = resampled_6h["storm_speed_kt"]
    assert (speeds > 0).all()
    assert (speeds < 30.0).all()


# -----------------------------------------------------------------------------
# Multi-Source Colocalization Tests
# -----------------------------------------------------------------------------


def test_build_samples_missing_sources_resilience():
    """Asserts build_samples executes cleanly with safe fallbacks when imagery or ERA5 are missing."""
    track_data = pd.DataFrame([
        {"storm_id": "CYC_01", "time": "2020-05-16 00:00:00", "lat": 12.0, "lon": 85.0, "wind_kt": 35.0, "pres_mb": 995.0, "storm_speed_kt": 10.0, "heading_deg": 350.0},
        {"storm_id": "CYC_01", "time": "2020-05-16 06:00:00", "lat": 13.0, "lon": 84.8, "wind_kt": 45.0, "pres_mb": 988.0, "storm_speed_kt": 10.5, "heading_deg": 350.0},
        {"storm_id": "CYC_01", "time": "2020-05-16 12:00:00", "lat": 14.0, "lon": 84.6, "wind_kt": 60.0, "pres_mb": 975.0, "storm_speed_kt": 11.0, "heading_deg": 350.0},
    ])

    # Case 1: Neither imagery nor ERA5 provided
    samples = build_samples(track_df=track_data, image_index=None, era5_ds=None, history_steps=4)

    assert len(samples) == 3
    for s in samples:
        assert s["storm_id"] == "CYC_01"
        assert s["image_available"] is False
        assert s["image_path"] is None
        assert isinstance(s["env"], dict)
        assert math.isnan(s["env"]["sst_c"])  # Safe fallback NaN
        assert len(s["history"]) >= 1
        assert s["history"][-1]["t_offset_h"] == 0.0  # Current step


def test_build_samples_with_sample_image_index():
    """Asserts build_samples correctly pairs satellite image frames when available in index."""
    # Load available test satellite sample index
    img_index = load_image_index(data_dir=DATA_DIR)
    assert not img_index.empty

    # Create a track point matching a timestamp from the image index
    sample_time = img_index["time"].iloc[0]
    track_data = pd.DataFrame([
        {
            "storm_id": img_index["storm_id"].iloc[0],
            "time": sample_time,
            "lat": 15.0,
            "lon": 85.0,
            "wind_kt": 50.0,
            "pres_mb": 980.0,
            "storm_speed_kt": 8.0,
            "heading_deg": 320.0,
        }
    ])

    samples = build_samples(
        track_df=track_data,
        image_index=img_index,
        era5_ds=None,
        image_time_tolerance_minutes=90,
    )

    assert len(samples) == 1
    sample = samples[0]
    assert sample["image_available"] is True
    assert sample["image_path"] is not None
    assert Path(sample["image_path"]).exists()
