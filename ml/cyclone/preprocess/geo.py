"""Geodesic and spherical navigation utilities for cyclone motion and distance modeling."""

from __future__ import annotations

import math

import numpy as np

EARTH_RADIUS_KM = 6371.0
KM_PER_NAUTICAL_MILE = 1.852


def haversine_distance_km(
    lat1: float | np.ndarray,
    lon1: float | np.ndarray,
    lat2: float | np.ndarray,
    lon2: float | np.ndarray,
) -> float | np.ndarray:
    """Calculates great-circle distance between two coordinate pairs on Earth in kilometers.

    Args:
        lat1, lon1: First point latitude and longitude in decimal degrees.
        lat2, lon2: Second point latitude and longitude in decimal degrees.

    Returns:
        Great-circle distance in kilometers.
    """
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    delta_phi = np.radians(lat2 - lat1)
    delta_lambda = np.radians(lon2 - lon1)

    a = np.sin(delta_phi / 2.0) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(delta_lambda / 2.0) ** 2
    # Clip for floating-point inaccuracies
    a = np.clip(a, 0.0, 1.0)
    c = 2.0 * np.arctan2(np.sqrt(a), np.sqrt(1.0 - a))

    dist_km = EARTH_RADIUS_KM * c
    return float(dist_km) if np.isscalar(lat1) and np.isscalar(lat2) else dist_km


def haversine_distance_nm(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    """Calculates great-circle distance between two points in nautical miles."""
    return haversine_distance_km(lat1, lon1, lat2, lon2) / KM_PER_NAUTICAL_MILE


def initial_bearing_deg(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    """Calculates initial forward bearing (azimuth) from point 1 to point 2 in degrees [0, 360).

    Args:
        lat1, lon1: Origin point in decimal degrees.
        lat2, lon2: Destination point in decimal degrees.

    Returns:
        Initial bearing clockwise from true North in degrees [0.0, 360.0).
    """
    if abs(lat1 - lat2) < 1e-6 and abs(lon1 - lon2) < 1e-6:
        return 0.0

    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_lambda = math.radians(lon2 - lon1)

    y = math.sin(delta_lambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)

    initial_bearing = math.degrees(math.atan2(y, x))
    compass_bearing = (initial_bearing + 360.0) % 360.0
    return compass_bearing


def calculate_speed_and_heading(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
    delta_hours: float,
) -> tuple[float, float]:
    """Computes translation speed in knots and heading in degrees over a elapsed time delta.

    Args:
        lat1, lon1: Initial coordinates.
        lat2, lon2: Final coordinates.
        delta_hours: Elapsed duration in hours (must be > 0).

    Returns:
        Tuple of (speed_knots, heading_degrees).
    """
    if delta_hours <= 0:
        return 0.0, 0.0

    dist_nm = haversine_distance_nm(lat1, lon1, lat2, lon2)
    speed_kt = dist_nm / delta_hours
    heading = initial_bearing_deg(lat1, lon1, lat2, lon2)
    return round(speed_kt, 2), round(heading, 1)


__all__ = [
    "EARTH_RADIUS_KM",
    "KM_PER_NAUTICAL_MILE",
    "haversine_distance_km",
    "haversine_distance_nm",
    "initial_bearing_deg",
    "calculate_speed_and_heading",
]
