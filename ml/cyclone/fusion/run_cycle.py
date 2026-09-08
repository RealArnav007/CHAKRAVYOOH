"""Single public entry point orchestrating multi-modal inference and producing frozen CycloneIntelligence objects."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import torch

from ml.cyclone.config import CycloneConfig, load_config
from ml.cyclone.eval.error_analysis import DEMO_STORMS_DATA
from ml.cyclone.features.fusion import (
    DEFAULT_HORIZONS,
    IMD_LEVEL_MAP,
    STAGE_MAP,
    FusedSample,
    make_fused_sample,
)
from ml.cyclone.fusion.tier_gate import (
    ConfidenceGatesConfig,
    gate_and_assemble_cyclone_intelligence,
)
from ml.cyclone.models import (
    FusionNet,
    ModelCalibrator,
    classify,
    identify,
    intensity,
    predict_cone_radii,
    predict_track,
)
from ml.cyclone.preprocess.geo import calculate_speed_and_heading
from ml.cyclone.preprocess.scales import (
    wind_kt_to_imd_level,
    wind_kt_to_saffir_simpson,
)
from ml.cyclone.schema.models import CycloneIntelligence, TierEnum

logger = logging.getLogger(__name__)

# Global singletons for lazy model and calibration caching
_CACHED_MODEL: Optional[FusionNet] = None
_CACHED_CALIBRATOR: Optional[ModelCalibrator] = None


# -----------------------------------------------------------------------------
# 1. Model & Calibrator Lifecycle Management
# -----------------------------------------------------------------------------


def get_or_load_calibrator(calibration_path: Optional[Union[str, Path]] = None) -> ModelCalibrator:
    """Retrieves or loads the ModelCalibrator parameter singleton."""
    global _CACHED_CALIBRATOR
    if _CACHED_CALIBRATOR is not None and calibration_path is None:
        return _CACHED_CALIBRATOR

    calibrator = ModelCalibrator()

    # Potential calibration artifact paths
    candidate_paths = [
        calibration_path,
        Path(__file__).resolve().parent.parent / "artifacts" / "calibration.json",
        Path("ml/cyclone/artifacts/calibration.json"),
        Path("artifacts/calibration.json"),
    ]

    loaded = False
    for p in candidate_paths:
        if p is not None:
            path_obj = Path(p)
            if path_obj.is_file():
                try:
                    calibrator.load(path_obj)
                    loaded = True
                    break
                except Exception as e:
                    logger.warning(f"Could not load calibration parameters from {path_obj}: {e}")

    if not loaded:
        logger.info("Using default unscaled calibration parameters.")

    if calibration_path is None:
        _CACHED_CALIBRATOR = calibrator

    return calibrator


def get_or_load_model(
    checkpoint_path: Optional[Union[str, Path]] = None,
    device: Optional[Union[str, torch.device]] = None,
) -> FusionNet:
    """Retrieves or loads the FusionNet neural network singleton."""
    global _CACHED_MODEL
    target_device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))

    if _CACHED_MODEL is not None and checkpoint_path is None:
        return _CACHED_MODEL.to(target_device)

    model = FusionNet.from_config()

    # Potential checkpoint paths
    candidate_paths = [
        checkpoint_path,
        Path(__file__).resolve().parent.parent / "artifacts" / "fusion" / "best_fusion_net.pt",
        Path("ml/cyclone/artifacts/fusion/best_fusion_net.pt"),
        Path("artifacts/fusion/best_fusion_net.pt"),
    ]

    loaded = False
    for p in candidate_paths:
        if p is not None:
            path_obj = Path(p)
            if path_obj.is_file():
                try:
                    ckpt = torch.load(path_obj, map_location="cpu")
                    state_dict = ckpt.get("model_state_dict", ckpt)
                    model.load_state_dict(state_dict, strict=False)
                    loaded = True
                    logger.info(f"Successfully loaded FusionNet weights from {path_obj}")
                    break
                except Exception as e:
                    logger.warning(f"Could not load checkpoint from {path_obj}: {e}")

    if not loaded:
        logger.info("FusionNet initialized with configuration defaults.")

    model = model.to(target_device)
    model.eval()

    if checkpoint_path is None:
        _CACHED_MODEL = model

    return model


# -----------------------------------------------------------------------------
# 2. Sample Retrieval & Assembly Helpers
# -----------------------------------------------------------------------------


def load_sample_for_cycle(
    storm_id: Optional[str] = None,
    frame_idx: Optional[int] = None,
    timestamp: Optional[str] = None,
) -> Dict[str, Any]:
    """Retrieves or synthesizes a rich multi-modal sample dictionary for a storm/frame/timestamp."""
    s_id = str(storm_id or "Amphan").strip()
    f_idx = int(frame_idx or 0)
    norm_id = s_id.lower().replace("-", "_").replace(" ", "_")

    # 1. No-detect / Negative background requests
    if norm_id in ["no_detect", "nodetect", "null", "none", "background"] or norm_id.startswith("non_cyclone"):
        no_detect_fixture = Path(__file__).resolve().parent.parent / "fixtures" / "no_detect.json"
        if no_detect_fixture.is_file():
            try:
                with open(no_detect_fixture, "r", encoding="utf-8") as f:
                    fix_data = json.load(f)
                    return {
                        "storm_id": fix_data.get("cyclone_id", "CYC-2026-NIO-NULL"),
                        "name": fix_data.get("name", "Area-of-Interest-42"),
                        "basin": fix_data.get("basin", "North Indian Ocean"),
                        "time": timestamp or fix_data.get("timestamp", "2026-09-08T06:00:00Z"),
                        "lat": 10.5,
                        "lon": 82.0,
                        "wind_kt": 12.0,
                        "pres_mb": 1012.0,
                        "image_available": True,
                        "image_tensor": None,
                        "env": {
                            "sst_c": 28.0,
                            "shear_ms": 15.0,
                            "rh500": 40.0,
                            "vort850": 1.5,
                            "mslp_mb": 1012.0,
                            "wind10m_ms": 5.0,
                        },
                        "history": [],
                    }
            except Exception:
                pass

        return {
            "storm_id": "CYC-2026-NIO-NULL",
            "name": "Area-of-Interest-42",
            "basin": "North Indian Ocean",
            "time": timestamp or "2026-09-08T06:00:00Z",
            "lat": 10.5,
            "lon": 82.0,
            "wind_kt": 12.0,
            "pres_mb": 1012.0,
            "image_available": True,
            "env": {
                "sst_c": 28.0,
                "shear_ms": 15.0,
                "rh500": 40.0,
                "vort850": 1.5,
                "mslp_mb": 1012.0,
                "wind10m_ms": 5.0,
            },
            "history": [],
        }

    # 2. Check landmark demo storms (Amphan, Fani, Biparjoy)
    matched_key = None
    for k in DEMO_STORMS_DATA.keys():
        if k in norm_id or norm_id in k or norm_id.split("_")[0] in k:
            matched_key = k
            break

    if matched_key is not None:
        data = DEMO_STORMS_DATA[matched_key]
        timesteps = data["timesteps"]
        k = max(0, min(f_idx, len(timesteps) - 1))
        ts_info = timesteps[k]

        lat = float(ts_info["true_lat"])
        lon = float(ts_info["true_lon"])
        wind = float(ts_info["true_wind_kt"])
        pres = round(1010.0 - (wind * 0.65), 1)

        # Reconstruct realistic past track history
        history: List[Dict[str, Any]] = []
        for prev_k in range(max(0, k - 4), k + 1):
            prev_ts = timesteps[prev_k]
            p_lat = float(prev_ts["true_lat"])
            p_lon = float(prev_ts["true_lon"])
            p_wind = float(prev_ts["true_wind_kt"])
            p_pres = round(1010.0 - (p_wind * 0.65), 1)
            t_off = float(prev_ts["lead_hours"] - ts_info["lead_hours"])
            history.append({
                "t_offset_h": t_off,
                "lat": p_lat,
                "lon": p_lon,
                "wind_kt": p_wind,
                "pres_mb": p_pres,
                "speed_kt": 10.0,
                "heading_deg": 350.0,
            })

        year_str = "2020" if "amphan" in matched_key else ("2019" if "fani" in matched_key else "2023")
        time_str = timestamp or f"{year_str}-05-18T{ts_info['lead_hours']:02d}:00:00Z"

        return {
            "storm_id": f"CYC-{year_str}-{matched_key.upper()[:3]}",
            "name": data["name"].split(" (")[0],
            "basin": data["basin"],
            "time": time_str,
            "lat": lat,
            "lon": lon,
            "wind_kt": wind,
            "pres_mb": pres,
            "image_available": ts_info.get("image_available", True),
            "env": {
                "sst_c": 29.8,
                "shear_ms": 6.5,
                "rh500": 72.0,
                "vort850": 9.2,
                "mslp_mb": pres,
                "wind10m_ms": round(wind * 0.514, 1),
            },
            "history": history,
        }

    # 3. Check fixtures
    fixture_map = {
        "early_stage": "early_stage.json",
        "landfall_imminent": "landfall_imminent.json",
    }
    if norm_id in fixture_map:
        fix_p = Path(__file__).resolve().parent.parent / "fixtures" / fixture_map[norm_id]
        if fix_p.is_file():
            with open(fix_p, "r", encoding="utf-8") as f:
                d = json.load(f)
                return {
                    "storm_id": d.get("cyclone_id", s_id),
                    "name": d.get("name", s_id),
                    "basin": d.get("basin", "North Indian Ocean"),
                    "time": timestamp or d.get("timestamp", "2026-09-08T06:00:00Z"),
                    "lat": d.get("prediction", {}).get("current_position", {}).get("lat", 15.0) if d.get("prediction") else 15.0,
                    "lon": d.get("prediction", {}).get("current_position", {}).get("lon", 85.0) if d.get("prediction") else 85.0,
                    "wind_kt": d.get("intensity", {}).get("max_wind_kt", 45.0),
                    "pres_mb": d.get("intensity", {}).get("min_pressure_mb", 992.0),
                    "image_available": True,
                    "env": {"sst_c": 29.0, "shear_ms": 8.0, "rh500": 65.0, "vort850": 6.0, "mslp_mb": 992.0, "wind10m_ms": 18.0},
                    "history": [],
                }

    # 4. Default synthetic live storm sample
    return {
        "storm_id": s_id,
        "name": s_id,
        "basin": "North Indian Ocean",
        "time": timestamp or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "lat": 14.5 + 0.2 * f_idx,
        "lon": 86.5 + 0.1 * f_idx,
        "wind_kt": 55.0,
        "pres_mb": 988.0,
        "image_available": True,
        "env": {
            "sst_c": 29.5,
            "shear_ms": 7.5,
            "rh500": 68.0,
            "vort850": 7.8,
            "mslp_mb": 988.0,
            "wind10m_ms": 22.0,
        },
        "history": [
            {"t_offset_h": -6.0, "lat": 14.3 + 0.2 * f_idx, "lon": 86.4 + 0.1 * f_idx, "wind_kt": 50.0, "pres_mb": 992.0, "speed_kt": 10.0, "heading_deg": 350.0},
            {"t_offset_h": 0.0, "lat": 14.5 + 0.2 * f_idx, "lon": 86.5 + 0.1 * f_idx, "wind_kt": 55.0, "pres_mb": 988.0, "speed_kt": 11.0, "heading_deg": 355.0},
        ],
    }


# -----------------------------------------------------------------------------
# 3. Master Public Entry Point: run_cycle()
# -----------------------------------------------------------------------------


def run_cycle(
    timestamp: Optional[Union[str, datetime]] = None,
    storm_id: Optional[str] = None,
    frame: Optional[int] = None,
    frame_idx: Optional[int] = None,
    storm: Optional[str] = None,
    sample: Optional[Dict[str, Any]] = None,
    model: Optional[FusionNet] = None,
    calibrator: Optional[ModelCalibrator] = None,
    gates_config: Optional[Union[ConfidenceGatesConfig, Dict[str, Any]]] = None,
    model_version: str = "chakravyuh-fusion-net-v1.0",
    device: Optional[Union[str, torch.device]] = None,
    return_model_object: bool = False,
) -> Union[Dict[str, Any], CycloneIntelligence]:
    """Single public entry point orchestrating a complete cycle of the Chakravyuh Cyclone Brain.

    Workflow:
    1. Loads/assembles the multi-modal fused sample (image, ERA5 scalars, GRU track sequence).
    2. Runs Tier-1 FusionNet (with temperature scaling & variance recalibration) and Tier-0 baselines.
    3. Applies per-field confidence and variance tier gating (tier_gate.py).
    4. Maps sustained wind to IMD level and Saffir-Simpson category; derives anisotropic cone.
    5. Populates active sources, model_version, execution tier, and provenance metadata.
    6. Validates against CycloneIntelligence schema before returning.

    Args:
        timestamp: Optional ISO-8601 UTC timestamp string or datetime.
        storm_id: Optional unique storm identifier or demo storm name (e.g. 'Amphan', 'Biparjoy').
        frame: Optional integer frame index offset.
        frame_idx: Alias for frame.
        storm: Alias for storm_id.
        sample: Optional pre-assembled raw sample dictionary.
        model: Optional pre-loaded FusionNet model instance.
        calibrator: Optional pre-loaded ModelCalibrator instance.
        gates_config: Optional threshold configuration for tier gating.
        model_version: String tag for model release version.
        device: PyTorch computing device ('cpu' or 'cuda').
        return_model_object: If True, returns pydantic CycloneIntelligence object; else validated dict.

    Returns:
        Validated dictionary (or CycloneIntelligence object) adhering to the frozen schema contract.
    """
    # 1. Resolve arguments
    target_storm_id = storm or storm_id
    target_frame = frame if frame is not None else frame_idx

    ts_str: Optional[str] = None
    if isinstance(timestamp, datetime):
        ts_str = timestamp.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    elif isinstance(timestamp, str):
        ts_str = timestamp if (timestamp.endswith("Z") or "+" in timestamp) else timestamp + "Z"

    # 2. Retrieve / synthesize sample dict
    if sample is not None:
        raw_sample = dict(sample)
    else:
        raw_sample = load_sample_for_cycle(storm_id=target_storm_id, frame_idx=target_frame, timestamp=ts_str)

    # Reconcile timestamp
    sample_time = raw_sample.get("time") or raw_sample.get("timestamp") or ts_str
    if sample_time:
        if isinstance(sample_time, datetime):
            final_ts = sample_time.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        else:
            final_ts = str(sample_time)
            if not final_ts.endswith("Z") and not ("+" in final_ts or "-" in final_ts[10:]):
                final_ts = final_ts + "Z"
    else:
        final_ts = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    raw_sample["time"] = final_ts

    # 3. Assemble FusedSample tensors
    fused: FusedSample = make_fused_sample(raw_sample)

    current_lat = float(fused.meta["lat"])
    current_lon = float(fused.meta["lon"])
    has_image = bool(raw_sample.get("image_available", True)) and (
        fused.image_tensor is not None or raw_sample.get("image_available") is True or "image" in raw_sample
    )
    has_env = bool(raw_sample.get("env_available", False)) or (
        raw_sample.get("env") is not None and bool(raw_sample.get("env"))
    )

    # Input availability dict for gating
    inputs_dict = {
        "image_available": has_image,
        "image": fused.image_tensor,
        "env_available": has_env,
        "env_vector": fused.env_vector,
        "track_available": True,
        "track_sequence": fused.track_sequence,
        "current_position": {"lat": current_lat, "lon": current_lon},
        "wind_kt": float(raw_sample.get("wind_kt", 0.0)),
        "pres_mb": float(raw_sample.get("pres_mb", 1010.0)),
        "history": raw_sample.get("history", []),
    }

    # 4. Run Tier-0 Deterministic Baselines
    try:
        ident_t0 = identify(raw_sample)
        class_t0 = classify(raw_sample)
        int_t0 = intensity(raw_sample)

        hist_for_track = raw_sample.get("history") or [
            {"lat": current_lat, "lon": current_lon, "wind_kt": raw_sample.get("wind_kt", 25.0), "pres_mb": raw_sample.get("pres_mb", 1005.0)}
        ]
        pred_t0 = predict_track(history=hist_for_track, horizons=[0, 6, 12, 24, 48, 72])
    except Exception as e:
        logger.error(f"[RUN_CYCLE] Error computing Tier-0 baselines: {e}")
        ident_t0 = {"detected": True, "confidence": 0.50}
        class_t0 = {"stage": "TROPICAL_DEPRESSION", "confidence": 0.50}
        int_t0 = {"level": "DEPRESSION", "scale": "IMD", "max_wind_kt": 25.0, "min_pressure_mb": 1000.0, "confidence": 0.50}
        pred_t0 = {
            "current_position": {"lat": current_lat, "lon": current_lon},
            "heading_deg": 0.0,
            "speed_kt": 10.0,
            "forecast_hours": 72,
            "predicted_path": [{"t_plus_h": h, "lat": current_lat + 0.1 * (h / 6), "lon": current_lon + 0.1 * (h / 6)} for h in [0, 6, 12, 24, 48, 72]],
            "confidence": 0.50,
            "uncertainty": {"cone_radius_km": [0.0, 40.0, 65.0, 120.0, 200.0, 290.0]},
        }

    tier0_payload = {
        "cyclone_id": str(raw_sample.get("storm_id", target_storm_id or "CYC-LIVE-001")),
        "name": str(raw_sample.get("name", "INVEST-SYSTEM")),
        "basin": str(raw_sample.get("basin", "North Indian Ocean")),
        "identification": ident_t0,
        "classification": class_t0,
        "intensity": int_t0,
        "prediction": pred_t0,
    }

    # 5. Run Tier-1 Neural FusionNet (with Calibration)
    net = model or get_or_load_model(device=device)
    calibrator_inst = calibrator or get_or_load_calibrator()
    target_dev = next(net.parameters()).device

    tier1_payload: Optional[Dict[str, Any]] = None
    cal_imd_probs_arr: Optional[np.ndarray] = None
    cal_stage_probs_arr: Optional[np.ndarray] = None

    try:
        # Prepare batch tensors
        if fused.image_tensor is not None:
            img_t = torch.from_numpy(fused.image_tensor).unsqueeze(0).to(dtype=torch.float32, device=target_dev)
            img_avail_t = torch.tensor([1.0], dtype=torch.float32, device=target_dev)
        else:
            img_t = torch.zeros((1, 1, 224, 224), dtype=torch.float32, device=target_dev)
            img_avail_t = torch.tensor([0.0], dtype=torch.float32, device=target_dev)

        env_t = torch.from_numpy(fused.env_vector).unsqueeze(0).to(dtype=torch.float32, device=target_dev)
        track_t = torch.from_numpy(fused.track_sequence).unsqueeze(0).to(dtype=torch.float32, device=target_dev)

        net.eval()
        with torch.no_grad():
            t1_out = net(
                img=img_t,
                env_vector=env_t,
                track_sequence=track_t,
                image_available=img_avail_t,
            )

        # 5.1 Calibrated Detection Head
        raw_det_logits = t1_out["detection_logits"].detach().cpu().numpy()
        cal_det_prob = float(calibrator_inst.detection_scaler.predict_proba(raw_det_logits, is_binary=True)[0, 0])
        t1_detected = bool(cal_det_prob >= 0.50)
        t1_det_conf = round(cal_det_prob, 2)

        # 5.2 Calibrated Stage Classification Head
        raw_stage_logits = t1_out["stage_logits"].detach().cpu().numpy()
        cal_stage_probs_arr = calibrator_inst.stage_scaler.predict_proba(raw_stage_logits, is_binary=False)[0]
        pred_stage_idx = int(np.argmax(cal_stage_probs_arr))
        stage_keys = list(STAGE_MAP.keys())
        pred_stage_enum = stage_keys[pred_stage_idx] if pred_stage_idx < len(stage_keys) else stage_keys[0]
        stage_conf = round(float(np.clip(cal_stage_probs_arr[pred_stage_idx], 0.05, 0.99)), 2)

        # 5.3 Calibrated Intensity Estimation Head
        pred_wind_kt = round(max(0.0, float(t1_out["intensity"]["wind_kt"].squeeze().item())), 1)
        pred_pres_mb = round(float(np.clip(t1_out["intensity"]["pres_mb"].squeeze().item(), 800.0, 1050.0)), 1)
        raw_imd_logits = t1_out["intensity"]["imd_logits"].detach().cpu().numpy()
        cal_imd_probs_arr = calibrator_inst.intensity_scaler.predict_proba(raw_imd_logits, is_binary=False)[0]
        pred_imd_level = wind_kt_to_imd_level(pred_wind_kt)
        int_conf = round(float(np.clip(np.max(cal_imd_probs_arr), 0.05, 0.99)), 2)

        # 5.4 Calibrated Trajectory Forecasting Head & Uncertainty Cone
        deltas = t1_out["track"]["deltas"].squeeze(0).detach().cpu().numpy()  # (5, 2)
        log_vars = t1_out["track"]["log_vars"].squeeze(0).detach().cpu().numpy()  # (5, 2)

        predicted_path: List[Dict[str, Any]] = [
            {"t_plus_h": 0, "lat": round(current_lat, 4), "lon": round(current_lon, 4)}
        ]
        for h_idx, h in enumerate(DEFAULT_HORIZONS):
            f_lat = round(current_lat + float(deltas[h_idx, 0]), 4)
            f_lon = round((current_lon + float(deltas[h_idx, 1]) + 540.0) % 360.0 - 180.0, 4)
            predicted_path.append({"t_plus_h": h, "lat": f_lat, "lon": f_lon})

        # Recalibrate Cone Radii
        raw_radii = predict_cone_radii(log_vars, current_lat=current_lat)
        cal_radii = calibrator_inst.cone_recalibrator.recalibrate_radii(raw_radii)
        cal_radii[0] = 0.0

        # Kinematics
        if len(predicted_path) >= 2:
            calc_speed, calc_heading = calculate_speed_and_heading(
                lat1=current_lat, lon1=current_lon, lat2=predicted_path[1]["lat"], lon2=predicted_path[1]["lon"], delta_hours=6.0
            )
        else:
            calc_speed, calc_heading = 10.0, 0.0

        track_conf = round(float(np.clip(0.85 - (0.02 * float(np.mean(log_vars))), 0.40, 0.95)), 2)

        tier1_payload = {
            "cyclone_id": str(raw_sample.get("storm_id", target_storm_id or "CYC-LIVE-001")),
            "name": str(raw_sample.get("name", "INVEST-SYSTEM")),
            "basin": str(raw_sample.get("basin", "North Indian Ocean")),
            "identification": {
                "detected": t1_detected,
                "confidence": t1_det_conf,
            },
            "classification": {
                "stage": pred_stage_enum.value,
                "confidence": stage_conf,
            },
            "intensity": {
                "level": pred_imd_level.value,
                "scale": "IMD",
                "max_wind_kt": pred_wind_kt,
                "min_pressure_mb": pred_pres_mb,
                "confidence": int_conf,
            },
            "prediction": {
                "current_position": {"lat": round(current_lat, 4), "lon": round(current_lon, 4)},
                "heading_deg": round(calc_heading, 1),
                "speed_kt": round(calc_speed, 1),
                "forecast_hours": DEFAULT_HORIZONS[-1],
                "predicted_path": predicted_path,
                "confidence": track_conf,
                "uncertainty": {"cone_radius_km": cal_radii},
                "max_log_var": float(np.max(log_vars)),
            },
        }

    except Exception as e:
        logger.error(f"[RUN_CYCLE] Tier-1 FusionNet inference exception: {e} -> Degrading to Tier-0.")
        tier1_payload = None

    # 6. Format Supplemental Metadata (extra)
    # Class probability distributions
    imd_class_probs: Dict[str, float] = {}
    if cal_imd_probs_arr is not None and len(cal_imd_probs_arr) == len(IMD_LEVEL_MAP):
        for idx, lvl in enumerate(IMD_LEVEL_MAP.keys()):
            imd_class_probs[lvl.value] = round(float(cal_imd_probs_arr[idx]), 4)
    else:
        for lvl in IMD_LEVEL_MAP.keys():
            imd_class_probs[lvl.value] = 0.90 if lvl == tier0_payload["intensity"]["level"] else 0.016

    stage_class_probs: Dict[str, float] = {}
    if cal_stage_probs_arr is not None and len(cal_stage_probs_arr) == len(STAGE_MAP):
        for idx, stg in enumerate(STAGE_MAP.keys()):
            stage_class_probs[stg.value] = round(float(cal_stage_probs_arr[idx]), 4)
    else:
        for stg in STAGE_MAP.keys():
            stage_class_probs[stg.value] = 0.90 if stg == tier0_payload["classification"]["stage"] else 0.02

    extra_metadata = {
        "intensity_class_probs": imd_class_probs,
        "stage_class_probs": stage_class_probs,
    }

    # 7. Apply Tier Gating & Contract Assembly
    intelligence_obj = gate_and_assemble_cyclone_intelligence(
        tier1_payload=tier1_payload,
        tier0_payload=tier0_payload,
        inputs=inputs_dict,
        config=gates_config,
        cyclone_id=str(raw_sample.get("storm_id", target_storm_id or "CYC-LIVE-001")),
        name=str(raw_sample.get("name", "INVEST-SYSTEM")),
        basin=str(raw_sample.get("basin", "North Indian Ocean")),
        timestamp=final_ts,
        model_version=model_version,
        extra=extra_metadata,
    )

    # 8. Final Schema Verification
    validated_dict = intelligence_obj.to_validated_dict()

    if return_model_object:
        return intelligence_obj

    return validated_dict


# -----------------------------------------------------------------------------
# 4. Command-Line Interface (CLI)
# -----------------------------------------------------------------------------


def main() -> None:
    """Command-line interface for running a cyclone intelligence cycle and emitting formatted JSON."""
    parser = argparse.ArgumentParser(
        description="Run Chakravyuh Cyclone Intelligence Cycle and emit certified CycloneIntelligence JSON."
    )
    parser.add_argument(
        "--storm",
        "--storm-id",
        "-s",
        type=str,
        default="Amphan",
        help="Storm identifier or landmark storm name (e.g. Amphan, Fani, Biparjoy, no_detect).",
    )
    parser.add_argument(
        "--frame",
        "--frame-idx",
        "-f",
        type=int,
        default=0,
        help="Frame / timestep index (default: 0).",
    )
    parser.add_argument(
        "--timestamp",
        "-t",
        type=str,
        default=None,
        help="Optional ISO-8601 UTC timestamp string.",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="JSON indentation for pretty-printing (default: 2).",
    )

    args = parser.parse_args()

    # Execute cycle
    result_dict = run_cycle(
        storm_id=args.storm,
        frame=args.frame,
        timestamp=args.timestamp,
    )

    # Output formatted JSON to stdout
    print(json.dumps(result_dict, indent=args.indent))


if __name__ == "__main__":
    main()
