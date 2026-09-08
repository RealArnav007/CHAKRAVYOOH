"""Tier-0 Deterministic Lifecycle Stage Classifier with boundary-distance confidence calibration."""

from __future__ import annotations

from typing import Any

import numpy as np

from ml.cyclone.preprocess.scales import lifecycle_stage
from ml.cyclone.schema.models import ClassificationPayload, StageEnum

STAGE_BOUNDARIES = [17.0, 28.0, 34.0, 48.0, 64.0]


def classify(sample: dict[str, Any]) -> dict[str, Any]:
    """Classifies the cyclone development stage with honest, margin-aware confidence.

    Confidence Modeling:
    - Base regime confidence: ~0.88–0.93 for observations safely inside class boundaries.
    - Boundary penalty: Proximity to major meteorological thresholds (e.g. 17 kt, 28 kt, 34 kt)
      reduces confidence down to ~0.60–0.70, reflecting physical uncertainty at stage transitions.

    Args:
        sample: Sample dictionary with 'wind_kt', 'pres_mb', 'nature', and optional 'history'.

    Returns:
        Dict conforming to ClassificationPayload: {"stage": StageEnum, "confidence": float}
    """
    stage_val = lifecycle_stage(sample, history=sample.get("history"))
    raw_w = sample.get("wind_kt", 0.0)
    wind_kt = 0.0 if (raw_w is None or np.isnan(float(raw_w))) else float(raw_w)

    # Calculate minimum distance to any critical intensity threshold boundary
    min_boundary_dist = min(abs(wind_kt - b) for b in STAGE_BOUNDARIES)

    # Base confidence depending on lifecycle stage stability
    if stage_val in [StageEnum.MATURE_TROPICAL_CYCLONE, StageEnum.POST_TROPICAL_REMNANT]:
        base_conf = 0.91
    elif stage_val in [StageEnum.TROPICAL_DEPRESSION, StageEnum.DEVELOPING_DISTURBANCE]:
        base_conf = 0.86
    elif stage_val == StageEnum.WEAKENING_SYSTEM:
        base_conf = 0.84
    else:
        base_conf = 0.88

    # Apply penalty for proximity to boundary (within 3 kt margin)
    if min_boundary_dist < 3.0:
        boundary_penalty = (3.0 - min_boundary_dist) * 0.07  # Up to 0.21 reduction
    else:
        boundary_penalty = 0.0

    confidence = base_conf - boundary_penalty
    confidence = float(np.clip(confidence, 0.55, 0.95))
    confidence = round(confidence, 2)

    payload = {
        "stage": stage_val,
        "confidence": confidence,
    }

    # Contract verification
    ClassificationPayload.model_validate(payload)
    return payload


__all__ = ["classify", "STAGE_BOUNDARIES"]
