"""Environmental atmospheric & oceanic scalar feature extractor with deterministic imputation."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np

ENV_FEATURE_NAMES: list[str] = [
    "sst_c",
    "shear_ms",
    "rh500",
    "vort850",
    "mslp_mb",
    "wind10m_ms",
]

# Standard training-set empirical medians for missing data imputation
DEFAULT_IMPUTER_MEDIANS: dict[str, float] = {
    "sst_c": 28.5,  # Mean tropical Indian Ocean SST in Celsius
    "shear_ms": 12.0,  # Deep-layer vertical wind shear (m/s)
    "rh500": 65.0,  # 500 hPa relative humidity (%)
    "vort850": 15.0,  # 850 hPa relative vorticity (* 10^-5 s^-1)
    "mslp_mb": 1006.0,  # Background environmental surface pressure (mb)
    "wind10m_ms": 8.0,  # Surface 10m wind speed (m/s)
}


def load_imputer_medians(spec_path: Path | None = None) -> dict[str, float]:
    """Loads feature imputer medians from feature_spec.json if present, else returns defaults."""
    path = spec_path or (Path(__file__).resolve().parent / "feature_spec.json")
    if path.is_file():
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            return data.get("environmental_imputer_medians", DEFAULT_IMPUTER_MEDIANS)
        except Exception:
            pass
    return DEFAULT_IMPUTER_MEDIANS.copy()


def extract_environmental_features(
    sample: dict[str, Any],
    imputer_stats: dict[str, float] | None = None,
) -> np.ndarray:
    """Assembles a 6-dimensional environmental atmospheric feature vector with deterministic imputation.

    Features (in strict order):
    1. sst_c: Sea Surface Temperature in degrees Celsius.
    2. shear_ms: 850–200 hPa deep-layer vertical wind shear magnitude (m/s).
    3. rh500: Relative humidity at 500 hPa (%).
    4. vort850: Relative vorticity at 850 hPa (s^-1).
    5. mslp_mb: Mean sea level pressure (mb/hPa).
    6. wind10m_ms: Surface 10m wind speed magnitude (m/s).

    Args:
        sample: Sample dictionary containing an 'env' sub-dict.
        imputer_stats: Optional dictionary of median values to replace NaNs.

    Returns:
        np.ndarray of shape (6,) and dtype np.float32.
    """
    stats = imputer_stats or DEFAULT_IMPUTER_MEDIANS
    env_dict = sample.get("env", {}) if isinstance(sample.get("env"), dict) else {}

    vector: list[float] = []

    for name in ENV_FEATURE_NAMES:
        val = env_dict.get(name, float("nan"))
        # Check if NaN or None
        if val is None or (isinstance(val, (float, int)) and math.isnan(val)):
            imputed_val = stats.get(name, DEFAULT_IMPUTER_MEDIANS[name])
            vector.append(float(imputed_val))
        else:
            vector.append(float(val))

    return np.array(vector, dtype=np.float32)


def fit_environmental_imputer(samples: list[dict[str, Any]]) -> dict[str, float]:
    """Computes empirical medians from a list of training samples and returns imputer dictionary."""
    accumulators: dict[str, list[float]] = {name: [] for name in ENV_FEATURE_NAMES}

    for s in samples:
        env_dict = s.get("env", {})
        if isinstance(env_dict, dict):
            for name in ENV_FEATURE_NAMES:
                val = env_dict.get(name)
                if val is not None and not math.isnan(val):
                    accumulators[name].append(float(val))

    medians = {}
    for name, vals in accumulators.items():
        if vals:
            medians[name] = round(float(np.median(vals)), 2)
        else:
            medians[name] = DEFAULT_IMPUTER_MEDIANS[name]

    return medians


__all__ = [
    "extract_environmental_features",
    "fit_environmental_imputer",
    "load_imputer_medians",
    "ENV_FEATURE_NAMES",
    "DEFAULT_IMPUTER_MEDIANS",
]
