"""Quality control, track cleaning, gap interpolation, and physical validation for cyclone tracks."""

from __future__ import annotations

from typing import Any

import pandas as pd

PHYSICAL_BOUNDS = {
    "lat": (-90.0, 90.0),
    "lon": (-180.0, 180.0),
    "wind_kt": (0.0, 200.0),  # Max observed tropical cyclone wind is ~185 kt (Patricia 2015)
    "pres_mb": (850.0, 1030.0),  # Min observed MSLP ~870 mb (Tip 1979)
    "storm_speed_kt": (0.0, 70.0),
    "storm_dir_deg": (0.0, 360.0),
}


def clean_tracks(
    df: pd.DataFrame,
    max_interp_gap: int = 2,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Performs rigorous quality control, sorting, deduplication, and short-gap interpolation on cyclone tracks.

    Steps:
    1. Sorts chronologically per storm (`['storm_id', 'time']`).
    2. Drops duplicate timestamps within the same storm trajectory (keeping the first occurrence).
    3. Interpolates short missing gaps (<= max_interp_gap steps) linearly in position, wind, and pressure.
    4. Flags interpolated records with `qc_interpolated = True`.
    5. Enforces physical boundary clipping on wind, pressure, and coordinates, flagging clipped rows with `qc_clipped = True`.
    6. Produces a comprehensive QC report dictionary.

    Args:
        df: Input raw track DataFrame.
        max_interp_gap: Maximum consecutive missing steps to interpolate (default: 2 steps / ~6 hours).

    Returns:
        Tuple of (cleaned_df, qc_report_dict)
    """
    if df.empty:
        empty_df = df.copy()
        empty_df["qc_interpolated"] = False
        empty_df["qc_clipped"] = False
        return empty_df, {"total_input_rows": 0, "total_output_rows": 0}

    initial_count = len(df)
    working_df = df.copy()

    # Ensure standardized types
    if "time" in working_df.columns:
        working_df["time"] = pd.to_datetime(working_df["time"], utc=True)

    # 1. Sort by storm and time
    sort_cols = [col for col in ["storm_id", "time"] if col in working_df.columns]
    if sort_cols:
        working_df = working_df.sort_values(by=sort_cols).reset_index(drop=True)

    # 2. Deduplicate timestamps per storm
    dup_mask = working_df.duplicated(subset=["storm_id", "time"], keep="first")
    duplicates_dropped = int(dup_mask.sum())
    working_df = working_df[~dup_mask].copy().reset_index(drop=True)

    # Initialize QC tracking flags
    working_df["qc_interpolated"] = False
    working_df["qc_clipped"] = False

    interpolated_counts: dict[str, int] = {}
    clipped_counts: dict[str, int] = {}

    numeric_interp_cols = [
        c for c in ["lat", "lon", "wind_kt", "pres_mb"] if c in working_df.columns
    ]

    # 3. Per-storm group interpolation for short gaps
    cleaned_groups: list[pd.DataFrame] = []

    for storm_id, group in working_df.groupby("storm_id", sort=False):
        grp = group.copy()

        for col in numeric_interp_cols:
            is_na = grp[col].isna()
            if is_na.any():
                # Interpolate linearly with gap limit
                interp_series = grp[col].interpolate(
                    method="linear", limit=max_interp_gap, limit_direction="forward"
                )
                filled_mask = is_na & interp_series.notna()
                count_filled = int(filled_mask.sum())
                interpolated_counts[col] = interpolated_counts.get(col, 0) + count_filled

                # Flag rows where interpolation occurred
                if count_filled > 0:
                    grp.loc[filled_mask, "qc_interpolated"] = True
                grp[col] = interp_series

        cleaned_groups.append(grp)

    working_df = pd.concat(cleaned_groups, ignore_index=True)

    # 4. Physical boundary validation and clipping
    for col, (lower_bound, upper_bound) in PHYSICAL_BOUNDS.items():
        if col in working_df.columns:
            val_series = working_df[col]
            out_of_bounds = (val_series < lower_bound) | (val_series > upper_bound)
            count_oob = int(out_of_bounds.sum())
            if count_oob > 0:
                clipped_counts[col] = count_oob
                working_df.loc[out_of_bounds, "qc_clipped"] = True
                working_df[col] = working_df[col].clip(lower=lower_bound, upper=upper_bound)

    # 5. Drop any remaining rows that still have missing position after interpolation
    pos_na_mask = working_df["lat"].isna() | working_df["lon"].isna()
    unresolvable_pos_dropped = int(pos_na_mask.sum())
    working_df = working_df[~pos_na_mask].reset_index(drop=True)

    final_count = len(working_df)

    qc_report = {
        "total_input_rows": initial_count,
        "total_output_rows": final_count,
        "duplicates_dropped": duplicates_dropped,
        "unresolvable_positions_dropped": unresolvable_pos_dropped,
        "interpolated_values_by_column": interpolated_counts,
        "total_rows_interpolated": int(working_df["qc_interpolated"].sum()),
        "clipped_values_by_column": clipped_counts,
        "total_rows_clipped": int(working_df["qc_clipped"].sum()),
    }

    return working_df, qc_report


__all__ = ["clean_tracks", "PHYSICAL_BOUNDS"]
