"""Temporal grid resampling and motion vector derivation for cyclone tracks."""

from __future__ import annotations

from typing import List, Optional
import numpy as np
import pandas as pd

from ml.cyclone.preprocess.geo import calculate_speed_and_heading


def resample_track(
    df: pd.DataFrame,
    step_hours: int = 6,
) -> pd.DataFrame:
    """Resamples irregular cyclone track observations onto a uniform temporal grid.

    For each storm:
    1. Generates an equidistant time series spaced by `step_hours` (e.g. 6h).
    2. Interpolates coordinates (`lat`, `lon`), `wind_kt`, and `pres_mb` using time-weighted interpolation.
    3. Calculates translation speed in knots and forward heading in degrees from consecutive points.
    4. Flags newly interpolated grid points with `qc_interpolated = True`.

    Args:
        df: Input DataFrame containing cleaned cyclone track points.
        step_hours: Target uniform sampling interval in hours (default: 6).

    Returns:
        pd.DataFrame aligned to uniform time grid with computed motion vectors.
    """
    if df.empty:
        return df.copy()

    working_df = df.copy()
    working_df["time"] = pd.to_datetime(working_df["time"], utc=True)
    working_df = working_df.sort_values(by=["storm_id", "time"]).reset_index(drop=True)

    resampled_storm_groups: List[pd.DataFrame] = []

    for storm_id, grp in working_df.groupby("storm_id", sort=False):
        if len(grp) == 0:
            continue

        grp_sorted = grp.drop_duplicates(subset=["time"]).sort_values(by="time").set_index("time")

        if len(grp_sorted) < 2:
            single_row = grp_sorted.reset_index()
            single_row["storm_speed_kt"] = 0.0
            single_row["storm_dir_deg"] = 0.0
            single_row["heading_deg"] = 0.0
            resampled_storm_groups.append(single_row)
            continue

        # Establish regular time range
        t_start = grp_sorted.index.min().floor(f"{step_hours}h")
        t_end = grp_sorted.index.max().ceil(f"{step_hours}h")
        target_grid = pd.date_range(start=t_start, end=t_end, freq=f"{step_hours}h", tz="UTC")

        # Combine original timestamps and target grid to preserve exact anchors
        union_index = grp_sorted.index.union(target_grid).sort_values()
        reindexed = grp_sorted.reindex(union_index)

        # Time-based linear interpolation for continuous numeric metrics
        for col in ["lat", "lon", "wind_kt", "pres_mb"]:
            if col in reindexed.columns:
                reindexed[col] = reindexed[col].interpolate(method="time")

        # Forward/backward fill metadata
        for meta_col in ["storm_id", "name", "nature", "basin"]:
            if meta_col in reindexed.columns:
                reindexed[meta_col] = reindexed[meta_col].ffill().bfill()
        if "storm_id" not in reindexed.columns or reindexed["storm_id"].isna().all():
            reindexed["storm_id"] = storm_id

        # Subselect strictly the target regular grid
        grid_df = reindexed.loc[target_grid].copy().reset_index().rename(columns={"index": "time"})

        # Drop any endpoints that fell outside interpolation boundary
        grid_df = grid_df.dropna(subset=["lat", "lon", "time"]).reset_index(drop=True)

        if grid_df.empty:
            continue

        # Flag newly created grid rows
        orig_times = set(grp_sorted.index)
        grid_df["qc_interpolated"] = grid_df["time"].apply(lambda t: t not in orig_times)
        if "qc_clipped" not in grid_df.columns:
            grid_df["qc_clipped"] = False

        # Calculate forward translation speed (kt) and heading (deg)
        speeds: List[float] = []
        headings: List[float] = []
        n_pts = len(grid_df)

        for i in range(n_pts):
            if i < n_pts - 1:
                p1 = grid_df.iloc[i]
                p2 = grid_df.iloc[i + 1]
                dt_h = (p2["time"] - p1["time"]).total_seconds() / 3600.0
                spd, hdg = calculate_speed_and_heading(p1["lat"], p1["lon"], p2["lat"], p2["lon"], dt_h)
            elif n_pts > 1:
                # Terminal point: inherit previous velocity vector
                spd, hdg = speeds[-1], headings[-1]
            else:
                spd, hdg = 0.0, 0.0

            speeds.append(spd)
            headings.append(hdg)

        grid_df["storm_speed_kt"] = speeds
        grid_df["storm_dir_deg"] = headings
        grid_df["heading_deg"] = headings  # Alias for consistency

        resampled_storm_groups.append(grid_df)

    if not resampled_storm_groups:
        return pd.DataFrame()

    out_df = pd.concat(resampled_storm_groups, ignore_index=True)
    return out_df


__all__ = ["resample_track"]
