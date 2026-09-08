"""Multi-source spatio-temporal colocalization engine linking tracks, imagery, and environmental fields."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd

from ml.cyclone.ingest.era5 import sample_env


def build_samples(
    track_df: pd.DataFrame,
    image_index: Optional[pd.DataFrame] = None,
    era5_ds: Optional[Any] = None,
    history_steps: int = 8,
    image_time_tolerance_minutes: int = 90,
) -> List[Dict[str, Any]]:
    """Colocalizes track coordinates with nearest satellite images, ERA5 environment, and historical motion.

    For every observation point on the track grid:
    1. Associates the nearest satellite image frame within the time tolerance window (+/- 90 min).
    2. Interpolates and samples ERA5 atmospheric variables (SST, shear, RH, vorticity, MSLP, 10m wind).
    3. Attaches an N-step historical trajectory sequence.
    4. Emits a clean dictionary representation without dropping points when modalities are missing.

    Args:
        track_df: Resampled regular track DataFrame with coordinates and motion vectors.
        image_index: Optional DataFrame of satellite image metadata [image_path, time, lat, lon, storm_id, ...].
        era5_ds: Optional xarray Dataset of ERA5 reanalysis fields.
        history_steps: Number of past track points to include in the history window (default: 8).
        image_time_tolerance_minutes: Maximum temporal discrepancy to pair an image (default: 90 min).

    Returns:
        List of colocalized raw sample dictionaries.
    """
    if track_df.empty:
        return []

    working_track = track_df.copy()
    working_track["time"] = pd.to_datetime(working_track["time"], utc=True)
    working_track = working_track.sort_values(by=["storm_id", "time"]).reset_index(drop=True)

    # Pre-process image index for fast temporal lookup
    has_images = image_index is not None and not image_index.empty
    if has_images:
        img_df = image_index.copy()
        img_df["time"] = pd.to_datetime(img_df["time"], utc=True)
        img_df = img_df.sort_values(by="time").reset_index(drop=True)
    else:
        img_df = pd.DataFrame()

    samples: List[Dict[str, Any]] = []

    for storm_id, storm_group in working_track.groupby("storm_id", sort=False):
        storm_pts = storm_group.reset_index(drop=True)
        n_pts = len(storm_pts)

        # Filter candidate images for this specific storm if storm_id matching exists
        if has_images:
            if "storm_id" in img_df.columns and (img_df["storm_id"] == storm_id).any():
                storm_images = img_df[img_df["storm_id"] == storm_id].reset_index(drop=True)
            else:
                storm_images = img_df
        else:
            storm_images = pd.DataFrame()

        for idx in range(n_pts):
            row = storm_pts.iloc[idx]
            current_time = row["time"]
            lat = float(row["lat"])
            lon = float(row["lon"])
            wind_kt = float(row.get("wind_kt", 0.0))
            pres_mb = float(row.get("pres_mb", 1010.0))
            speed_kt = float(row.get("storm_speed_kt", 0.0))
            heading_deg = float(row.get("heading_deg", row.get("storm_dir_deg", 0.0)))

            # (a) Associate nearest satellite image within tolerance
            matched_image_path: Optional[str] = None
            image_available = False

            if not storm_images.empty:
                time_diffs = (storm_images["time"] - current_time).abs()
                min_diff = time_diffs.min()
                min_diff_minutes = min_diff.total_seconds() / 60.0

                if min_diff_minutes <= image_time_tolerance_minutes:
                    closest_row = storm_images.iloc[time_diffs.idxmin()]
                    matched_image_path = str(closest_row["image_path"])
                    image_available = True

            # (b) Sample ERA5 environmental scalars (safe NaN fallback if missing)
            env_scalars = sample_env(
                ds=era5_ds,
                time=current_time,
                lat=lat,
                lon=lon,
            )

            # (c) Build historical trajectory window
            start_hist_idx = max(0, idx - history_steps + 1)
            hist_rows = storm_pts.iloc[start_hist_idx : idx + 1]

            history: List[Dict[str, Any]] = []
            for _, h_row in hist_rows.iterrows():
                t_offset_h = (h_row["time"] - current_time).total_seconds() / 3600.0
                history.append({
                    "t_offset_h": round(t_offset_h, 1),
                    "lat": round(float(h_row["lat"]), 4),
                    "lon": round(float(h_row["lon"]), 4),
                    "wind_kt": round(float(h_row.get("wind_kt", 0.0)), 1),
                    "pres_mb": round(float(h_row.get("pres_mb", 1010.0)), 1),
                    "speed_kt": round(float(h_row.get("storm_speed_kt", 0.0)), 2),
                    "heading_deg": round(float(h_row.get("heading_deg", h_row.get("storm_dir_deg", 0.0))), 1),
                })

            # (d) Build future trajectory lookup for forecast horizons
            future_lookup: Dict[int, Tuple[float, float]] = {}
            for f_idx in range(idx + 1, n_pts):
                f_row = storm_pts.iloc[f_idx]
                delta_h = int(round((f_row["time"] - current_time).total_seconds() / 3600.0))
                if delta_h in [6, 12, 24, 48, 72]:
                    future_lookup[delta_h] = (round(float(f_row["lat"]), 4), round(float(f_row["lon"]), 4))

            sample_dict = {
                "storm_id": str(storm_id),
                "time": current_time.isoformat(),
                "lat": round(lat, 4),
                "lon": round(lon, 4),
                "wind_kt": round(wind_kt, 1),
                "pres_mb": round(pres_mb, 1),
                "storm_speed_kt": round(speed_kt, 2),
                "heading_deg": round(heading_deg, 1),
                "image_path": matched_image_path,
                "image_available": image_available,
                "env": env_scalars,
                "history": history,
                "future_lookup": future_lookup,
            }

            samples.append(sample_dict)

    return samples


__all__ = ["build_samples"]
