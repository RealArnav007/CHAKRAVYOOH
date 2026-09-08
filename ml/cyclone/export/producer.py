"""Producer engine transmitting validated CycloneIntelligence payloads via HTTP POST, atomic file-drop, and JSONL."""

from __future__ import annotations

import argparse
import json
import logging
import os
import time
from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

from ml.cyclone.config import load_config
from ml.cyclone.replay.replay import normalize_storm_key, replay
from ml.cyclone.schema.models import CycloneIntelligence

logger = logging.getLogger(__name__)

DEFAULT_PRODUCER_ENDPOINT = "http://localhost:8000/api/v1/cyclone/intelligence"
DEFAULT_DROP_DIRECTORY = "ml/cyclone/data/replay_feed"


# -----------------------------------------------------------------------------
# 1. Configuration & Credential Resolution
# -----------------------------------------------------------------------------


def get_producer_endpoint(explicit_endpoint: str | None = None) -> str:
    """Resolves target backend ingestion endpoint from environment variable, config, or default."""
    if explicit_endpoint:
        return explicit_endpoint

    env_endpoint = os.environ.get("CHAKRAVYUH_PRODUCER_ENDPOINT") or os.environ.get(
        "CYCLONE_PRODUCER_ENDPOINT"
    )
    if env_endpoint:
        return env_endpoint

    try:
        cfg = load_config()
        if hasattr(cfg, "replay") and hasattr(cfg.replay, "playback"):
            cfg_ep = getattr(cfg.replay.playback, "producer_endpoint", None)
            if cfg_ep:
                return str(cfg_ep)
    except Exception:
        pass

    return DEFAULT_PRODUCER_ENDPOINT


def get_auth_header(explicit_auth: str | None = None) -> str | None:
    """Resolves API token / Authorization header from environment variable, config, or None."""
    if explicit_auth:
        return explicit_auth

    env_auth = (
        os.environ.get("CHAKRAVYUH_PRODUCER_AUTH")
        or os.environ.get("CHAKRAVYUH_AUTH_HEADER")
        or os.environ.get("CHAKRAVYUH_API_KEY")
    )
    if env_auth:
        if not env_auth.startswith("Bearer ") and not env_auth.startswith("ApiKey "):
            return f"Bearer {env_auth}"
        return env_auth

    return None


def get_watch_directory(explicit_dir: str | Path | None = None) -> Path:
    """Resolves target directory for atomic file-drop mode."""
    if explicit_dir:
        return Path(explicit_dir)

    env_dir = os.environ.get("CHAKRAVYUH_DROP_DIRECTORY") or os.environ.get("CHAKRAVYUH_WATCH_DIR")
    if env_dir:
        return Path(env_dir)

    try:
        cfg = load_config()
        if hasattr(cfg, "replay") and hasattr(cfg.replay, "playback"):
            cfg_dir = getattr(cfg.replay.playback, "drop_directory", None)
            if cfg_dir:
                return Path(cfg_dir)
    except Exception:
        pass

    return Path(DEFAULT_DROP_DIRECTORY)


# -----------------------------------------------------------------------------
# 2. Producer Output Handlers
# -----------------------------------------------------------------------------


def write_jsonl(
    objects: Sequence[dict[str, Any] | CycloneIntelligence],
    path: str | Path,
) -> Path:
    """Exports a sequence of CycloneIntelligence objects to a JSONL file.

    Args:
        objects: Sequence of CycloneIntelligence dicts or model instances.
        path: Target file path.

    Returns:
        Path to written JSONL file.
    """
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, "w", encoding="utf-8") as f:
        for obj in objects:
            payload = obj.to_dict() if hasattr(obj, "to_dict") else obj
            f.write(json.dumps(payload) + "\n")

    logger.info(f"[PRODUCER] Wrote {len(objects)} JSONL records to {out_path}")
    return out_path


def post_frame(
    obj: dict[str, Any] | CycloneIntelligence,
    endpoint: str | None = None,
    auth_header: str | None = None,
    max_retries: int = 3,
    backoff_factor: float = 0.5,
    timeout_seconds: float = 5.0,
) -> bool:
    """POSTs a single CycloneIntelligence frame to the backend ingestion endpoint with retry and backoff.

    Args:
        obj: CycloneIntelligence dict or model instance.
        endpoint: Destination HTTP endpoint (defaults to config/env).
        auth_header: Optional Authorization header string.
        max_retries: Number of retry attempts on network or 5xx server errors.
        backoff_factor: Exponential backoff delay multiplier.
        timeout_seconds: HTTP request timeout in seconds.

    Returns:
        True if accepted (2xx HTTP response), False otherwise.
    """
    target_url = get_producer_endpoint(endpoint)
    auth = get_auth_header(auth_header)
    payload = obj.to_dict() if hasattr(obj, "to_dict") else obj

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Chakravyuh-Cyclone-Producer/1.0",
    }
    if auth:
        headers["Authorization"] = auth

    c_id = payload.get("cyclone_id", "UNKNOWN")
    ts = payload.get("timestamp", "")

    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.post(
                target_url,
                json=payload,
                headers=headers,
                timeout=timeout_seconds,
            )

            if resp.status_code in [200, 201, 202, 204]:
                logger.info(
                    f"[PRODUCER] Successfully POSTed frame {c_id} ({ts}) to {target_url} [HTTP {resp.status_code}]"
                )
                return True
            elif resp.status_code >= 500:
                logger.warning(
                    f"[PRODUCER] Server error {resp.status_code} posting frame {c_id} (attempt {attempt}/{max_retries}): {resp.text}"
                )
            else:
                logger.error(
                    f"[PRODUCER] Client error {resp.status_code} posting frame {c_id}: {resp.text}"
                )
                return False

        except (requests.ConnectionError, requests.Timeout) as e:
            logger.warning(
                f"[PRODUCER] Network error posting frame {c_id} to {target_url} (attempt {attempt}/{max_retries}): {e}"
            )

        if attempt < max_retries:
            sleep_duration = backoff_factor * (2 ** (attempt - 1))
            time.sleep(sleep_duration)

    logger.error(
        f"[PRODUCER] Exhausted {max_retries} attempts posting frame {c_id} to {target_url}."
    )
    return False


def file_drop(
    obj: dict[str, Any] | CycloneIntelligence,
    watch_dir: str | Path | None = None,
    filename: str | None = None,
    keep_latest_symlink: bool = True,
) -> Path:
    """Performs an atomic file-drop write of one CycloneIntelligence frame to the watched directory.

    Guarantees:
    - Writes initially to a hidden `.tmp` file and performs an atomic rename to prevent consumer race conditions.
    - Updates a `latest.json` atomic file in the watch directory for polling consumers.

    Args:
        obj: CycloneIntelligence dict or model instance.
        watch_dir: Destination directory being watched by downstream consumers.
        filename: Optional custom filename (defaults to '{cyclone_id}_{timestamp_slug}.json').
        keep_latest_symlink: If True, also updates 'latest.json' in watch_dir.

    Returns:
        Path to the dropped JSON file.
    """
    target_dir = get_watch_directory(watch_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    payload = obj.to_dict() if hasattr(obj, "to_dict") else obj
    c_id = payload.get("cyclone_id", "CYC-FRAME").replace(" ", "_")
    ts_str = (
        payload.get("timestamp", datetime.now(timezone.utc).isoformat())
        .replace(":", "-")
        .replace("Z", "")
    )

    if filename is None:
        target_name = f"{c_id}_{ts_str}.json"
    else:
        target_name = filename

    dest_file = target_dir / target_name
    tmp_file = target_dir / f".{target_name}.tmp"

    # Atomic write pattern: write to tmp then atomic rename
    with open(tmp_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    tmp_file.replace(dest_file)
    logger.info(f"[PRODUCER] Atomic file drop completed -> {dest_file}")

    if keep_latest_symlink:
        latest_file = target_dir / "latest.json"
        latest_tmp = target_dir / ".latest.json.tmp"
        with open(latest_tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        latest_tmp.replace(latest_file)

    return dest_file


# -----------------------------------------------------------------------------
# 3. Master Replay -> Producer Pipeline Runner
# -----------------------------------------------------------------------------


def run_producer(
    storm_id: str = "Amphan",
    mode: str = "both",
    speed: float = 1.0,
    jump: str | None = None,
    step_hours: int = 6,
    endpoint: str | None = None,
    auth_header: str | None = None,
    watch_dir: str | Path | None = None,
    output_jsonl_path: str | Path | None = None,
    max_frames: int | None = None,
) -> dict[str, Any]:
    """Drives the historical replay stream into target production channels (POST, file-drop, and/or JSONL).

    Args:
        storm_id: Storm name or identifier (e.g. 'Amphan', 'Biparjoy').
        mode: Transmission channel: 'post', 'file', 'both', or 'jsonl'.
        speed: Playback speed multiplier (0 for instant dump, 1.0 for real-time demo pacing).
        jump: Preset jump target (e.g. 'landfall-24h', 'genesis', 'rapid_intensification').
        step_hours: Temporal interval in hours between frames.
        endpoint: HTTP ingestion endpoint (default: from config/env).
        auth_header: Optional authorization header.
        watch_dir: Directory path for atomic file drops.
        output_jsonl_path: Optional destination to write full JSONL replay.
        max_frames: Optional cap on frames produced.

    Returns:
        Summary dict of producer run statistics.
    """
    mode_lower = mode.lower().strip()
    if mode_lower not in ["post", "file", "both", "jsonl"]:
        raise ValueError(f"Invalid mode '{mode}'. Must be one of 'post', 'file', 'both', 'jsonl'.")

    target_endpoint = get_producer_endpoint(endpoint)
    target_watch_dir = get_watch_directory(watch_dir)

    logger.info(
        f"[PRODUCER] Starting producer run for storm='{storm_id}' | mode='{mode}' | speed={speed} | jump='{jump}'"
    )

    frames_produced: list[dict[str, Any]] = []
    posted_count = 0
    dropped_count = 0

    frame_generator = replay(
        storm_id=storm_id,
        jump=jump,
        speed=speed,
        step_hours=step_hours,
    )

    for idx, frame in enumerate(frame_generator):
        if max_frames is not None and idx >= max_frames:
            break

        # Contract verification
        CycloneIntelligence.model_validate(frame)
        frames_produced.append(frame)

        # 1. HTTP POST mode
        if mode_lower in ["post", "both"]:
            success = post_frame(frame, endpoint=target_endpoint, auth_header=auth_header)
            if success:
                posted_count += 1

        # 2. File-drop mode
        if mode_lower in ["file", "both"]:
            file_drop(frame, watch_dir=target_watch_dir)
            dropped_count += 1

    # 3. JSONL sequence export
    if output_jsonl_path is not None or mode_lower == "jsonl":
        jsonl_dest = (
            output_jsonl_path or target_watch_dir / f"{normalize_storm_key(storm_id)}.jsonl"
        )
        write_jsonl(frames_produced, jsonl_dest)

    summary = {
        "status": "completed",
        "storm_id": storm_id,
        "mode": mode_lower,
        "frames_produced": len(frames_produced),
        "frames_posted": posted_count,
        "files_dropped": dropped_count,
        "endpoint": target_endpoint if mode_lower in ["post", "both"] else None,
        "watch_dir": str(target_watch_dir) if mode_lower in ["file", "both"] else None,
    }
    logger.info(f"[PRODUCER] Completed run: {summary}")
    return summary


# -----------------------------------------------------------------------------
# 4. Command-Line Interface (CLI)
# -----------------------------------------------------------------------------


def main() -> None:
    """CLI runner driving the producer pipeline."""
    parser = argparse.ArgumentParser(
        description="Chakravyuh Cyclone Intelligence Producer (Push / File-Drop / JSONL)."
    )
    parser.add_argument(
        "--storm",
        "--storm-id",
        "-s",
        type=str,
        default="Amphan",
        help="Storm identifier or demo storm name (default: Amphan).",
    )
    parser.add_argument(
        "--mode",
        "-m",
        type=str,
        default="both",
        choices=["post", "file", "both", "jsonl"],
        help="Producer transmission mode: post, file, both, or jsonl (default: both).",
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=1.0,
        help="Playback speed multiplier (default: 1.0; 0 for instant push).",
    )
    parser.add_argument(
        "--jump",
        "-j",
        type=str,
        default=None,
        help="Preset jump target (e.g. 'landfall-24h', 'genesis', 'rapid_intensification').",
    )
    parser.add_argument(
        "--endpoint",
        type=str,
        default=None,
        help="Destination backend HTTP endpoint (default from config/env).",
    )
    parser.add_argument(
        "--watch-dir",
        type=str,
        default=None,
        help="Destination directory for file drops (default: ml/cyclone/data/replay_feed).",
    )
    parser.add_argument(
        "--to-file",
        type=str,
        default=None,
        help="Destination JSONL path.",
    )

    args = parser.parse_args()

    summary = run_producer(
        storm_id=args.storm,
        mode=args.mode,
        speed=args.speed,
        jump=args.jump,
        endpoint=args.endpoint,
        watch_dir=args.watch_dir,
        output_jsonl_path=args.to_file,
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
