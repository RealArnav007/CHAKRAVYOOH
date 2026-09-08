"""Typed loader and spatio-temporal environmental sampler for ERA5 reanalysis via xarray."""

from __future__ import annotations

import math
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

try:
    import xarray as xr
except ImportError:
    xr = None


STANDARD_ENV_VARIABLES = [
    "sst_c",
    "shear_ms",
    "rh500",
    "vort850",
    "mslp_mb",
    "wind10m_ms",
]


def _get_nan_env_dict() -> dict[str, float]:
    """Returns a standardized dictionary of NaN environmental parameters."""
    return {var: float("nan") for var in STANDARD_ENV_VARIABLES}


def open_era5(path: str | Path) -> Any | None:
    """Safely opens an ERA5 NetCDF file with xarray.

    Returns:
        xr.Dataset if valid NetCDF file exists, else None.
    """
    if xr is None:
        return None

    p = Path(path)
    if not p.is_file():
        return None

    try:
        ds = xr.open_dataset(p)
        return ds
    except Exception as exc:
        print(f"[ERA5] Warning: could not open NetCDF at {p}: {exc}")
        return None


def sample_env(
    ds: Any | None,
    time: datetime | str | pd.Timestamp,
    lat: float,
    lon: float,
) -> dict[str, float]:
    """Samples environmental atmospheric parameters at a specific (time, lat, lon) point.

    Uses spatial bilinear / nearest interpolation and nearest temporal selection.
    Returns NaNs (never raises) when out of coverage or when dataset is unavailable.

    Returns:
        Dict with keys: sst_c, shear_ms, rh500, vort850, mslp_mb, wind10m_ms
    """
    if ds is None or xr is None:
        return _get_nan_env_dict()

    try:
        # Standardize timestamp
        target_time = pd.to_datetime(time, utc=True).tz_localize(None)

        # Determine latitude / longitude coordinate names
        lat_name = (
            "latitude" if "latitude" in ds.coords else ("lat" if "lat" in ds.coords else None)
        )
        lon_name = (
            "longitude" if "longitude" in ds.coords else ("lon" if "lon" in ds.coords else None)
        )
        time_name = (
            "time" if "time" in ds.coords else ("valid_time" if "valid_time" in ds.coords else None)
        )

        if not lat_name or not lon_name or not time_name:
            return _get_nan_env_dict()

        # Handle 0-360 vs -180-180 longitude conventions
        ds_lons = ds[lon_name].values
        query_lon = lon
        if np.nanmin(ds_lons) >= 0 and query_lon < 0:
            query_lon = query_lon + 360.0

        # Select nearest in time
        slice_t = ds.sel({time_name: target_time}, method="nearest")

        # Interpolate in space
        try:
            point_ds = slice_t.interp({lat_name: lat, lon_name: query_lon}, method="linear")
        except Exception:
            point_ds = slice_t.sel({lat_name: lat, lon_name: query_lon}, method="nearest")

        result = {}

        # 1. SST (K -> Celsius)
        sst_val = float("nan")
        for sst_key in ["sst", "sea_surface_temperature"]:
            if sst_key in point_ds:
                val = float(point_ds[sst_key].values)
                if not math.isnan(val) and val > 100:
                    sst_val = val - 273.15
                break
        result["sst_c"] = round(sst_val, 2) if not math.isnan(sst_val) else float("nan")

        # 2. Vertical Wind Shear (850 hPa vs 200 hPa vector difference magnitude in m/s)
        shear_val = float("nan")
        if "u" in point_ds and "v" in point_ds and "level" in point_ds["u"].dims:
            try:
                u200 = float(point_ds["u"].sel(level=200, method="nearest").values)
                u850 = float(point_ds["u"].sel(level=850, method="nearest").values)
                v200 = float(point_ds["v"].sel(level=200, method="nearest").values)
                v850 = float(point_ds["v"].sel(level=850, method="nearest").values)
                shear_val = math.sqrt((u200 - u850) ** 2 + (v200 - v850) ** 2)
            except Exception:
                pass
        result["shear_ms"] = round(shear_val, 2) if not math.isnan(shear_val) else float("nan")

        # 3. Relative Humidity at 500 hPa (%)
        rh_val = float("nan")
        for rh_key in ["r", "relative_humidity"]:
            if rh_key in point_ds:
                try:
                    if "level" in point_ds[rh_key].dims:
                        rh_val = float(point_ds[rh_key].sel(level=500, method="nearest").values)
                    else:
                        rh_val = float(point_ds[rh_key].values)
                except Exception:
                    pass
                break
        result["rh500"] = round(rh_val, 1) if not math.isnan(rh_val) else float("nan")

        # 4. Vorticity at 850 hPa (s^-1)
        vort_val = float("nan")
        for vo_key in ["vo", "vorticity", "relative_vorticity"]:
            if vo_key in point_ds:
                try:
                    if "level" in point_ds[vo_key].dims:
                        vort_val = float(point_ds[vo_key].sel(level=850, method="nearest").values)
                    else:
                        vort_val = float(point_ds[vo_key].values)
                except Exception:
                    pass
                break
        result["vort850"] = vort_val if not math.isnan(vort_val) else float("nan")

        # 5. MSLP (Pa -> hPa/mb)
        mslp_val = float("nan")
        for mslp_key in ["msl", "mean_sea_level_pressure"]:
            if mslp_key in point_ds:
                val = float(point_ds[mslp_key].values)
                if not math.isnan(val):
                    mslp_val = val / 100.0 if val > 2000 else val
                break
        result["mslp_mb"] = round(mslp_val, 1) if not math.isnan(mslp_val) else float("nan")

        # 6. 10m Wind Speed (m/s)
        wind10_val = float("nan")
        if "u10" in point_ds and "v10" in point_ds:
            u10 = float(point_ds["u10"].values)
            v10 = float(point_ds["v10"].values)
            wind10_val = math.sqrt(u10**2 + v10**2)
        elif "10m_u_component_of_wind" in point_ds and "10m_v_component_of_wind" in point_ds:
            u10 = float(point_ds["10m_u_component_of_wind"].values)
            v10 = float(point_ds["10m_v_component_of_wind"].values)
            wind10_val = math.sqrt(u10**2 + v10**2)
        result["wind10m_ms"] = round(wind10_val, 2) if not math.isnan(wind10_val) else float("nan")

        return result

    except Exception:
        return _get_nan_env_dict()


__all__ = ["open_era5", "sample_env", "STANDARD_ENV_VARIABLES"]
