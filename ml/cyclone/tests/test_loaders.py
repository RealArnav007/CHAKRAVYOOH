"""Unit tests for typed data ingestion loaders and registry factory."""

import math
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from ml.cyclone.ingest.era5 import STANDARD_ENV_VARIABLES, open_era5, sample_env
from ml.cyclone.ingest.ibtracs import STANDARD_TRACK_COLUMNS, get_storm, load_tracks
from ml.cyclone.ingest.registry import get_loader, list_sources, load_dataset
from ml.cyclone.ingest.satellite import SATELLITE_INDEX_COLUMNS, load_image_index, read_image


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
IBTRACS_SAMPLE = DATA_DIR / "ibtracs" / "ibtracs_sample.csv"
DRIVENDATA_SAMPLE = DATA_DIR / "drivendata" / "drivendata_sample.csv"
DIGITAL_TYPHOON_SAMPLE = DATA_DIR / "digital_typhoon" / "digital_typhoon_sample.csv"


# -----------------------------------------------------------------------------
# IBTrACS Loader Tests
# -----------------------------------------------------------------------------


def test_ibtracs_sample_loader():
    """Asserts IBTrACS loader parses sample data into standardized columns and dtypes."""
    assert IBTRACS_SAMPLE.is_file(), f"Sample file missing at {IBTRACS_SAMPLE}"

    df = load_tracks(file_path=IBTRACS_SAMPLE)
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert list(df.columns) == STANDARD_TRACK_COLUMNS

    # Dtype and integrity assertions
    assert pd.api.types.is_datetime64_any_dtype(df["time"])
    assert pd.api.types.is_float_dtype(df["lat"])
    assert pd.api.types.is_float_dtype(df["lon"])
    assert pd.api.types.is_float_dtype(df["wind_kt"])
    assert pd.api.types.is_float_dtype(df["pres_mb"])

    # Coordinate ranges
    assert df["lat"].between(-90, 90).all()
    assert df["lon"].between(-180, 180).all()

    # Test get_storm helper
    first_storm_id = df["storm_id"].iloc[0]
    storm_df = get_storm(first_storm_id, df=df)
    assert not storm_df.empty
    assert (storm_df["storm_id"] == first_storm_id).all()
    assert storm_df["time"].is_monotonic_increasing


# -----------------------------------------------------------------------------
# Satellite Loader Tests
# -----------------------------------------------------------------------------


def test_satellite_index_loaders():
    """Asserts satellite image index loaders return expected columns for Digital Typhoon and DrivenData."""
    dt_df = load_image_index(source="digital_typhoon", data_dir=DATA_DIR)
    assert list(dt_df.columns) == SATELLITE_INDEX_COLUMNS
    assert not dt_df.empty
    assert (dt_df["source"] == "digital_typhoon").all()

    dd_df = load_image_index(source="drivendata", data_dir=DATA_DIR)
    assert list(dd_df.columns) == SATELLITE_INDEX_COLUMNS
    assert not dd_df.empty
    assert (dd_df["source"] == "drivendata").all()

    all_df = load_image_index(data_dir=DATA_DIR)
    assert len(all_df) == len(dt_df) + len(dd_df)


def test_read_image_lazy_normalization():
    """Asserts lazy image reader outputs float32 (224, 224) array normalized to [0, 1]."""
    dt_df = load_image_index(source="digital_typhoon", data_dir=DATA_DIR)
    assert not dt_df.empty
    first_img_path = dt_df["image_path"].iloc[0]

    img = read_image(first_img_path, target_size=(224, 224))
    assert isinstance(img, np.ndarray)
    assert img.shape == (224, 224)
    assert img.dtype == np.float32
    assert 0.0 <= img.min() <= img.max() <= 1.0


# -----------------------------------------------------------------------------
# ERA5 Safe Fallback Tests
# -----------------------------------------------------------------------------


def test_era5_missing_safe_fallback():
    """Asserts ERA5 loader returns NaNs and never crashes on missing dataset or out-of-bounds queries."""
    ds = open_era5("non_existent_path.nc")
    assert ds is None

    env = sample_env(ds=ds, time="2020-05-18T12:00:00Z", lat=16.5, lon=87.2)
    assert isinstance(env, dict)
    for var in STANDARD_ENV_VARIABLES:
        assert var in env
        assert math.isnan(env[var])


# -----------------------------------------------------------------------------
# Registry Factory Tests
# -----------------------------------------------------------------------------


def test_registry_factory():
    """Asserts source registry lists all sources and provides correct loader dispatch."""
    sources = list_sources()
    for expected in ["ibtracs", "satellite", "drivendata", "digital_typhoon", "era5"]:
        assert expected in sources

    # Test get_loader
    ib_loader = get_loader("ibtracs")
    assert "load" in ib_loader
    assert callable(ib_loader["load"])

    # Test load_dataset convenience wrapper
    df = load_dataset("ibtracs", file_path=IBTRACS_SAMPLE)
    assert isinstance(df, pd.DataFrame)
    assert not df.empty

    # Test invalid source raises KeyError
    with pytest.raises(KeyError):
        get_loader("non_existent_source")
