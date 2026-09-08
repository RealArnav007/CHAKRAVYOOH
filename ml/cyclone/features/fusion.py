"""Multi-modal fused sample constructor uniting satellite imagery, atmospheric scalars, and track sequence."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from ml.cyclone.features.environmental import extract_environmental_features
from ml.cyclone.features.motion import extract_motion_features
from ml.cyclone.ingest.satellite import read_image
from ml.cyclone.preprocess.scales import (
    lifecycle_stage,
    wind_kt_to_imd_level,
)
from ml.cyclone.schema.models import IntensityLevelEnum, StageEnum


IMD_LEVEL_MAP: Dict[IntensityLevelEnum, int] = {
    IntensityLevelEnum.DEPRESSION: 0,
    IntensityLevelEnum.DEEP_DEPRESSION: 1,
    IntensityLevelEnum.CYCLONIC_STORM: 2,
    IntensityLevelEnum.SEVERE_CYCLONIC_STORM: 3,
    IntensityLevelEnum.VERY_SEVERE_CYCLONIC_STORM: 4,
    IntensityLevelEnum.EXTREMELY_SEVERE_CYCLONIC_STORM: 5,
    IntensityLevelEnum.SUPER_CYCLONIC_STORM: 6,
}

STAGE_MAP: Dict[StageEnum, int] = {
    StageEnum.NO_SIGNIFICANT_SYSTEM: 0,
    StageEnum.DEVELOPING_DISTURBANCE: 1,
    StageEnum.TROPICAL_DEPRESSION: 2,
    StageEnum.MATURE_TROPICAL_CYCLONE: 3,
    StageEnum.WEAKENING_SYSTEM: 4,
    StageEnum.POST_TROPICAL_REMNANT: 5,
}

DEFAULT_HORIZONS: List[int] = [6, 12, 24, 48, 72]
TRACK_SEQUENCE_DIM = 7


@dataclass
class FusedSample:
    """Unified multi-modal sample tensor container ready for model training and inference."""

    image_tensor: Optional[np.ndarray]           # Shape: (1, H, W) float32 in [0, 1] or None
    env_vector: np.ndarray                      # Shape: (6,) float32
    motion_vector: np.ndarray                   # Shape: (16,) float32
    track_sequence: np.ndarray                  # Shape: (N, 7) float32 [t_offset, lat, lon, wind, pres, speed, heading]
    meta: Dict[str, Any]                        # Storm ID, timestamp, original coordinates
    targets: Dict[str, Any]                     # Ground truth supervision signals


def _build_track_sequence_tensor(
    history: List[Dict[str, Any]],
    current_lat: float,
    current_lon: float,
    history_steps: int = 8,
) -> np.ndarray:
    """Constructs a fixed-length (N, 7) track sequence tensor with left zero-padding."""
    seq = np.zeros((history_steps, TRACK_SEQUENCE_DIM), dtype=np.float32)

    if not history:
        return seq

    pts_to_take = history[-history_steps:]
    n_pts = len(pts_to_take)
    start_idx = history_steps - n_pts

    for i, pt in enumerate(pts_to_take):
        t_off = float(pt.get("t_offset_h", 0.0))
        lat = float(pt.get("lat", current_lat))
        lon = float(pt.get("lon", current_lon))
        wind = float(pt.get("wind_kt", 0.0))
        pres = float(pt.get("pres_mb", 1010.0))
        spd = float(pt.get("speed_kt", 0.0))
        hdg = float(pt.get("heading_deg", 0.0))

        seq[start_idx + i] = [t_off, lat, lon, wind, pres, spd, hdg]

    return seq


def make_fused_sample(
    sample: Dict[str, Any],
    storm_future_lookup: Optional[Dict[int, Tuple[float, float]]] = None,
    horizons: Optional[List[int]] = None,
    history_steps: int = 8,
    image_target_size: Tuple[int, int] = (224, 224),
    imputer_stats: Optional[Dict[str, float]] = None,
) -> FusedSample:
    """Transforms a raw colocalized sample dictionary into a model-ready FusedSample.

    Args:
        sample: Raw colocalized sample containing position, history, and environmental fields.
        storm_future_lookup: Optional mapping {horizon_hours: (future_lat, future_lon)} for target building.
        horizons: List of forecast horizons in hours (default: [6, 12, 24, 48, 72]).
        history_steps: Length of recurrent history window (default: 8).
        image_target_size: Desired (H, W) for satellite imagery.
        imputer_stats: Optional environmental median dictionary.

    Returns:
        FusedSample container with tensors and multi-task supervision targets.
    """
    forecast_horizons = horizons or DEFAULT_HORIZONS
    num_horizons = len(forecast_horizons)

    lat = float(sample.get("lat", 0.0))
    lon = float(sample.get("lon", 0.0))
    wind_kt = float(sample.get("wind_kt", 0.0))
    pres_mb = float(sample.get("pres_mb", 1010.0))

    # 1. Feature vectors
    env_vector = extract_environmental_features(sample, imputer_stats=imputer_stats)
    motion_vector = extract_motion_features(sample)
    track_sequence = _build_track_sequence_tensor(
        history=sample.get("history", []),
        current_lat=lat,
        current_lon=lon,
        history_steps=history_steps,
    )

    # 2. Image tensor (lazy load if image path is valid)
    image_tensor: Optional[np.ndarray] = None
    img_path_str = sample.get("image_path")
    if img_path_str and Path(img_path_str).is_file():
        try:
            img_arr = read_image(img_path_str, target_size=image_target_size)
            image_tensor = np.expand_dims(img_arr, axis=0).astype(np.float32)  # (1, H, W)
        except Exception:
            image_tensor = None

    # 3. Target values
    imd_enum = wind_kt_to_imd_level(wind_kt)
    imd_idx = IMD_LEVEL_MAP.get(imd_enum, 0)

    stage_enum = lifecycle_stage(sample, history=sample.get("history"))
    stage_idx = STAGE_MAP.get(stage_enum, 0)

    detected_val = 1.0 if wind_kt >= 17.0 else 0.0

    # 4. Trajectory future targets (delta positions & valid horizon masks)
    future_deltas = np.zeros((num_horizons, 2), dtype=np.float32)
    future_positions = np.zeros((num_horizons, 2), dtype=np.float32)
    horizon_masks = np.zeros(num_horizons, dtype=bool)

    lookup = storm_future_lookup or sample.get("future_lookup") or sample.get("future")
    if lookup:
        for idx, h in enumerate(forecast_horizons):
            if h in lookup:
                f_lat, f_lon = lookup[h]
                d_lat = f_lat - lat
                d_lon = (f_lon - lon + 540.0) % 360.0 - 180.0
                future_deltas[idx] = [d_lat, d_lon]
                future_positions[idx] = [f_lat, f_lon]
                horizon_masks[idx] = True

    targets = {
        "wind_kt": np.float32(wind_kt),
        "pres_mb": np.float32(pres_mb),
        "imd_level_idx": np.int64(imd_idx),
        "stage_idx": np.int64(stage_idx),
        "detected": np.float32(detected_val),
        "future_deltas": future_deltas,
        "future_positions": future_positions,
        "horizon_masks": horizon_masks,
    }

    meta = {
        "storm_id": sample.get("storm_id", "UNKNOWN"),
        "time": sample.get("time", ""),
        "lat": lat,
        "lon": lon,
        "image_path": img_path_str,
        "image_available": image_tensor is not None,
    }

    return FusedSample(
        image_tensor=image_tensor,
        env_vector=env_vector,
        motion_vector=motion_vector,
        track_sequence=track_sequence,
        meta=meta,
        targets=targets,
    )


__all__ = [
    "FusedSample",
    "make_fused_sample",
    "IMD_LEVEL_MAP",
    "STAGE_MAP",
    "DEFAULT_HORIZONS",
]
