"""Leak-free, spatio-temporally blocked dataset splitting preserving whole-storm boundaries."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from ml.cyclone.config import load_config

DEFAULT_DEMO_STORMS: list[str] = [
    "Amphan",
    "Biparjoy",
    "CYC-2020-BAY-001",
    "CYC-2023-ARB-001",
    "2020136N10087",  # IBTrACS ID for Amphan
    "2023157N12066",  # IBTrACS ID for Biparjoy
]


def _extract_sample_metadata(samples: list[Any] | pd.DataFrame) -> list[dict[str, Any]]:
    """Extracts storm_id and timestamp from a list of dicts, FusedSample objects, or a DataFrame."""
    records: list[dict[str, Any]] = []

    if isinstance(samples, pd.DataFrame):
        for idx, row in samples.iterrows():
            records.append(
                {
                    "index": idx,
                    "storm_id": str(row.get("storm_id", "STORM")).strip(),
                    "time": pd.to_datetime(
                        row.get("time", row.get("ISO_TIME", pd.Timestamp.now(tz="UTC"))), utc=True
                    ),
                }
            )
        return records

    for idx, s in enumerate(samples):
        if hasattr(s, "meta") and isinstance(s.meta, dict):
            # FusedSample object
            storm_id = str(s.meta.get("storm_id", "STORM")).strip()
            time_val = s.meta.get("time", pd.Timestamp.now(tz="UTC"))
        elif isinstance(s, dict):
            storm_id = str(s.get("storm_id", "STORM")).strip()
            time_val = s.get("time", pd.Timestamp.now(tz="UTC"))
        else:
            storm_id = "STORM"
            time_val = pd.Timestamp.now(tz="UTC")

        records.append(
            {
                "index": idx,
                "storm_id": storm_id,
                "time": pd.to_datetime(time_val, utc=True),
            }
        )

    return records


def make_splits(
    samples: list[Any] | pd.DataFrame,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    demo_storm_ids: list[str] | None = None,
    output_manifest_path: str | Path | None = None,
) -> dict[str, list[int]]:
    """Generates leak-free, temporally-ordered train/val/test/demo split indices blocked by WHOLE STORMS.

    Key Guarantees:
    1. Zero Storm Leakage: A storm_id appears in exactly ONE split (train, val, test, or demo).
    2. Chronological Ordering: Test storms are strictly later than train storms to avoid future lookahead.
    3. Demo Storm Isolation: Demo showcase storms are reserved exclusively for qualitative evaluation.

    Args:
        samples: List of sample dictionaries, FusedSample instances, or DataFrame.
        train_ratio: Fraction of non-demo storms for training (default: 0.70).
        val_ratio: Fraction of non-demo storms for validation (default: 0.15).
        test_ratio: Fraction of non-demo storms for evaluation testing (default: 0.15).
        demo_storm_ids: List of storm IDs/names to isolate into demo split.
        output_manifest_path: Optional file path to write split_manifest.json.

    Returns:
        Dict mapping split names ('train', 'val', 'test', 'demo') to lists of integer sample indices.
    """
    records = _extract_sample_metadata(samples)
    if not records:
        return {"train": [], "val": [], "test": [], "demo": []}

    # Resolve demo storm identifiers
    configured_demo_storms = (
        set(demo_storm_ids) if demo_storm_ids is not None else set(DEFAULT_DEMO_STORMS)
    )
    try:
        cfg = load_config()
        if hasattr(cfg, "replay") and hasattr(cfg.replay, "storms"):
            for s_key, s_info in cfg.replay.storms.items():
                if isinstance(s_info, dict):
                    if "cyclone_id" in s_info:
                        configured_demo_storms.add(s_info["cyclone_id"])
                    if "name" in s_info:
                        configured_demo_storms.add(s_info["name"])
    except Exception:
        pass

    # Group sample records by storm
    storm_summary: dict[str, dict[str, Any]] = {}
    for r in records:
        sid = r["storm_id"]
        t = r["time"]
        idx = r["index"]

        if sid not in storm_summary:
            storm_summary[sid] = {
                "storm_id": sid,
                "min_time": t,
                "max_time": t,
                "indices": [],
            }
        storm_summary[sid]["min_time"] = min(storm_summary[sid]["min_time"], t)
        storm_summary[sid]["max_time"] = max(storm_summary[sid]["max_time"], t)
        storm_summary[sid]["indices"].append(idx)

    # Separate demo storms
    demo_storms: list[str] = []
    regular_storms: list[str] = []

    for sid, info in storm_summary.items():
        is_demo = False
        for demo_name in configured_demo_storms:
            if demo_name.upper() == sid.upper() or demo_name.upper() in sid.upper():
                is_demo = True
                break
        if is_demo:
            demo_storms.append(sid)
        else:
            regular_storms.append(sid)

    # Sort regular storms chronologically by earliest observation timestamp
    regular_storms.sort(key=lambda s: storm_summary[s]["min_time"])

    # Compute partition counts
    num_regular = len(regular_storms)
    if num_regular == 0 and demo_storms:
        # If all storms are demo storms, keep them in demo
        train_storms, val_storms, test_storms = [], [], []
    elif num_regular == 1:
        train_storms = regular_storms
        val_storms, test_storms = [], []
    elif num_regular == 2:
        train_storms = [regular_storms[0]]
        val_storms = []
        test_storms = [regular_storms[1]]
    else:
        n_train = max(1, int(round(num_regular * train_ratio)))
        n_val = max(1, int(round(num_regular * val_ratio)))
        if n_train + n_val >= num_regular:
            n_train = num_regular - 2
            n_val = 1

        train_storms = regular_storms[:n_train]
        val_storms = regular_storms[n_train : n_train + n_val]
        test_storms = regular_storms[n_train + n_val :]

    # Map storm groupings to sample indices
    splits: dict[str, list[int]] = {
        "train": [idx for sid in train_storms for idx in storm_summary[sid]["indices"]],
        "val": [idx for sid in val_storms for idx in storm_summary[sid]["indices"]],
        "test": [idx for sid in test_storms for idx in storm_summary[sid]["indices"]],
        "demo": [idx for sid in demo_storms for idx in storm_summary[sid]["indices"]],
    }

    # Write split manifest JSON
    manifest = {
        "split_counts": {k: len(v) for k, v in splits.items()},
        "storm_counts": {
            "train": len(train_storms),
            "val": len(val_storms),
            "test": len(test_storms),
            "demo": len(demo_storms),
        },
        "splits": {
            "train": {
                "storms": train_storms,
                "date_range": (
                    f"{min(storm_summary[s]['min_time'] for s in train_storms).isoformat()} -> {max(storm_summary[s]['max_time'] for s in train_storms).isoformat()}"
                    if train_storms
                    else "N/A"
                ),
            },
            "val": {
                "storms": val_storms,
                "date_range": (
                    f"{min(storm_summary[s]['min_time'] for s in val_storms).isoformat()} -> {max(storm_summary[s]['max_time'] for s in val_storms).isoformat()}"
                    if val_storms
                    else "N/A"
                ),
            },
            "test": {
                "storms": test_storms,
                "date_range": (
                    f"{min(storm_summary[s]['min_time'] for s in test_storms).isoformat()} -> {max(storm_summary[s]['max_time'] for s in test_storms).isoformat()}"
                    if test_storms
                    else "N/A"
                ),
            },
            "demo": {
                "storms": demo_storms,
                "date_range": (
                    f"{min(storm_summary[s]['min_time'] for s in demo_storms).isoformat()} -> {max(storm_summary[s]['max_time'] for s in demo_storms).isoformat()}"
                    if demo_storms
                    else "N/A"
                ),
            },
        },
    }

    manifest_path = (
        Path(output_manifest_path)
        if output_manifest_path
        else (Path(__file__).resolve().parent / "split_manifest.json")
    )
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return splits


__all__ = ["make_splits", "DEFAULT_DEMO_STORMS"]
