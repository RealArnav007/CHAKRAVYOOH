"""Motion dynamics, velocity vectors, and intensity rate-of-change feature extractor."""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from ml.cyclone.preprocess.geo import initial_bearing_deg


MOTION_FEATURE_NAMES: List[str] = [
    "current_speed_kt",
    "current_heading_deg",
    "heading_sin",
    "heading_cos",
    "dv_6h",
    "dv_12h",
    "dv_24h",
    "dp_6h",
    "dp_12h",
    "dp_24h",
    "acceleration_kt_per_h",
    "curvature_deg_per_h",
    "lat",
    "lon",
    "coriolis_param",
    "days_since_genesis",
]

# Earth rotation rate Omega in rad/s
EARTH_OMEGA = 7.2921159e-5


def _find_history_point_at_offset(
    history: List[Dict[str, Any]],
    target_offset_h: float,
    tolerance_h: float = 3.5,
) -> Optional[Dict[str, Any]]:
    """Finds the closest history point within target offset window (e.g. -6h +/- 3.5h)."""
    best_pt = None
    min_err = float("inf")
    for pt in history:
        offset = float(pt.get("t_offset_h", 0.0))
        err = abs(offset - target_offset_h)
        if err <= tolerance_h and err < min_err:
            min_err = err
            best_pt = pt
    return best_pt


def extract_motion_features(sample: Dict[str, Any]) -> np.ndarray:
    """Extracts a fixed-order 16-dimensional motion & intensity dynamics feature vector from a sample.

    Features:
    1. current_speed_kt: Translation speed in knots.
    2. current_heading_deg: Heading in degrees [0, 360).
    3. heading_sin: sin(heading in radians).
    4. heading_cos: cos(heading in radians).
    5. dv_6h: 6-hour change in maximum sustained wind speed (kt).
    6. dv_12h: 12-hour change in maximum sustained wind speed (kt).
    7. dv_24h: 24-hour change in maximum sustained wind speed (kt).
    8. dp_6h: 6-hour change in central pressure (mb).
    9. dp_12h: 12-hour change in central pressure (mb).
    10. dp_24h: 24-hour change in central pressure (mb).
    11. acceleration_kt_per_h: Acceleration in speed over past 6 hours (kt/h).
    12. curvature_deg_per_h: Track curvature / angular velocity over past 6 hours (deg/h).
    13. lat: Current latitude in decimal degrees.
    14. lon: Current longitude in decimal degrees.
    15. coriolis_param: Planetary vorticity parameter 2 * Omega * sin(lat) * 10^4.
    16. days_since_genesis: Elapsed time in days from storm genesis/first history point.

    Args:
        sample: Colocalized sample dictionary containing 'lat', 'lon', 'wind_kt', 'pres_mb',
                'storm_speed_kt', 'heading_deg', and 'history'.

    Returns:
        np.ndarray of shape (16,) and dtype np.float32.
    """
    lat = float(sample.get("lat", 0.0))
    lon = float(sample.get("lon", 0.0))
    wind_kt = float(sample.get("wind_kt", 0.0))
    pres_mb = float(sample.get("pres_mb", 1010.0))
    speed_kt = float(sample.get("storm_speed_kt", 0.0))
    heading_deg = float(sample.get("heading_deg", sample.get("storm_dir_deg", 0.0)))

    # Heading trigonometry
    rad = math.radians(heading_deg)
    heading_sin = math.sin(rad)
    heading_cos = math.cos(rad)

    # History lookups for delta wind and delta pressure
    history = sample.get("history", [])

    pt_minus_6h = _find_history_point_at_offset(history, -6.0)
    pt_minus_12h = _find_history_point_at_offset(history, -12.0)
    pt_minus_24h = _find_history_point_at_offset(history, -24.0)

    # Delta V (wind)
    dv_6h = (wind_kt - float(pt_minus_6h["wind_kt"])) if pt_minus_6h else 0.0
    dv_12h = (wind_kt - float(pt_minus_12h["wind_kt"])) if pt_minus_12h else (dv_6h * 2.0)
    dv_24h = (wind_kt - float(pt_minus_24h["wind_kt"])) if pt_minus_24h else (dv_12h * 2.0)

    # Delta P (pressure)
    dp_6h = (pres_mb - float(pt_minus_6h["pres_mb"])) if pt_minus_6h else 0.0
    dp_12h = (pres_mb - float(pt_minus_12h["pres_mb"])) if pt_minus_12h else (dp_6h * 2.0)
    dp_24h = (pres_mb - float(pt_minus_24h["pres_mb"])) if pt_minus_24h else (dp_12h * 2.0)

    # Acceleration and curvature over past 6h
    if pt_minus_6h:
        dt_h = abs(float(pt_minus_6h.get("t_offset_h", -6.0)))
        dt_h = max(dt_h, 1.0)
        past_speed = float(pt_minus_6h.get("speed_kt", speed_kt))
        past_heading = float(pt_minus_6h.get("heading_deg", heading_deg))

        accel = (speed_kt - past_speed) / dt_h

        # Angular difference wrapped to [-180, 180]
        heading_diff = (heading_deg - past_heading + 180.0) % 360.0 - 180.0
        curvature = heading_diff / dt_h
    else:
        accel = 0.0
        curvature = 0.0

    # Coriolis parameter f = 2 * Omega * sin(lat) scaled by 10^4 for numerical conditioning
    coriolis_param = 2.0 * EARTH_OMEGA * math.sin(math.radians(lat)) * 1e4

    # Days since genesis
    if history:
        earliest_offset = min(float(pt.get("t_offset_h", 0.0)) for pt in history)
        days_since_genesis = abs(earliest_offset) / 24.0
    else:
        days_since_genesis = 0.0

    features = [
        speed_kt,
        heading_deg,
        heading_sin,
        heading_cos,
        dv_6h,
        dv_12h,
        dv_24h,
        dp_6h,
        dp_12h,
        dp_24h,
        accel,
        curvature,
        lat,
        lon,
        coriolis_param,
        days_since_genesis,
    ]

    return np.array(features, dtype=np.float32)


__all__ = ["extract_motion_features", "MOTION_FEATURE_NAMES"]
