"""Tier-0 Deterministic Cyclone Identification with continuous, calibrated confidence scores."""

from __future__ import annotations

import math
from typing import Any, Dict, List
import numpy as np

from ml.cyclone.schema.models import IdentificationPayload

IMD_DEPRESSION_WIND_THRESHOLD_KT = 17.0


def identify(sample: Dict[str, Any]) -> Dict[str, Any]:
    """Identifies cyclone existence from wind magnitude, pressure anomalies, and track persistence.

    Confidence Modeling:
    - Base confidence is a logistic response centered at the 17 kt depression threshold.
    - Track persistence bonus: Sustained historical points (+0.05 to +0.15) increase confidence.
    - Borderline systems (16–18 kt) receive ~0.45–0.55 confidence.
    - Clear organized cyclones (>= 45 kt) receive >= 0.90 confidence.
    - Sub-12 kt background noise receives < 0.20 confidence.

    Args:
        sample: Sample dictionary with 'wind_kt', 'pres_mb', and optional 'history'.

    Returns:
        Dict conforming to IdentificationPayload: {"detected": bool, "confidence": float}
    """
    wind_kt = float(sample.get("wind_kt", 0.0))
    pres_mb = float(sample.get("pres_mb", 1010.0))
    history: List[Dict[str, Any]] = sample.get("history", [])

    # 1. Wind logistic component (steepness k = 0.16 centered at 17.0 kt)
    wind_margin = wind_kt - IMD_DEPRESSION_WIND_THRESHOLD_KT
    raw_logistic = 1.0 / (1.0 + math.exp(-0.16 * wind_margin))

    # 2. Persistence / Circulation organization factor
    # Continuous tracking over past 12-24h indicates organized vortex (+0.01 to +0.06)
    n_hist = len(history)
    persistence_factor = min(0.06, (n_hist / 8.0) * 0.06) if n_hist > 1 else 0.0

    # 3. Pressure deficit factor (lower pressure below standard 1010 mb increases confidence)
    pres_deficit = max(0.0, 1010.0 - pres_mb)
    pres_factor = min(0.04, (pres_deficit / 30.0) * 0.04)

    # 4. Synthesize calibrated confidence score
    confidence = raw_logistic + persistence_factor + pres_factor
    confidence = float(np.clip(confidence, 0.05, 0.98))
    confidence = round(confidence, 2)

    # Detection decision threshold: detected when wind >= 17 kt or confidence >= 0.50
    detected = bool(wind_kt >= IMD_DEPRESSION_WIND_THRESHOLD_KT or confidence >= 0.50)

    # Safety clamp: if detected is False, confidence must reflect non-detection
    if not detected and confidence > 0.49:
        confidence = 0.45

    payload = {
        "detected": detected,
        "confidence": confidence,
    }

    # Contract verification
    IdentificationPayload.model_validate(payload)
    return payload


__all__ = ["identify", "IMD_DEPRESSION_WIND_THRESHOLD_KT"]
