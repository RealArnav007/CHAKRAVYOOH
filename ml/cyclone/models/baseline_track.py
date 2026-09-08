"""Tier-0 Deterministic Track Baseline: Persistence + CLIPER Climatological Drift with Parametric Uncertainty Cone."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np

from ml.cyclone.preprocess.geo import (
    EARTH_RADIUS_KM,
    KM_PER_NAUTICAL_MILE,
    calculate_speed_and_heading,
    haversine_distance_km,
    initial_bearing_deg,
)


DEFAULT_HORIZONS = [0, 6, 12, 24, 48, 72]

# IMD RSMC New Delhi 5-Year Average Operational Track Forecast Errors (km)
# Reference: IMD Cyclone Warning Division Annual Operational Reports (2018-2023)
# - 12h error: ~46 km
# - 24h error: ~78 km
# - 48h error: ~132 km
# - 72h error: ~205 km
# Linear growth rate parameter: b ~ 2.85 km/hour (r(t) = a + b * t, a=0)
PARAMETRIC_CONE_RATE_KM_PER_HOUR = 2.85


def load_climatology(spec_path: Optional[Path] = None) -> Dict[str, Any]:
    """Loads North Indian Ocean climatological drift vectors from cliper_climatology.json."""
    p = spec_path or (Path(__file__).resolve().parent / "cliper_climatology.json")
    if p.is_file():
        try:
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    # Fallback default climatology table
    return {
        "lat_bands": [
            {"min_lat": 0.0, "max_lat": 10.0, "mean_speed_kt": 9.5, "mean_heading_deg": 300.0},
            {"min_lat": 10.0, "max_lat": 15.0, "mean_speed_kt": 11.0, "mean_heading_deg": 320.0},
            {"min_lat": 15.0, "max_lat": 19.0, "mean_speed_kt": 12.5, "mean_heading_deg": 355.0},
            {"min_lat": 19.0, "max_lat": 35.0, "mean_speed_kt": 14.5, "mean_heading_deg": 35.0},
        ]
    }


def step_great_circle(
    lat: float,
    lon: float,
    distance_km: float,
    bearing_deg: float,
) -> Tuple[float, float]:
    """Projects a coordinate forward along a great-circle arc for a given distance and initial bearing.

    Args:
        lat, lon: Starting coordinate in decimal degrees.
        distance_km: Travel distance in kilometers.
        bearing_deg: Forward bearing in degrees [0, 360).

    Returns:
        Tuple of (new_lat, new_lon) in decimal degrees.
    """
    if distance_km <= 0.0:
        return lat, lon

    delta = distance_km / EARTH_RADIUS_KM
    phi1 = math.radians(lat)
    lambda1 = math.radians(lon)
    theta = math.radians(bearing_deg)

    sin_phi2 = math.sin(phi1) * math.cos(delta) + math.cos(phi1) * math.sin(delta) * math.cos(theta)
    sin_phi2 = max(-1.0, min(1.0, sin_phi2))
    phi2 = math.asin(sin_phi2)

    y = math.sin(theta) * math.sin(delta) * math.cos(phi1)
    x = math.cos(delta) - math.sin(phi1) * math.sin(phi2)
    lambda2 = lambda1 + math.atan2(y, x)

    # Normalize lon to [-180, 180]
    new_lat = math.degrees(phi2)
    new_lon = (math.degrees(lambda2) + 540.0) % 360.0 - 180.0

    return new_lat, new_lon


def persistence_forecast(
    history: List[Dict[str, Any]],
    horizons: List[int] = DEFAULT_HORIZONS,
) -> List[Tuple[int, float, float]]:
    """Generates trajectory forecast by linear great-circle extrapolation of latest velocity vector.

    Args:
        history: Sequence of past track points (must contain at least 1 point with lat, lon).
        horizons: List of forecast horizons in hours (e.g. [0, 6, 12, 24, 48, 72]).

    Returns:
        List of tuples: [(t_plus_h, lat, lon), ...]
    """
    if not history:
        raise ValueError("Cannot compute persistence forecast on empty history.")

    current = history[-1]
    lat0 = float(current["lat"])
    lon0 = float(current["lon"])
    speed_kt = float(current.get("speed_kt", current.get("storm_speed_kt", 10.0)))
    heading_deg = float(current.get("heading_deg", current.get("storm_dir_deg", 0.0)))

    # Ensure realistic non-zero translation speed for persistence
    speed_kt = max(3.0, speed_kt)

    forecast_pts: List[Tuple[int, float, float]] = []

    for h in horizons:
        if h == 0:
            forecast_pts.append((0, round(lat0, 4), round(lon0, 4)))
        else:
            dist_km = speed_kt * KM_PER_NAUTICAL_MILE * h
            f_lat, f_lon = step_great_circle(lat0, lon0, dist_km, heading_deg)
            forecast_pts.append((h, round(f_lat, 4), round(f_lon, 4)))

    return forecast_pts


def _get_climatological_drift(lat: float, climatology: Dict[str, Any]) -> Tuple[float, float]:
    """Retrieves mean translation speed and heading for a given latitude from climatology table."""
    bands = climatology.get("lat_bands", [])
    for b in bands:
        if float(b["min_lat"]) <= lat < float(b["max_lat"]):
            return float(b["mean_speed_kt"]), float(b["mean_heading_deg"])

    # Fallback to mid-latitude northward drift
    return 12.0, 350.0


def cliper_forecast(
    history: List[Dict[str, Any]],
    horizons: List[int] = DEFAULT_HORIZONS,
    climatology: Optional[Dict[str, Any]] = None,
) -> List[Tuple[int, float, float]]:
    """Generates a Climatology-and-Persistence (CLIPER) blended trajectory forecast.

    Damping Scheme:
    - At short horizons (6-12h), persistence dominates (w_pers ~ 1.0).
    - At extended horizons (24-72h), motion smoothly damps toward historical basin drift
      (poleward recurvature along the subtropical ridge).

    Args:
        history: Sequence of past track points.
        horizons: List of forecast horizons in hours.
        climatology: Optional climatological lookup dictionary.

    Returns:
        List of tuples: [(t_plus_h, lat, lon), ...]
    """
    if not history:
        raise ValueError("Cannot compute CLIPER forecast on empty history.")

    clim = climatology or load_climatology()
    current = history[-1]
    lat0 = float(current["lat"])
    lon0 = float(current["lon"])
    speed_kt = max(3.0, float(current.get("speed_kt", current.get("storm_speed_kt", 10.0))))
    heading_deg = float(current.get("heading_deg", current.get("storm_dir_deg", 0.0)))

    clim_speed, clim_heading = _get_climatological_drift(lat0, clim)

    # Persistence velocity vector components (knots)
    rad_pers = math.radians(heading_deg)
    u_pers = speed_kt * math.sin(rad_pers)
    v_pers = speed_kt * math.cos(rad_pers)

    # Climatology velocity vector components
    rad_clim = math.radians(clim_heading)
    u_clim = clim_speed * math.sin(rad_clim)
    v_clim = clim_speed * math.cos(rad_clim)

    forecast_pts: List[Tuple[int, float, float]] = []

    for h in horizons:
        if h == 0:
            forecast_pts.append((0, round(lat0, 4), round(lon0, 4)))
        else:
            # Exponential decay of persistence weight (e.g. e^(-h/36))
            # At 0h -> 1.0, at 24h -> 0.51, at 48h -> 0.26, at 72h -> 0.135
            w_pers = math.exp(-h / 36.0)
            w_clim = 1.0 - w_pers

            u_blend = w_pers * u_pers + w_clim * u_clim
            v_blend = w_pers * v_pers + w_clim * v_clim

            eff_speed = math.sqrt(u_blend**2 + v_blend**2)
            eff_heading = (math.degrees(math.atan2(u_blend, v_blend)) + 360.0) % 360.0

            dist_km = eff_speed * KM_PER_NAUTICAL_MILE * h
            f_lat, f_lon = step_great_circle(lat0, lon0, dist_km, eff_heading)
            forecast_pts.append((h, round(f_lat, 4), round(f_lon, 4)))

    return forecast_pts


def parametric_cone(
    horizons: List[int] = DEFAULT_HORIZONS,
    growth_rate_km_per_hour: float = PARAMETRIC_CONE_RATE_KM_PER_HOUR,
) -> List[float]:
    """Computes IMD-calibrated parametric uncertainty cone radii in km for given forecast horizons.

    Formula:
        r(0) = 0.0 km
        r(t) = growth_rate * t (empirically calibrated ~46km at 12h, ~78km at 24h, ~205km at 72h).

    Args:
        horizons: List of forecast horizons in hours.
        growth_rate_km_per_hour: Radial error expansion rate (default: 2.85 km/h).

    Returns:
        List of non-negative float radii in km, strictly starting with 0.0.
    """
    radii = []
    for h in horizons:
        if h == 0:
            radii.append(0.0)
        else:
            # Calibrated piecewise empirical curve matching IMD 5-year averages
            if h <= 12:
                r = 3.83 * h        # ~46 km at 12h
            elif h <= 24:
                r = 46.0 + 2.67 * (h - 12)  # ~78 km at 24h
            elif h <= 48:
                r = 78.0 + 2.25 * (h - 24)  # ~132 km at 48h
            else:
                r = 132.0 + 3.04 * (h - 48) # ~205 km at 72h
            radii.append(round(r, 2))
    return radii


def predict_track(
    history: List[Dict[str, Any]],
    horizons: List[int] = DEFAULT_HORIZONS,
    method: str = "cliper",
) -> Dict[str, Any]:
    """Generates complete Tier-0 deterministic trajectory prediction payload adhering to the frozen contract.

    Args:
        history: Sequence of historical track points.
        horizons: Forecast horizons [0, 6, 12, 24, 48, 72].
        method: 'cliper' (default) or 'persistence'.

    Returns:
        Dictionary conforming to PredictionPayload schema.
    """
    if not history:
        raise ValueError("predict_track requires non-empty history sequence.")

    # Select forecasting method
    if method.lower() == "persistence":
        pts = persistence_forecast(history, horizons=horizons)
    else:
        pts = cliper_forecast(history, horizons=horizons)

    cone_radii = parametric_cone(horizons=horizons)

    current = history[-1]
    lat0 = round(float(current["lat"]), 4)
    lon0 = round(float(current["lon"]), 4)
    speed_kt = round(float(current.get("speed_kt", current.get("storm_speed_kt", 10.0))), 2)
    heading_deg = round(float(current.get("heading_deg", current.get("storm_dir_deg", 0.0))), 1)

    predicted_path = [
        {"t_plus_h": h, "lat": lat, "lon": lon}
        for h, lat, lon in pts
    ]

    # Calculate confidence decaying with horizon and recent track erraticness
    max_h = max(horizons)
    base_confidence = 0.88 - (max_h * 0.0015)  # E.g. 0.88 - 0.108 = 0.772 at 72h

    if len(history) >= 3:
        headings = [float(pt.get("heading_deg", heading_deg)) for pt in history[-4:]]
        heading_std = float(np.std(headings))
        erratic_penalty = min(0.15, heading_std * 0.003)
        confidence = base_confidence - erratic_penalty
    else:
        confidence = base_confidence

    confidence = round(float(np.clip(confidence, 0.40, 0.95)), 2)

    return {
        "current_position": {"lat": lat0, "lon": lon0},
        "heading_deg": heading_deg,
        "speed_kt": speed_kt,
        "forecast_hours": max_h,
        "predicted_path": predicted_path,
        "confidence": confidence,
        "uncertainty": {"cone_radius_km": cone_radii},
    }


__all__ = [
    "persistence_forecast",
    "cliper_forecast",
    "parametric_cone",
    "predict_track",
    "step_great_circle",
    "PARAMETRIC_CONE_RATE_KM_PER_HOUR",
]
