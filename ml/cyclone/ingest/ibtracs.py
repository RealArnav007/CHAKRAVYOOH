"""Typed loader for IBTrACS best-track historical storm archives."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Union
import pandas as pd

from ml.cyclone.config import load_config


STANDARD_TRACK_COLUMNS = [
    "storm_id",
    "time",
    "lat",
    "lon",
    "wind_kt",
    "pres_mb",
    "storm_speed_kt",
    "storm_dir_deg",
    "nature",
    "basin",
]


def resolve_ibtracs_path(override_path: Optional[Union[str, Path]] = None) -> Path:
    """Resolves IBTrACS file location from explicit path, config, or fallback sample files."""
    if override_path:
        p = Path(override_path)
        if p.exists():
            return p

    cfg = load_config()
    cfg_path = Path(cfg.data.paths.ibtracs_csv)
    if cfg_path.exists():
        return cfg_path

    # Check for parquet in same directory
    parquet_candidate = cfg_path.parent / "ibtracs_north_indian_ocean.parquet"
    if parquet_candidate.exists():
        return parquet_candidate

    # Fallback to sample dataset
    sample_candidate = cfg_path.parent / "ibtracs_sample.csv"
    if sample_candidate.exists():
        return sample_candidate

    # Root-relative sample fallback
    root_sample = Path("ml/cyclone/data/ibtracs/ibtracs_sample.csv")
    if root_sample.exists():
        return root_sample

    raise FileNotFoundError(
        f"IBTrACS best-track file not found at {override_path or cfg_path}. "
        "Run `python -m ml.cyclone.ingest.download_ibtracs` to download the dataset."
    )


def load_tracks(file_path: Optional[Union[str, Path]] = None) -> pd.DataFrame:
    """Loads and standardizes IBTrACS cyclone track dataset into a clean DataFrame.

    Coalescing Strategy:
    - `wind_kt`: Prioritizes official WMO agency reports (e.g. IMD for NIO). If WMO_WIND is NaN
      or <= 0, falls back to USA_WIND (JTWC/NHC).
    - `pres_mb`: Prioritizes WMO_PRES. If NaN or <= 0, falls back to USA_PRES.
    - Rows with missing geographic coordinates (`lat` or `lon`) are discarded.

    Returns:
        pd.DataFrame with columns: [storm_id, time, lat, lon, wind_kt, pres_mb,
                                    storm_speed_kt, storm_dir_deg, nature, basin]
    """
    path = resolve_ibtracs_path(file_path)

    if path.suffix == ".parquet":
        raw_df = pd.read_parquet(path)
    else:
        # Check if row 1 contains unit headers
        first_rows = pd.read_csv(path, nrows=2)
        if len(first_rows) > 0 and any("kts" in str(v).lower() or "mb" in str(v).lower() for v in first_rows.iloc[0]):
            raw_df = pd.read_csv(path, skiprows=[1], low_memory=False)
        else:
            raw_df = pd.read_csv(path, low_memory=False)

    df = pd.DataFrame()

    # Storm ID & Name
    df["storm_id"] = raw_df["SID"].astype(str).str.strip() if "SID" in raw_df.columns else raw_df.get("storm_id", "UNKNOWN").astype(str)

    # Time parsing with strict UTC conversion
    time_col = "ISO_TIME" if "ISO_TIME" in raw_df.columns else "time"
    df["time"] = pd.to_datetime(raw_df[time_col], utc=True, errors="coerce")

    # Coordinates
    lat_col = "LAT" if "LAT" in raw_df.columns else "lat"
    lon_col = "LON" if "LON" in raw_df.columns else "lon"
    df["lat"] = pd.to_numeric(raw_df[lat_col], errors="coerce")
    df["lon"] = pd.to_numeric(raw_df[lon_col], errors="coerce")

    # Coalesce wind (WMO prioritized over USA)
    if "WMO_WIND" in raw_df.columns and "USA_WIND" in raw_df.columns:
        wmo_wind = pd.to_numeric(raw_df["WMO_WIND"], errors="coerce")
        usa_wind = pd.to_numeric(raw_df["USA_WIND"], errors="coerce")
        # Replace non-positive values with NaN before coalesce
        wmo_wind = wmo_wind.where(wmo_wind > 0)
        usa_wind = usa_wind.where(usa_wind > 0)
        df["wind_kt"] = wmo_wind.combine_first(usa_wind)
    elif "wind_kt" in raw_df.columns:
        df["wind_kt"] = pd.to_numeric(raw_df["wind_kt"], errors="coerce")
    elif "USA_WIND" in raw_df.columns:
        df["wind_kt"] = pd.to_numeric(raw_df["USA_WIND"], errors="coerce")
    else:
        df["wind_kt"] = pd.Series(float("nan"), index=raw_df.index)

    # Coalesce pressure (WMO prioritized over USA)
    if "WMO_PRES" in raw_df.columns and "USA_PRES" in raw_df.columns:
        wmo_pres = pd.to_numeric(raw_df["WMO_PRES"], errors="coerce")
        usa_pres = pd.to_numeric(raw_df["USA_PRES"], errors="coerce")
        wmo_pres = wmo_pres.where(wmo_pres > 800)
        usa_pres = usa_pres.where(usa_pres > 800)
        df["pres_mb"] = wmo_pres.combine_first(usa_pres)
    elif "pres_mb" in raw_df.columns:
        df["pres_mb"] = pd.to_numeric(raw_df["pres_mb"], errors="coerce")
    elif "USA_PRES" in raw_df.columns:
        df["pres_mb"] = pd.to_numeric(raw_df["USA_PRES"], errors="coerce")
    else:
        df["pres_mb"] = pd.Series(float("nan"), index=raw_df.index)

    # Motion features
    speed_col = "STORM_SPEED" if "STORM_SPEED" in raw_df.columns else "storm_speed_kt"
    dir_col = "STORM_DIR" if "STORM_DIR" in raw_df.columns else "storm_dir_deg"
    df["storm_speed_kt"] = pd.to_numeric(raw_df.get(speed_col), errors="coerce")
    df["storm_dir_deg"] = pd.to_numeric(raw_df.get(dir_col), errors="coerce")

    # Metadata categories
    nature_col = "NATURE" if "NATURE" in raw_df.columns else "nature"
    basin_col = "BASIN" if "BASIN" in raw_df.columns else "basin"
    df["nature"] = raw_df.get(nature_col, "TS").astype(str).str.strip()
    df["basin"] = raw_df.get(basin_col, "NI").astype(str).str.strip()

    # Drop records without valid position coordinates or timestamps
    df = df.dropna(subset=["lat", "lon", "time"])

    # Sort chronologically per storm
    df = df.sort_values(by=["storm_id", "time"]).reset_index(drop=True)

    return df[STANDARD_TRACK_COLUMNS]


def get_storm(storm_id: str, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """Retrieves the chronological track for a specific storm ID.

    Args:
        storm_id: Unique storm identifier (e.g. '2020136N10087' or 'CYC-2020-BAY-001')
        df: Optional pre-loaded tracks DataFrame.

    Returns:
        pd.DataFrame containing the storm's track records.
    """
    if df is None:
        df = load_tracks()

    # Search by exact storm_id match or case-insensitive match
    matches = df[df["storm_id"].str.upper() == storm_id.strip().upper()]
    if matches.empty:
        # Fallback partial search
        matches = df[df["storm_id"].str.contains(storm_id.strip(), case=False, regex=False)]

    return matches.sort_values(by="time").reset_index(drop=True)


__all__ = ["load_tracks", "get_storm", "STANDARD_TRACK_COLUMNS", "resolve_ibtracs_path"]
