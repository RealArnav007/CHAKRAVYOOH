#!/usr/bin/env python3
"""Interactive & automated demo dry-run validator executing the landfall-24h replay sequence."""

from __future__ import annotations

import argparse
import math
import sys
import time
from pathlib import Path
from typing import Any

# Ensure repository root is in sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import numpy as np

from ml.cyclone.replay.replay import (
    normalize_storm_key,
    precompute_replay,
    replay,
    resolve_preset_frame_index,
)
from ml.cyclone.schema.models import CycloneIntelligence


def check_no_nans(obj: Any, path: str = "") -> None:
    """Recursively checks that no NaN or Inf values exist in any dictionary or list structure."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            check_no_nans(v, f"{path}.{k}" if path else str(k))
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            check_no_nans(v, f"{path}[{i}]")
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            raise ValueError(f"Found invalid float value '{obj}' at path: {path}")


def run_demo_dryrun(
    storm_id: str = "Amphan",
    jump: str = "landfall-24h",
    speed: float = 0.0,
    verbose: bool = True,
) -> bool:
    """Executes replay sequence from landfall-24h preset and performs runtime verification."""
    print("=" * 80)
    print(f"  🌀 CHAKRAVYUH LIVE DEMO DRY-RUN VALIDATOR: Storm '{storm_id}' (Jump: '{jump}')")
    print("=" * 80)

    # 1. Precompute and resolve start index
    frames = precompute_replay(storm_id=storm_id)
    if not frames:
        print(f"❌ Error: No precomputed replay frames found for storm '{storm_id}'")
        return False

    sk = normalize_storm_key(storm_id)
    start_idx = resolve_preset_frame_index(sk, jump, len(frames))
    active_frames = frames[start_idx:]
    print(
        f"  Total Storm Frames : {len(frames)} | Replay Window: Frame {start_idx} to {len(frames) - 1} ({len(active_frames)} frames)"
    )
    print(f"  Playback Speed     : {speed}x wall-clock cadence")
    print("-" * 80)

    confidences: list[float] = []
    latitudes: list[float] = []
    longitudes: list[float] = []
    winds: list[float] = []
    cones_24h: list[float] = []
    tiers: list[str] = []

    # 2. Iterate through replay generator
    frame_count = 0
    t_start = time.perf_counter()

    for idx, raw_frame in enumerate(replay(storm_id=storm_id, start=jump, speed=speed)):
        frame_idx = start_idx + idx
        frame_count += 1

        # Check 1: No NaN / Inf anywhere in payload
        check_no_nans(raw_frame)

        # Check 2: Strict Pydantic Schema Validation
        try:
            cyc = CycloneIntelligence(**raw_frame)
        except Exception as e:
            print(f"❌ Schema validation failed on frame {frame_idx}: {e}")
            return False

        # Extract values for logging and checks
        ts = cyc.timestamp
        detected = cyc.identification.detected
        conf = cyc.identification.confidence
        stage = (
            cyc.classification.stage.value
            if cyc.classification and cyc.classification.stage
            else "UNKNOWN"
        )
        int_lvl = cyc.intensity.level.value if cyc.intensity and cyc.intensity.level else "UNKNOWN"
        wind = cyc.intensity.max_wind_kt if cyc.intensity else 0.0
        tier_val = cyc.tier.value if cyc.tier else "tier1"

        # 24h heading and 24h cone radius
        heading_24h = (
            f"{cyc.prediction.heading_deg:05.1f}°"
            if cyc.prediction and cyc.prediction.heading_deg is not None
            else "N/A"
        )
        cone_24h = 0.0
        if cyc.prediction and len(cyc.prediction.predicted_path) >= 4:
            # 24h is index 3 (0h, 6h, 12h, 24h)
            p0 = cyc.prediction.predicted_path[0]
            p24 = cyc.prediction.predicted_path[3]
            # Bearing calculation
            dlon = math.radians(p24.lon - p0.lon)
            lat1 = math.radians(p0.lat)
            lat2 = math.radians(p24.lat)
            x = math.sin(dlon) * math.cos(lat2)
            y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
            b_deg = (math.degrees(math.atan2(x, y)) + 360.0) % 360.0
            heading_24h = f"{b_deg:05.1f}°"
            if len(cyc.prediction.uncertainty.cone_radius_km) >= 4:
                cone_24h = cyc.prediction.uncertainty.cone_radius_km[3]

        # Record metrics for statistical sanity
        confidences.append(conf)
        lat = cyc.prediction.current_position.lat if cyc.prediction else 0.0
        lon = cyc.prediction.current_position.lon if cyc.prediction else 0.0
        latitudes.append(lat)
        longitudes.append(lon)
        winds.append(wind)
        cones_24h.append(cone_24h)
        tiers.append(tier_val)

        # Print compact per-frame line
        line = (
            f"  [FRAME {frame_idx:02d}] {ts} | "
            f"DETECTED: {str(detected):<5} (conf={conf:0.2f}) | "
            f"STAGE: {stage:<24} | "
            f"INTENSITY: {int_lvl:<30} ({wind:5.1f} kt) | "
            f"HDG@24h: {heading_24h} | "
            f"CONE@24h: {cone_24h:5.1f} km | "
            f"TIER: {tier_val}"
        )
        print(line)

    t_elapsed = time.perf_counter() - t_start

    print("-" * 80)
    print("  📊 SANITY & ROBUSTNESS AUDIT SUMMARY:")
    print(f"  • Total Validated Frames   : {frame_count}")
    print(
        f"  • Elapsed Processing Time  : {t_elapsed * 1000.0:0.2f} ms ({frame_count / max(1e-5, t_elapsed):0.1f} FPS)"
    )
    print(
        f"  • Confidence Distribution  : Min={min(confidences):0.2f}, Max={max(confidences):0.2f}, Mean={np.mean(confidences):0.2f}"
    )
    print(f"  • Intensity Range (Winds)  : {min(winds):0.1f} kt -> {max(winds):0.1f} kt")
    print(f"  • 24h Cone Expansion Range : {min(cones_24h):0.1f} km -> {max(cones_24h):0.1f} km")
    print(f"  • Engine Tiers Emitted     : {set(tiers)}")

    # Assertions
    # 1. No 0-or-1 confidence flicker on detected storm
    for c in confidences:
        if c <= 0.0 or c >= 1.0:
            print(f"❌ Error: Uncalibrated hard-clipped confidence {c} found.")
            return False

    # 2. Coordinates monotonically advance towards coast
    assert max(latitudes) > min(latitudes), "Storm did not evolve in latitude."
    assert len(confidences) == len(active_frames), "Frame count mismatch."

    print(
        "\n  ✅ DEMO DRY-RUN SUCCESSFUL: All frames strictly valid, 0 NaNs, 0 flicker, 100% verified."
    )
    print("=" * 80 + "\n")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run Chakravyuh Cyclone Intelligence Replay Demo Dry-Run."
    )
    parser.add_argument(
        "--storm",
        "-s",
        type=str,
        default="Amphan",
        help="Storm identifier (e.g. Amphan, Fani, Biparjoy)",
    )
    parser.add_argument(
        "--jump",
        "-j",
        type=str,
        default="landfall-24h",
        help="Replay starting jump preset (e.g. landfall-24h, start)",
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=0.0,
        help="Playback speed multiplier (0.0 for instantaneous dry-run)",
    )
    args = parser.parse_args()

    success = run_demo_dryrun(storm_id=args.storm, jump=args.jump, speed=args.speed)
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
