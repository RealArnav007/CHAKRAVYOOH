"""Tier-0 Deterministic Intensity Estimator mapping observed parameters to IMD scale."""

from __future__ import annotations

from typing import Any

import numpy as np

from ml.cyclone.preprocess.scales import wind_kt_to_imd_level
from ml.cyclone.schema.models import IntensityPayload

IMD_BOUNDARIES = [17.0, 28.0, 34.0, 48.0, 64.0, 90.0, 120.0]


def intensity(sample: dict[str, Any]) -> dict[str, Any]:
    """Maps observed surface wind and central pressure to the IMD category with calibrated confidence.

    Args:
        sample: Sample dictionary with 'wind_kt' and 'pres_mb'.

    Returns:
        Dict conforming to IntensityPayload: {
            "level": IntensityLevelEnum,
            "scale": "IMD",
            "max_wind_kt": float,
            "min_pressure_mb": float,
            "confidence": float
        }
    """
    raw_wind = sample.get("wind_kt", 25.0)
    raw_pres = sample.get("pres_mb", 1005.0)
    w_val = 25.0 if (raw_wind is None or np.isnan(float(raw_wind))) else float(raw_wind)
    p_val = 1005.0 if (raw_pres is None or np.isnan(float(raw_pres))) else float(raw_pres)

    wind_kt = round(float(np.clip(w_val, 0.0, 200.0)), 1)
    pres_mb = round(float(np.clip(p_val, 850.0, 1030.0)), 1)

    level_val = wind_kt_to_imd_level(wind_kt)

    # Proximity to IMD scale category transition boundary
    min_dist_to_boundary = min(abs(wind_kt - b) for b in IMD_BOUNDARIES)

    # Base observation confidence
    base_conf = 0.90

    # Slight uncertainty penalty if right on the edge of two categories (e.g. 33.5 kt vs 34.0 kt)
    if min_dist_to_boundary < 2.0:
        boundary_penalty = (2.0 - min_dist_to_boundary) * 0.06  # Up to 0.12 reduction
    else:
        boundary_penalty = 0.0

    confidence = base_conf - boundary_penalty
    confidence = float(np.clip(confidence, 0.50, 0.94))
    confidence = round(confidence, 2)

    payload = {
        "level": level_val,
        "scale": "IMD",
        "max_wind_kt": wind_kt,
        "min_pressure_mb": pres_mb,
        "confidence": confidence,
    }

    # Contract verification
    IntensityPayload.model_validate(payload)
    return payload


__all__ = ["intensity", "IMD_BOUNDARIES"]
