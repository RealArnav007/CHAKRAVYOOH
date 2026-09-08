"""Meteorological scale mappings and lifecycle stage determination for Chakravyuh.

Authoritative source of truth for:
- IMD (India Meteorological Department / RSMC New Delhi) Tropical Cyclone Intensity Scale.
- Saffir-Simpson Hurricane Wind Scale (supplemental mapping for extra.saffir_simpson).
- Lifecycle development stage classification.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from ml.cyclone.schema.models import IntensityLevelEnum, StageEnum


def wind_kt_to_imd_level(wind_kt: float) -> IntensityLevelEnum:
    """Maps sustained 3-minute surface wind speed in knots to official IMD category.

    Reference: IMD RSMC New Delhi Cyclone Classification Standards
    - Depression (D): 17–27 kt (31–49 km/h)
    - Deep Depression (DD): 28–33 kt (50–61 km/h)
    - Cyclonic Storm (CS): 34–47 kt (62–88 km/h)
    - Severe Cyclonic Storm (SCS): 48–63 kt (89–117 km/h)
    - Very Severe Cyclonic Storm (VSCS): 64–89 kt (118–166 km/h)
    - Extremely Severe Cyclonic Storm (ESCS): 90–119 kt (167–221 km/h)
    - Super Cyclonic Storm (SuCS): >= 120 kt (>= 222 km/h)

    Args:
        wind_kt: Maximum sustained wind speed in knots.

    Returns:
        IntensityLevelEnum value.
    """
    w = float(wind_kt)

    # IMD Threshold 7: Super Cyclonic Storm (>= 120 kt)
    if w >= 120.0:
        return IntensityLevelEnum.SUPER_CYCLONIC_STORM

    # IMD Threshold 6: Extremely Severe Cyclonic Storm (90–119 kt)
    if w >= 90.0:
        return IntensityLevelEnum.EXTREMELY_SEVERE_CYCLONIC_STORM

    # IMD Threshold 5: Very Severe Cyclonic Storm (64–89 kt)
    if w >= 64.0:
        return IntensityLevelEnum.VERY_SEVERE_CYCLONIC_STORM

    # IMD Threshold 4: Severe Cyclonic Storm (48–63 kt)
    if w >= 48.0:
        return IntensityLevelEnum.SEVERE_CYCLONIC_STORM

    # IMD Threshold 3: Cyclonic Storm (34–47 kt)
    if w >= 34.0:
        return IntensityLevelEnum.CYCLONIC_STORM

    # IMD Threshold 2: Deep Depression (28–33 kt)
    if w >= 28.0:
        return IntensityLevelEnum.DEEP_DEPRESSION

    # IMD Threshold 1: Depression (17–27 kt, and sub-17 kt clamped fallback)
    return IntensityLevelEnum.DEPRESSION


def wind_kt_to_saffir_simpson(wind_kt: float) -> str:
    """Maps sustained wind speed in knots to Saffir-Simpson Hurricane Wind Scale category string.

    Reference: NOAA National Hurricane Center (NHC) Saffir-Simpson Scale
    - Tropical Depression: < 34 kt
    - Tropical Storm: 34–63 kt
    - Category 1: 64–82 kt
    - Category 2: 83–95 kt
    - Category 3: 96–112 kt
    - Category 4: 113–136 kt
    - Category 5: >= 137 kt

    Args:
        wind_kt: Maximum sustained wind speed in knots.

    Returns:
        Human-readable category string (e.g. "Category 3", "Tropical Storm").
    """
    w = float(wind_kt)

    if w >= 137.0:
        return "Category 5"
    if w >= 113.0:
        return "Category 4"
    if w >= 96.0:
        return "Category 3"
    if w >= 83.0:
        return "Category 2"
    if w >= 64.0:
        return "Category 1"
    if w >= 34.0:
        return "Tropical Storm"
    return "Tropical Depression"


def lifecycle_stage(
    row: pd.Series | dict[str, Any],
    history: pd.DataFrame | list[dict[str, Any]] | None = None,
) -> StageEnum:
    """Determines meteorological life-cycle stage based on current wind, 24h wind trend, and system nature.

    Lifecycle stages:
    1. POST_TROPICAL_REMNANT: Extratropical transition ('ET', 'EX', 'DS') or post-landfall dissipation.
    2. WEAKENING_SYSTEM: System past peak intensity with wind declining by > 15 kt.
    3. MATURE_TROPICAL_CYCLONE: Gale-force winds (>= 34 kt) actively maintained near peak.
    4. TROPICAL_DEPRESSION: Organized low pressure system with 17–33 kt winds.
    5. DEVELOPING_DISTURBANCE: Early-stage intensifying disturbance (< 28 kt, rising trend).
    6. NO_SIGNIFICANT_SYSTEM: Weak disturbance with winds < 17 kt and no intensification signature.

    Args:
        row: Current observation record (must contain 'wind_kt', optionally 'nature', 'pres_mb').
        history: Historical track sequence preceding the current observation.

    Returns:
        StageEnum development stage.
    """
    wind_val = row.get("wind_kt", 0.0) if isinstance(row, dict) else row.get("wind_kt", 0.0)
    current_wind = float(wind_val) if pd.notna(wind_val) else 0.0

    nature_val = row.get("nature", "TS") if isinstance(row, dict) else row.get("nature", "TS")
    nature_str = str(nature_val).upper().strip()

    # Rule 1: Nature indicates post-tropical / extratropical transition
    if nature_str in ["ET", "EX", "POST_TROPICAL", "REMNANT"]:
        return StageEnum.POST_TROPICAL_REMNANT

    # Calculate historical peak and trend if history is supplied
    max_history_wind = current_wind
    wind_trend = 0.0  # Positive = intensifying, Negative = weakening

    if history is not None:
        if isinstance(history, pd.DataFrame) and not history.empty:
            hist_winds = pd.to_numeric(history.get("wind_kt"), errors="coerce").dropna()
            if not hist_winds.empty:
                max_history_wind = max(float(hist_winds.max()), current_wind)
                # Trend over last 2-4 points (~6-12 hours)
                if len(hist_winds) >= 2:
                    wind_trend = current_wind - float(hist_winds.iloc[-2])
        elif isinstance(history, list) and len(history) > 0:
            hist_winds = [
                float(h["wind_kt"]) for h in history if "wind_kt" in h and h["wind_kt"] is not None
            ]
            if hist_winds:
                max_history_wind = max(max(hist_winds), current_wind)
                if len(hist_winds) >= 2:
                    wind_trend = current_wind - hist_winds[-2]

    # Rule 2: Post-peak significant weakening
    if max_history_wind >= 34.0 and (max_history_wind - current_wind) >= 15.0:
        if current_wind < 28.0 and nature_str in ["DS", "NR"]:
            return StageEnum.POST_TROPICAL_REMNANT
        return StageEnum.WEAKENING_SYSTEM

    # Rule 3: Mature tropical cyclone (>= 34 kt, IMD Cyclonic Storm through Super Cyclonic Storm)
    if current_wind >= 34.0:
        return StageEnum.MATURE_TROPICAL_CYCLONE

    # Rule 4: Tropical Depression (17–33 kt)
    if current_wind >= 17.0:
        if current_wind < 28.0 and wind_trend > 0:
            return StageEnum.DEVELOPING_DISTURBANCE
        return StageEnum.TROPICAL_DEPRESSION

    # Rule 5: Sub-17 kt system
    if wind_trend > 0:
        return StageEnum.DEVELOPING_DISTURBANCE

    return StageEnum.NO_SIGNIFICANT_SYSTEM


__all__ = [
    "wind_kt_to_imd_level",
    "wind_kt_to_saffir_simpson",
    "lifecycle_stage",
]
