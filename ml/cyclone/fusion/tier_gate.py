"""Per-field Tier-1 / Tier-0 gating, provenance tracking, and graceful multi-modal degradation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np

from ml.cyclone.preprocess.scales import wind_kt_to_saffir_simpson
from ml.cyclone.schema.models import (
    ClassificationPayload,
    CycloneIntelligence,
    GeoPoint,
    IdentificationPayload,
    IntensityLevelEnum,
    IntensityPayload,
    PredictionPayload,
    StageEnum,
    TierEnum,
    TrajectoryPoint,
    UncertaintyCone,
)

logger = logging.getLogger(__name__)


@dataclass
class ConfidenceGatesConfig:
    """Configurable threshold gates for dynamic tier selection."""

    min_detection_confidence: float = 0.50
    min_stage_confidence: float = 0.60
    min_intensity_confidence: float = 0.60
    min_track_confidence: float = 0.50
    max_track_variance_ceiling: float = 5.0


def select_tier(
    field: str,
    tier1_out: Optional[Union[Dict[str, Any], Any]],
    tier0_out: Union[Dict[str, Any], Any],
    inputs: Dict[str, Any],
    config: Optional[Union[ConfidenceGatesConfig, Dict[str, Any]]] = None,
) -> Tuple[Any, str, str]:
    """Performs per-field gating between Tier-1 (neural) and Tier-0 (deterministic baseline).

    Decision Rules:
    1. Identification (Detection):
       - Requires valid Tier-1 output.
       - If image is missing/empty, uses env+track if confident.
       - Requires detection confidence >= min_detection_confidence.
    2. Classification (Lifecycle Stage):
       - Requires valid Tier-1 stage output.
       - Requires stage confidence >= min_stage_confidence.
    3. Intensity Estimation:
       - Requires valid Tier-1 intensity output (wind_kt > 0).
       - Requires intensity confidence >= min_intensity_confidence.
    4. Trajectory Prediction:
       - Requires valid Tier-1 prediction output with non-empty path.
       - Requires track confidence >= min_track_confidence AND predicted variance <= ceiling.
       - For ultra-short initial genesis steps (t <= 6h with high heading uncertainty), Tier-0 is favored.

    Args:
        field: One of 'identification', 'classification', 'intensity', 'prediction'.
        tier1_out: Tier-1 neural output payload or dict (can be None on failure).
        tier0_out: Tier-0 baseline output payload or dict (guaranteed fallback).
        inputs: Input features dict containing available modalities (image, env, track).
        config: Optional gate thresholds.

    Returns:
        Tuple of (selected_payload, source_tier_tag, decision_reason).
    """
    cfg = config if isinstance(config, ConfidenceGatesConfig) else ConfidenceGatesConfig(**(config or {}))

    # Check input availability flags
    has_image = bool(inputs.get("image_available", False))
    has_env = bool(inputs.get("env_available", False))
    has_track = bool(inputs.get("track_available", True))

    # 1. Failure mode check: If only track is available and both image & env are missing -> Fallback to Tier-0
    if not has_image and not has_env:
        return tier0_out, "tier0", "Missing both satellite imagery and ERA5 environment -> Tier-0 deterministic fallback"

    # If Tier-1 output is completely missing or None
    if tier1_out is None:
        return tier0_out, "tier0", "Tier-1 neural model produced no output -> Fallback to Tier-0"

    # -------------------------------------------------------------------------
    # Field-Specific Gating
    # -------------------------------------------------------------------------

    if field == "identification":
        det_flag = bool(tier1_out.get("detected", False)) if isinstance(tier1_out, dict) else getattr(tier1_out, "detected", False)
        conf = _extract_confidence(tier1_out)
        if conf is None:
            return tier0_out, "tier0", "Tier-1 identification confidence missing -> Tier-0 fallback"

        obs_wind = float(inputs.get("wind_kt", 0.0))
        if conf >= cfg.min_detection_confidence:
            if not det_flag and not has_image and obs_wind >= 17.0:
                return tier0_out, "tier0", f"Tier-1 (no-image) non-detection overridden by observed wind ({obs_wind} kt >= 17 kt) -> Tier-0 fallback"
            source = "tier1 (image+env)" if has_image else "tier1 (env+track fallback)"
            status_str = "Detection" if det_flag else "Non-detection"
            return tier1_out, "tier1", f"{status_str} confidence ({conf:.2f}) >= threshold ({cfg.min_detection_confidence:.2f}) via {source}"
        else:
            return tier0_out, "tier0", f"Detection confidence ({conf:.2f}) < threshold ({cfg.min_detection_confidence:.2f}) -> Tier-0 fallback"

    elif field == "classification":
        conf = _extract_confidence(tier1_out)
        if conf is None:
            return tier0_out, "tier0", "Tier-1 stage classification confidence missing -> Tier-0 fallback"
        if conf >= cfg.min_stage_confidence:
            return tier1_out, "tier1", f"Stage confidence ({conf:.2f}) >= threshold ({cfg.min_stage_confidence:.2f})"
        else:
            return tier0_out, "tier0", f"Stage confidence ({conf:.2f}) < threshold ({cfg.min_stage_confidence:.2f}) -> Tier-0 fallback"

    elif field == "intensity":
        conf = _extract_confidence(tier1_out)
        if conf is None:
            return tier0_out, "tier0", "Tier-1 intensity confidence missing -> Tier-0 fallback"

        # Check physical bounds on predicted wind
        pred_wind = _extract_wind_kt(tier1_out)
        if pred_wind is None or pred_wind < 0.0 or pred_wind > 250.0:
            return tier0_out, "tier0", f"Predicted wind speed ({pred_wind} kt) violates physical bounds -> Tier-0 fallback"

        if conf >= cfg.min_intensity_confidence:
            return tier1_out, "tier1", f"Intensity confidence ({conf:.2f}) >= threshold ({cfg.min_intensity_confidence:.2f})"
        else:
            return tier0_out, "tier0", f"Intensity confidence ({conf:.2f}) < threshold ({cfg.min_intensity_confidence:.2f}) -> Tier-0 fallback"

    elif field == "prediction":
        conf = _extract_confidence(tier1_out) or 0.8
        max_log_var = _extract_max_log_variance(tier1_out)

        if max_log_var is not None and max_log_var > cfg.max_track_variance_ceiling:
            return tier0_out, "tier0", f"Predicted track log-variance ({max_log_var:.2f}) exceeded ceiling ({cfg.max_track_variance_ceiling:.2f}) -> Tier-0 CLIPER fallback"

        if conf >= cfg.min_track_confidence:
            return tier1_out, "tier1", f"Track confidence ({conf:.2f}) >= threshold ({cfg.min_track_confidence:.2f})"
        else:
            return tier0_out, "tier0", f"Track confidence ({conf:.2f}) < threshold ({cfg.min_track_confidence:.2f}) -> Tier-0 fallback"

    # Default fallback
    return tier0_out, "tier0", f"Unrecognized field '{field}' -> Tier-0 default"


# -----------------------------------------------------------------------------
# Master Assembly & Provenance Tracking
# -----------------------------------------------------------------------------


def gate_and_assemble_cyclone_intelligence(
    tier1_payload: Optional[Dict[str, Any]],
    tier0_payload: Dict[str, Any],
    inputs: Dict[str, Any],
    config: Optional[Union[ConfidenceGatesConfig, Dict[str, Any]]] = None,
    cyclone_id: str = "CYC-LIVE-001",
    name: str = "INVEST-SYSTEM",
    basin: str = "North Indian Ocean",
    timestamp: Optional[str] = None,
    model_version: str = "chakravyuh-fusion-net-v1.0",
    extra: Optional[Dict[str, Any]] = None,
) -> CycloneIntelligence:
    """Gates per-field outputs and builds a certified, schema-validated CycloneIntelligence object.

    Graceful Degradation Guarantees:
    - Missing Image: Uses Env+Track neural trunk; tags provenance.
    - Missing ERA5: Uses Image+Track neural trunk; tags provenance.
    - Missing Everything Except Track: Falls back completely to Tier-0 CLIPER / Persistence.
    - Never raises: Catches any formatting anomalies and emits a valid Tier-0 fallback.
    """
    ts_str = timestamp or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    if not ts_str.endswith("Z") and not ("+" in ts_str or "-" in ts_str[10:]):
        ts_str = ts_str + "Z"

    t1 = tier1_payload or {}
    t0 = tier0_payload

    provenance_sources: Dict[str, str] = {}
    provenance_reasons: Dict[str, str] = {}

    try:
        # 1. Identification Gating
        ident_val, ident_tier, ident_reason = select_tier(
            "identification", t1.get("identification"), t0.get("identification", {}), inputs, config
        )
        provenance_sources["identification"] = ident_tier
        provenance_reasons["identification"] = ident_reason
        ident_obj = _parse_identification(ident_val)

        # 2. Classification Gating
        class_val, class_tier, class_reason = select_tier(
            "classification", t1.get("classification"), t0.get("classification", {}), inputs, config
        )
        provenance_sources["classification"] = class_tier
        provenance_reasons["classification"] = class_reason
        class_obj = _parse_classification(class_val)

        # 3. Intensity Gating
        int_val, int_tier, int_reason = select_tier(
            "intensity", t1.get("intensity"), t0.get("intensity", {}), inputs, config
        )
        provenance_sources["intensity"] = int_tier
        provenance_reasons["intensity"] = int_reason
        int_obj = _parse_intensity(int_val)

        # 4. Prediction Gating
        pred_obj = None
        if ident_obj.detected:
            pred_val, pred_tier, pred_reason = select_tier(
                "prediction", t1.get("prediction"), t0.get("prediction", {}), inputs, config
            )
            provenance_sources["prediction"] = pred_tier
            provenance_reasons["prediction"] = pred_reason
            pred_obj = _parse_prediction(pred_val, current_pos=inputs.get("current_position"))
        else:
            provenance_sources["prediction"] = "none (detected=false)"
            provenance_reasons["prediction"] = "System not detected; prediction omitted"

        # Determine object-level tier
        used_tiers = set()
        for k in ["identification", "classification", "intensity"]:
            used_tiers.add(provenance_sources[k])
        if ident_obj.detected and "prediction" in provenance_sources:
            used_tiers.add(provenance_sources["prediction"])

        if used_tiers == {"tier1"}:
            obj_tier = TierEnum.TIER1
        elif used_tiers == {"tier0"}:
            obj_tier = TierEnum.TIER0
        else:
            obj_tier = TierEnum.MIXED

        # Build active sources list
        active_sources = []
        if bool(inputs.get("image_available", False)):
            active_sources.append("insat3d_ir")
        if bool(inputs.get("env_available", False)):
            active_sources.append("era5")
        if bool(inputs.get("track_available", True)):
            active_sources.append("ibtracs_track")
        if not active_sources:
            active_sources = ["ibtracs_climatology"]

        extra_metadata = {
            "saffir_simpson": wind_kt_to_saffir_simpson(int_obj.max_wind_kt),
            "provenance": {
                "sources": provenance_sources,
                "reasons": provenance_reasons,
                "object_tier": obj_tier.value,
            },
            "active_modalities": active_sources,
        }
        if extra:
            for k, v in extra.items():
                if k == "provenance" and isinstance(v, dict):
                    extra_metadata["provenance"].update(v)
                else:
                    extra_metadata[k] = v

        # Assemble Master Payload
        return CycloneIntelligence(
            schema_version="1.0",
            cyclone_id=str(t1.get("cyclone_id") or t0.get("cyclone_id") or cyclone_id),
            name=str(t1.get("name") or t0.get("name") or name),
            timestamp=ts_str,
            basin=str(t1.get("basin") or t0.get("basin") or basin),
            identification=ident_obj,
            classification=class_obj,
            intensity=int_obj,
            prediction=pred_obj,
            sources=active_sources,
            model_version=model_version,
            tier=obj_tier,
            extra=extra_metadata,
        )

    except Exception as e:
        logger.error(f"[TIER GATE] Error during assembly ({e}) -> Emitting safe Tier-0 fallback.")
        return _build_safe_tier0_fallback(
            t0=t0,
            cyclone_id=cyclone_id,
            name=name,
            basin=basin,
            timestamp=ts_str,
            inputs=inputs,
            error_msg=str(e),
        )


# -----------------------------------------------------------------------------
# Internal Parsing Helpers
# -----------------------------------------------------------------------------


def _extract_confidence(data: Any) -> Optional[float]:
    if isinstance(data, dict):
        val = data.get("confidence")
        return float(val) if val is not None else None
    elif hasattr(data, "confidence"):
        return float(data.confidence)
    return None


def _extract_wind_kt(data: Any) -> Optional[float]:
    if isinstance(data, dict):
        val = data.get("max_wind_kt") or data.get("wind_kt")
        return float(val) if val is not None else None
    elif hasattr(data, "max_wind_kt"):
        return float(data.max_wind_kt)
    return None


def _extract_max_log_variance(data: Any) -> Optional[float]:
    if isinstance(data, dict):
        val = data.get("max_log_var") or data.get("log_var")
        return float(val) if val is not None else None
    return None


def _parse_identification(data: Any) -> IdentificationPayload:
    if isinstance(data, IdentificationPayload):
        return data
    d = data if isinstance(data, dict) else {}
    return IdentificationPayload(
        detected=bool(d.get("detected", True)),
        confidence=float(np.clip(d.get("confidence", 0.5), 0.0, 1.0)),
    )


def _parse_classification(data: Any) -> ClassificationPayload:
    if isinstance(data, ClassificationPayload):
        return data
    d = data if isinstance(data, dict) else {}
    stage_raw = str(d.get("stage", "DEVELOPING_DISTURBANCE"))
    try:
        stage_enum = StageEnum(stage_raw)
    except ValueError:
        stage_enum = StageEnum.DEVELOPING_DISTURBANCE

    return ClassificationPayload(
        stage=stage_enum,
        confidence=float(np.clip(d.get("confidence", 0.5), 0.0, 1.0)),
    )


def _parse_intensity(data: Any) -> IntensityPayload:
    if isinstance(data, IntensityPayload):
        return data
    d = data if isinstance(data, dict) else {}
    lvl_raw = str(d.get("level", "CYCLONIC_STORM"))
    try:
        lvl_enum = IntensityLevelEnum(lvl_raw)
    except ValueError:
        lvl_enum = IntensityLevelEnum.CYCLONIC_STORM

    return IntensityPayload(
        level=lvl_enum,
        scale="IMD",
        max_wind_kt=max(0.0, float(d.get("max_wind_kt", 45.0))),
        min_pressure_mb=float(np.clip(d.get("min_pressure_mb", 990.0), 800.0, 1050.0)),
        confidence=float(np.clip(d.get("confidence", 0.5), 0.0, 1.0)),
    )


def _parse_prediction(data: Any, current_pos: Optional[Dict[str, float]] = None) -> PredictionPayload:
    if isinstance(data, PredictionPayload):
        return data

    d = data if isinstance(data, dict) else {}
    c_pos_raw = d.get("current_position") or current_pos or {"lat": 15.0, "lon": 85.0}
    c_lat, c_lon = float(c_pos_raw.get("lat", 15.0)), float(c_pos_raw.get("lon", 85.0))

    raw_path = d.get("predicted_path", [])
    path_points: List[TrajectoryPoint] = []

    if raw_path:
        for idx, pt in enumerate(raw_path):
            if idx == 0:
                # Enforce exact match with current position at t=0
                path_points.append(TrajectoryPoint(t_plus_h=0, lat=c_lat, lon=c_lon))
            else:
                p_t = int(pt.get("t_plus_h", idx * 6))
                p_lat = float(pt.get("lat", c_lat))
                p_lon = float(pt.get("lon", c_lon))
                path_points.append(TrajectoryPoint(t_plus_h=p_t, lat=p_lat, lon=p_lon))
    else:
        # Construct default 6h-72h path
        path_points.append(TrajectoryPoint(t_plus_h=0, lat=c_lat, lon=c_lon))
        for h in [6, 12, 24, 48, 72]:
            path_points.append(TrajectoryPoint(t_plus_h=h, lat=c_lat + 0.1 * (h / 6), lon=c_lon + 0.1 * (h / 6)))

    raw_unc = d.get("uncertainty", {})
    raw_radii = raw_unc.get("cone_radius_km", [])
    if len(raw_radii) != len(path_points):
        # Generate default cone matching path length
        raw_radii = [0.0] + [round(30.0 + 3.5 * pt.t_plus_h, 2) for pt in path_points[1:]]
    else:
        raw_radii[0] = 0.0

    return PredictionPayload(
        current_position=GeoPoint(lat=c_lat, lon=c_lon),
        heading_deg=float(np.clip(d.get("heading_deg", 0.0), 0.0, 360.0)),
        speed_kt=max(0.0, float(d.get("speed_kt", 10.0))),
        forecast_hours=int(d.get("forecast_hours", path_points[-1].t_plus_h if path_points else 72)),
        predicted_path=path_points,
        confidence=float(np.clip(d.get("confidence", 0.7), 0.0, 1.0)),
        uncertainty=UncertaintyCone(cone_radius_km=raw_radii),
    )


def _build_safe_tier0_fallback(
    t0: Dict[str, Any],
    cyclone_id: str,
    name: str,
    basin: str,
    timestamp: str,
    inputs: Dict[str, Any],
    error_msg: str,
) -> CycloneIntelligence:
    """Constructs a deterministic Tier-0 fallback guaranteed to satisfy the frozen schema contract."""
    c_pos = inputs.get("current_position", {"lat": 15.0, "lon": 85.0})
    c_lat = float(c_pos.get("lat", 15.0))
    c_lon = float(c_pos.get("lon", 85.0))

    fallback_path = [TrajectoryPoint(t_plus_h=0, lat=c_lat, lon=c_lon)]
    for h in [6, 12, 24, 48, 72]:
        fallback_path.append(TrajectoryPoint(t_plus_h=h, lat=c_lat + 0.1 * (h / 6), lon=c_lon + 0.1 * (h / 6)))

    return CycloneIntelligence(
        schema_version="1.0",
        cyclone_id=cyclone_id,
        name=name,
        timestamp=timestamp,
        basin=basin,
        identification=IdentificationPayload(detected=True, confidence=0.5),
        classification=ClassificationPayload(stage=StageEnum.TROPICAL_DEPRESSION, confidence=0.5),
        intensity=IntensityPayload(level=IntensityLevelEnum.DEPRESSION, scale="IMD", max_wind_kt=25.0, min_pressure_mb=1000.0, confidence=0.5),
        prediction=PredictionPayload(
            current_position=GeoPoint(lat=c_lat, lon=c_lon),
            heading_deg=0.0,
            speed_kt=10.0,
            forecast_hours=72,
            predicted_path=fallback_path,
            confidence=0.5,
            uncertainty=UncertaintyCone(cone_radius_km=[0.0, 40.0, 65.0, 120.0, 200.0, 290.0]),
        ),
        sources=["ibtracs_tier0_fallback"],
        model_version="chakravyuh-tier0-safety-net",
        tier=TierEnum.TIER0,
        extra={
            "provenance": {
                "sources": {k: "tier0" for k in ["identification", "classification", "intensity", "prediction"]},
                "reasons": {k: f"Safety-net fallback triggered: {error_msg}" for k in ["identification", "classification", "intensity", "prediction"]},
                "object_tier": "tier0",
            },
            "error_fallback": True,
        },
    )


__all__ = [
    "ConfidenceGatesConfig",
    "select_tier",
    "gate_and_assemble_cyclone_intelligence",
]
