"""Unit tests for leak-free storm splitting, temporal isolation, and PyTorch dataset batching."""

import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
import torch
from torch.utils.data import DataLoader

from ml.cyclone.datasets.splits import make_splits
from ml.cyclone.datasets.torch_dataset import CycloneDataset, cyclone_collate_fn
from ml.cyclone.features.fusion import FusedSample, make_fused_sample


# -----------------------------------------------------------------------------
# Data Splitting & Leak-Free Guarantee Tests
# -----------------------------------------------------------------------------


def test_make_splits_zero_leakage_and_chronology(tmp_path):
    """Asserts zero storm overlap across splits, temporal ordering, and demo storm isolation."""
    # Synthetic multi-storm trajectory data spanning 2018 to 2022
    records = []
    storms_info = [
        ("STORM_2018_A", "2018-05-10T00:00:00Z", 4),
        ("STORM_2018_B", "2018-11-15T00:00:00Z", 5),
        ("STORM_2019_C", "2019-06-01T00:00:00Z", 6),
        ("STORM_2020_DEMO", "2020-05-18T00:00:00Z", 8), # Demo storm
        ("STORM_2021_E", "2021-05-25T00:00:00Z", 4),
        ("STORM_2022_F", "2022-10-10T00:00:00Z", 5),
    ]

    for sid, start_t, n_steps in storms_info:
        base_time = pd.Timestamp(start_t)
        for i in range(n_steps):
            records.append({
                "storm_id": sid,
                "time": (base_time + pd.Timedelta(hours=i * 6)).isoformat(),
                "lat": 12.0 + i * 0.5,
                "lon": 85.0 + i * 0.3,
                "wind_kt": 35.0 + i * 5.0,
                "pres_mb": 995.0 - i * 4.0,
            })

    manifest_file = tmp_path / "test_manifest.json"
    splits = make_splits(
        samples=records,
        train_ratio=0.60,
        val_ratio=0.20,
        test_ratio=0.20,
        demo_storm_ids=["STORM_2020_DEMO"],
        output_manifest_path=manifest_file,
    )

    # 1. Total samples conserved
    total_split_indices = sum(len(indices) for indices in splits.values())
    assert total_split_indices == len(records)

    # 2. Extract storm IDs per split
    split_storms = {
        name: set(records[idx]["storm_id"] for idx in indices)
        for name, indices in splits.items()
    }

    # Invariant 1: Zero storm overlap between any two splits
    train_storms = split_storms["train"]
    val_storms = split_storms["val"]
    test_storms = split_storms["test"]
    demo_storms = split_storms["demo"]

    assert len(train_storms.intersection(val_storms)) == 0
    assert len(train_storms.intersection(test_storms)) == 0
    assert len(train_storms.intersection(demo_storms)) == 0
    assert len(val_storms.intersection(test_storms)) == 0
    assert len(val_storms.intersection(demo_storms)) == 0
    assert len(test_storms.intersection(demo_storms)) == 0

    # Invariant 2: Demo storm strictly in demo split
    assert demo_storms == {"STORM_2020_DEMO"}

    # Invariant 3: Chronological ordering (Train strictly earlier than Test)
    max_train_time = max(pd.Timestamp(records[i]["time"]) for i in splits["train"])
    min_test_time = min(pd.Timestamp(records[i]["time"]) for i in splits["test"])
    assert max_train_time < min_test_time

    # Invariant 4: Written manifest is valid JSON
    assert manifest_file.is_file()
    with open(manifest_file, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)
    assert "splits" in manifest_data
    assert "storm_counts" in manifest_data


# -----------------------------------------------------------------------------
# PyTorch CycloneDataset & Collate Function Tests
# -----------------------------------------------------------------------------


def test_pytorch_dataset_and_collate_fn():
    """Asserts CycloneDataset yields tensors and collates properly in a DataLoader."""
    # Build a small list of FusedSample objects
    fused_samples = []
    for i in range(4):
        sample_dict = {
            "storm_id": f"STORM_{i // 2}",
            "time": f"2020-05-{16 + i}T12:00:00Z",
            "lat": 15.0 + i,
            "lon": 85.0 + i,
            "wind_kt": 45.0 + i * 10.0,
            "pres_mb": 990.0 - i * 8.0,
            "storm_speed_kt": 10.0,
            "heading_deg": 315.0,
            "history": [
                {"t_offset_h": 0.0, "lat": 15.0 + i, "lon": 85.0 + i, "wind_kt": 45.0 + i * 10.0, "pres_mb": 990.0, "speed_kt": 10.0, "heading_deg": 315.0}
            ],
            "env": {
                "sst_c": 29.0,
                "shear_ms": 11.5,
                "rh500": 70.0,
                "vort850": 18.0,
                "mslp_mb": 1005.0,
                "wind10m_ms": 7.5,
            },
        }
        future_lookup = {6: (15.5 + i, 85.3 + i), 12: (16.0 + i, 85.6 + i)}
        fused = make_fused_sample(sample_dict, storm_future_lookup=future_lookup)
        fused_samples.append(fused)

    # 1. Multimodal dataset & DataLoader
    dataset = CycloneDataset(fused_samples, mode="multimodal")
    assert len(dataset) == 4

    loader = DataLoader(dataset, batch_size=2, shuffle=False, collate_fn=cyclone_collate_fn)
    batch = next(iter(loader))

    assert "image" in batch
    assert batch["image"].shape == (2, 1, 224, 224)
    assert batch["image"].dtype == torch.float32

    assert "env_vector" in batch
    assert batch["env_vector"].shape == (2, 6)

    assert "motion_vector" in batch
    assert batch["motion_vector"].shape == (2, 16)

    assert "track_sequence" in batch
    assert batch["track_sequence"].shape == (2, 8, 7)

    # Check targets sub-dictionary
    targets = batch["targets"]
    assert targets["wind_kt"].shape == (2,)
    assert targets["imd_level_idx"].shape == (2,)
    assert targets["future_deltas"].shape == (2, 5, 2)
    assert targets["horizon_masks"].shape == (2, 5)

    # 2. Image-only pretraining mode
    img_dataset = CycloneDataset(fused_samples, mode="image_only")
    img_loader = DataLoader(img_dataset, batch_size=2, shuffle=False, collate_fn=cyclone_collate_fn)
    img_batch = next(iter(img_loader))

    assert "image" in img_batch
    assert "wind_kt" in img_batch
    assert "imd_level_idx" in img_batch
    assert "env_vector" not in img_batch  # Excluded in image_only mode
