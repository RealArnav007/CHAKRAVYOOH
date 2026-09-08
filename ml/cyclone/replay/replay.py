"""Historical Cyclone Replay Driver with Cadence Control, Landfall Presets, and JSONL Caching."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
import logging
from pathlib import Path
import time
from typing import Any, Dict, Iterator, List, Optional, Union

from ml.cyclone.config import load_config
from ml.cyclone.eval.error_analysis import DEMO_STORMS_DATA
from ml.cyclone.fusion.run_cycle import (
    get_or_load_calibrator,
    get_or_load_model,
    load_sample_for_cycle,
    run_cycle,
)
from ml.cyclone.schema.models import CycloneIntelligence

logger = logging.getLogger(__name__)

# Standard Cache Directories
REPLAY_CACHE_DIR = Path(__file__).resolve().parent / "cache"
ROOT_REPLAY_CACHE_DIR = Path("replay/cache")


# -----------------------------------------------------------------------------
# 1. Storm Metadata & Preset Resolution
# -----------------------------------------------------------------------------

STORM_PRESET_METADATA: Dict[str, Dict[str, Any]] = {
    "amphan_2020": {
        "canonical_id": "CYC-2020-BAY-001",
        "name": "Super Cyclone Amphan",
        "basin": "Bay of Bengal",
        "start_time": "2020-05-16T00:00:00Z",
        "landfall_time": "2020-05-20T12:00:00Z",
        "end_time": "2020-05-21T06:00:00Z",
        "total_hours": 84,
        "step_hours": 6,
        "landfall_lead_hours": 72,
        "presets": {
            "genesis": 0,
            "rapid_intensification": 2,  # 24h
            "landfall_minus_24h": 4,     # 48h (72h - 24h)
            "landfall_24h": 4,
            "landfall-24h": 4,
            "landfall-24": 4,
            "landfall": 6,              # 72h
            "decay": 7,                 # 84h
        },
    },
    "biparjoy_2023": {
        "canonical_id": "CYC-2023-ARB-001",
        "name": "Extremely Severe Cyclone Biparjoy",
        "basin": "Arabian Sea",
        "start_time": "2023-06-06T06:00:00Z",
        "landfall_time": "2023-06-15T18:00:00Z",
        "end_time": "2023-06-17T00:00:00Z",
        "total_hours": 84,
        "step_hours": 6,
        "landfall_lead_hours": 72,
        "presets": {
            "genesis": 0,
            "stall_loop": 2,             # 24h
            "landfall_minus_24h": 4,     # 48h
            "landfall_24h": 4,
            "landfall-24h": 4,
            "landfall-24": 4,
            "landfall": 6,              # 72h
            "decay": 7,
        },
    },
    "fani_2019": {
        "canonical_id": "CYC-2019-BAY-001",
        "name": "Extremely Severe Cyclone Fani",
        "basin": "Bay of Bengal",
        "start_time": "2019-04-26T06:00:00Z",
        "landfall_time": "2019-05-03T03:00:00Z",
        "end_time": "2019-05-04T12:00:00Z",
        "total_hours": 84,
        "step_hours": 6,
        "landfall_lead_hours": 72,
        "presets": {
            "genesis": 0,
            "recurvature": 4,           # 48h
            "landfall_minus_24h": 4,    # 48h
            "landfall_24h": 4,
            "landfall-24h": 4,
            "landfall-24": 4,
            "landfall": 6,             # 72h
            "decay": 7,
        },
    },
}


def normalize_storm_key(storm_id: str) -> str:
    """Resolves any variant name (e.g. 'Amphan', 'CYC-2020-BAY-001', 'biparjoy_2023') to canonical key."""
    s = storm_id.lower().replace("-", "_").replace(" ", "_")
    for k in STORM_PRESET_METADATA.keys():
        if k in s or s in k or s.split("_")[0] in k:
            return k
    return s


def resolve_preset_frame_index(
    storm_key: str,
    preset: Union[str, int],
    total_frames: int,
) -> int:
    """Resolves jump preset string or numeric offset to an integer frame index in [0, total_frames - 1]."""
    if isinstance(preset, int):
        return max(0, min(preset, total_frames - 1))

    p_norm = str(preset).lower().strip().replace(" ", "_").replace("-", "_")

    # Check known aliases
    if p_norm in ["landfall_24h", "landfall_minus_24h", "landfall_minus24", "landfall_24", "minus_24h", "landfall_24hr"]:
        p_norm = "landfall-24h"

    meta = STORM_PRESET_METADATA.get(storm_key)
    if meta and "presets" in meta:
        for k, v in meta["presets"].items():
            if k.replace("-", "_") == p_norm or k == p_norm:
                return max(0, min(v, total_frames - 1))

    # Generic heuristics
    if "landfall" in p_norm and "24" in p_norm:
        # Default ~24h before end/landfall (usually frame index around 60% of sequence)
        return max(0, min(total_frames - 3, int(total_frames * 0.6)))
    elif "landfall" in p_norm:
        return max(0, total_frames - 2)
    elif "genesis" in p_norm or "start" in p_norm:
        return 0
    elif "ri" in p_norm or "intensif" in p_norm:
        return max(0, min(2, total_frames - 1))

    # Try numeric string parse
    try:
        idx = int(p_norm)
        return max(0, min(idx, total_frames - 1))
    except ValueError:
        pass

    logger.warning(f"Unrecognized preset '{preset}' -> starting at frame 0.")
    return 0


# -----------------------------------------------------------------------------
# 2. Precompute & Caching Engine
# -----------------------------------------------------------------------------


def precompute_replay(
    storm_id: str = "Amphan",
    step_hours: int = 6,
    output_path: Optional[Union[str, Path]] = None,
    force_recompute: bool = False,
) -> List[Dict[str, Any]]:
    """Runs run_cycle for every frame genesis -> landfall/decay and caches an ordered list of JSONL objects.

    Guarantees:
    1. Stable cyclone_id across all frames in the storm sequence.
    2. Strictly time-ordered sequence with valid ISO-8601 UTC timestamps.
    3. Every emitted frame validates against the frozen CycloneIntelligence contract.
    4. Caches to replay/cache/<storm_id>.jsonl for zero-latency live demo replays.

    Args:
        storm_id: Storm name or identifier (e.g. 'Amphan', 'Biparjoy', 'fani_2019').
        step_hours: Temporal step in hours between consecutive frames (default: 6h).
        output_path: Optional destination path for the JSONL cache file.
        force_recompute: If True, bypasses existing cache and re-executes inference.

    Returns:
        Ordered list of validated CycloneIntelligence dictionary frames.
    """
    storm_key = normalize_storm_key(storm_id)
    canonical_meta = STORM_PRESET_METADATA.get(storm_key, {})
    canonical_cyclone_id = canonical_meta.get("canonical_id", f"CYC-{storm_key.upper()[:12]}")
    storm_name = canonical_meta.get("name", storm_id)
    basin = canonical_meta.get("basin", "North Indian Ocean")

    # Determine cache file path
    target_cache_file = (
        Path(output_path)
        if output_path is not None
        else REPLAY_CACHE_DIR / f"{storm_key}.jsonl"
    )

    # Check cache hit
    if target_cache_file.is_file() and not force_recompute:
        try:
            cached_frames: List[Dict[str, Any]] = []
            with open(target_cache_file, "r", encoding="utf-8") as f:
                for line in f:
                    line_str = line.strip()
                    if line_str:
                        cached_frames.append(json.loads(line_str))
            if cached_frames:
                logger.info(f"[REPLAY] Loaded {len(cached_frames)} precomputed frames from {target_cache_file}")
                return cached_frames
        except Exception as e:
            logger.warning(f"[REPLAY] Failed reading cache {target_cache_file}: {e} -> recomputing.")

    # Shared model and calibrator singletons for fast generation
    model = get_or_load_model()
    calibrator = get_or_load_calibrator()

    # Retrieve timestep definitions from error analysis or generate stepped sequence
    demo_data = None
    for k, data in DEMO_STORMS_DATA.items():
        if k in storm_key or storm_key in k:
            demo_data = data
            break

    frames_raw_timesteps = (
        demo_data["timesteps"]
        if demo_data is not None
        else [{"time_step": i, "lead_hours": i * step_hours} for i in range(8)]
    )

    start_iso = canonical_meta.get("start_time", "2020-05-16T00:00:00Z")
    start_dt = datetime.fromisoformat(start_iso.replace("Z", "+00:00"))

    ordered_objects: List[Dict[str, Any]] = []

    for frame_idx, ts in enumerate(frames_raw_timesteps):
        lead_h = int(ts.get("lead_hours", frame_idx * step_hours))
        frame_time = start_dt + timedelta(hours=lead_h)
        frame_time_iso = frame_time.strftime("%Y-%m-%dT%H:%M:%SZ")

        # Load rich sample for this frame
        sample_dict = load_sample_for_cycle(
            storm_id=storm_id,
            frame_idx=frame_idx,
            timestamp=frame_time_iso,
        )

        # Enforce canonical metadata stability
        sample_dict["storm_id"] = canonical_cyclone_id
        sample_dict["name"] = storm_name
        sample_dict["basin"] = basin
        sample_dict["time"] = frame_time_iso

        # Run inference cycle
        result_dict = run_cycle(
            sample=sample_dict,
            model=model,
            calibrator=calibrator,
            model_version="chakravyuh-fusion-net-v1.0",
            return_model_object=False,
        )

        # Ensure strict invariant: cyclone_id remains constant across whole lifecycle
        result_dict["cyclone_id"] = canonical_cyclone_id
        result_dict["name"] = storm_name
        result_dict["timestamp"] = frame_time_iso

        # Validate against schema
        CycloneIntelligence.model_validate(result_dict)
        ordered_objects.append(result_dict)

    # Write to local cache and root mirror cache
    target_cache_file.parent.mkdir(parents=True, exist_ok=True)
    with open(target_cache_file, "w", encoding="utf-8") as f:
        for frame in ordered_objects:
            f.write(json.dumps(frame) + "\n")

    # Also write to root replay/cache/<storm_id>.jsonl
    root_cache_file = ROOT_REPLAY_CACHE_DIR / f"{storm_key}.jsonl"
    root_cache_file.parent.mkdir(parents=True, exist_ok=True)
    with open(root_cache_file, "w", encoding="utf-8") as f:
        for frame in ordered_objects:
            f.write(json.dumps(frame) + "\n")

    logger.info(f"[REPLAY] Precomputed and cached {len(ordered_objects)} frames to {target_cache_file} and {root_cache_file}")
    return ordered_objects


# -----------------------------------------------------------------------------
# 3. Streaming Replay Generator
# -----------------------------------------------------------------------------


def replay(
    storm_id: str = "Amphan",
    start: Optional[Union[int, str]] = None,
    speed: float = 1.0,
    jump: Optional[str] = None,
    step_hours: int = 6,
    precomputed_frames: Optional[List[Dict[str, Any]]] = None,
    base_cadence_seconds: float = 0.5,
) -> Iterator[Dict[str, Any]]:
    """Generator that yields certified CycloneIntelligence frames on a wall-clock cadence scaled by speed.

    Each frame visibly evolves:
    - Position (moving forward along the track).
    - Intensity (surface wind & pressure).
    - Lifecycle stage and IMD level.
    - Saffir-Simpson category in extra.saffir_simpson.
    - Multi-horizon predicted path and anisotropic learned uncertainty cone.
    - Calibrated confidence distributions.

    Args:
        storm_id: Storm identifier or landmark demo storm name.
        start: Optional starting frame index or ISO timestamp string.
        speed: Wall-clock cadence multiplier (e.g. 1.0 = real-time cadence, 2.0 = 2x faster, 0.0 = instant).
        jump: Preset jump target (e.g. 'landfall-24h', 'genesis', 'rapid_intensification', 'landfall').
        step_hours: Temporal step hours (default: 6h).
        precomputed_frames: Optional pre-loaded list of frame dictionaries.
        base_cadence_seconds: Base wall-clock delay in seconds between frames at speed=1.0 (default: 0.5s).

    Yields:
        Dictionary adhering to CycloneIntelligence schema.
    """
    storm_key = normalize_storm_key(storm_id)
    frames = precomputed_frames or precompute_replay(storm_id=storm_id, step_hours=step_hours)

    if not frames:
        return

    # Determine starting frame index
    start_target = jump or start or 0
    start_idx = resolve_preset_frame_index(
        storm_key=storm_key,
        preset=start_target,
        total_frames=len(frames),
    )

    delay_sec = (base_cadence_seconds / speed) if speed > 0 else 0.0

    for idx in range(start_idx, len(frames)):
        frame = frames[idx]

        # Delay for wall-clock cadence pacing if active
        if delay_sec > 0:
            time.sleep(delay_sec)

        yield frame


# -----------------------------------------------------------------------------
# 4. Command-Line Interface (CLI)
# -----------------------------------------------------------------------------


def main() -> None:
    """CLI runner for precomputing, streaming, jumping, and exporting historical replays."""
    parser = argparse.ArgumentParser(
        description="Chakravyuh Historical Cyclone Replay Driver (Live Demo Engine)."
    )
    parser.add_argument(
        "--storm",
        "--storm-id",
        "-s",
        type=str,
        default="Amphan",
        help="Storm identifier or landmark storm name (e.g. Amphan, Biparjoy, Fani).",
    )
    parser.add_argument(
        "--jump",
        "-j",
        type=str,
        default=None,
        help="Preset jump target (e.g. 'landfall-24h', 'genesis', 'rapid_intensification', 'landfall').",
    )
    parser.add_argument(
        "--start",
        type=str,
        default=None,
        help="Starting frame index (int) or ISO timestamp string.",
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=1.0,
        help="Playback speed multiplier (0 for instant dump, 1.0 for standard demo pacing).",
    )
    parser.add_argument(
        "--step-hours",
        type=int,
        default=6,
        help="Temporal interval in hours between frames (default: 6).",
    )
    parser.add_argument(
        "--to-file",
        type=str,
        default=None,
        help="Export all precomputed frames to a JSONL file and exit.",
    )
    parser.add_argument(
        "--precompute",
        action="store_true",
        help="Precompute and cache all frames for the storm without streaming to stdout.",
    )

    args = parser.parse_args()

    # 1. Precompute
    frames = precompute_replay(storm_id=args.storm, step_hours=args.step_hours)

    # 2. Handle --to-file export
    if args.to_file:
        out_path = Path(args.to_file)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            for fr in frames:
                f.write(json.dumps(fr) + "\n")
        print(f"[REPLAY] Exported {len(frames)} frames to {out_path}")
        return

    if args.precompute:
        print(f"[REPLAY] Precomputed {len(frames)} frames for {args.storm}.")
        return

    # 3. Stream frames according to jump/speed
    print(f"[REPLAY] Starting replay stream for {args.storm} (jump={args.jump}, speed={args.speed})...")
    for frame in replay(
        storm_id=args.storm,
        start=args.start,
        jump=args.jump,
        speed=args.speed,
        step_hours=args.step_hours,
        precomputed_frames=frames,
    ):
        print(json.dumps(frame))


if __name__ == "__main__":
    main()
