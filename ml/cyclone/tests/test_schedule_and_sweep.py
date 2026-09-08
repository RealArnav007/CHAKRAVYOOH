"""Unit tests for LR scheduling, layer-wise LR decay (LLRD), and HPO sweep runner."""

from __future__ import annotations

from pathlib import Path

import pytest
import torch
import torch.nn as nn
import yaml

from ml.cyclone.models.fusion_net import FusionNet
from ml.cyclone.train.losses import MultiTaskLoss
from ml.cyclone.train.schedule import (
    CosineWarmupScheduler,
    build_optimizer_with_llrd,
    get_cosine_schedule_with_warmup,
)
from ml.cyclone.train.sweep import (
    compute_composite_val_score,
    lock_in_best_config,
)


def test_cosine_warmup_scheduler_mechanics() -> None:
    """Tests that CosineWarmupScheduler ramps up linearly and decays along cosine curve."""
    model = nn.Linear(10, 2)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
    scheduler = CosineWarmupScheduler(
        optimizer=optimizer,
        warmup_steps=5,
        total_steps=20,
        min_lr=1e-5,
    )

    # Step 0: start at min_lr
    initial_lr = scheduler.get_lr()[0]
    assert initial_lr == pytest.approx(1e-5, abs=1e-6)

    # Step 5: peak at base_lr (1e-3)
    for _ in range(5):
        optimizer.step()
        scheduler.step()

    peak_lr = scheduler.get_lr()[0]
    assert peak_lr == pytest.approx(1e-3, rel=1e-2)

    # Step 20: decay down to min_lr
    for _ in range(15):
        optimizer.step()
        scheduler.step()

    final_lr = scheduler.get_lr()[0]
    assert final_lr == pytest.approx(1e-5, abs=1e-5)


def test_lambda_cosine_warmup_scheduler() -> None:
    """Tests get_cosine_schedule_with_warmup helper."""
    model = nn.Linear(10, 2)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    scheduler = get_cosine_schedule_with_warmup(
        optimizer=optimizer,
        num_warmup_steps=4,
        num_training_steps=16,
        min_lr_ratio=0.05,
    )

    lrs = []
    for _ in range(16):
        optimizer.step()
        lrs.append(scheduler.get_last_lr()[0])
        scheduler.step()

    # Monotonically increasing during warmup
    assert lrs[3] > lrs[0]
    # Decaying towards end
    assert lrs[-1] < lrs[4]


def test_layerwise_decay_param_groups() -> None:
    """Tests Layer-wise Learning Rate Decay (LLRD) layer assignments and regularization."""
    model = FusionNet(
        image_backbone="efficientnet_b0",
        image_pretrained=False,
        image_dim=64,
        env_in_dim=6,
        env_dim=32,
        track_in_dim=7,
        track_hidden_dim=32,
        fusion_hidden_dim=64,
        shared_dim=32,
    )
    criterion = MultiTaskLoss()

    base_lr = 2e-4
    backbone_lr_ratio = 0.1
    layer_decay = 0.75

    optimizer = build_optimizer_with_llrd(
        model=model,
        lr=base_lr,
        weight_decay=1e-4,
        backbone_lr_ratio=backbone_lr_ratio,
        layer_decay=layer_decay,
        extra_parameters=list(criterion.parameters()),
    )

    # Check parameter groups
    lrs = [g["lr"] for g in optimizer.param_groups]
    wds = [g["weight_decay"] for g in optimizer.param_groups]

    # Task heads / trunk should have base_lr (2e-4)
    assert any(pytest.approx(lr) == base_lr for lr in lrs)

    # Early backbone layers should have decayed learning rates (< base_lr * backbone_lr_ratio)
    backbone_lrs = [g["lr"] for g in optimizer.param_groups if "backbone" in g.get("name", "")]
    if backbone_lrs:
        assert min(backbone_lrs) < base_lr * backbone_lr_ratio
        assert max(backbone_lrs) <= base_lr * backbone_lr_ratio

    # Biases and 1D norms should have weight_decay=0.0
    assert 0.0 in wds
    # Weights should have weight_decay=1e-4
    assert 1e-4 in wds


def test_composite_score_computation() -> None:
    """Tests multi-task composite validation scoring."""
    good_metrics = {
        "track_mean_error_km": 150.0,
        "intensity_wind_rmse_kt": 8.0,
        "stage_macro_f1": 0.85,
        "val_loss": 10.0,
    }
    poor_metrics = {
        "track_mean_error_km": 450.0,
        "intensity_wind_rmse_kt": 25.0,
        "stage_macro_f1": 0.20,
        "val_loss": 40.0,
    }

    good_score = compute_composite_val_score(good_metrics)
    poor_score = compute_composite_val_score(poor_metrics)

    # Lower score represents superior model performance
    assert good_score < poor_score


def test_lock_in_best_config(tmp_path: Path) -> None:
    """Tests saving the winning configuration into model.best.yaml."""
    best_params = {
        "learning_rate": 3e-4,
        "weight_decay": 2e-4,
        "dropout": 0.25,
        "backbone": "efficientnet_b0",
        "track_hidden_dim": 128,
        "fusion_hidden_dim": 512,
        "task_loss_init": {"track": -0.1, "intensity_reg": -0.1},
    }
    out_file = tmp_path / "model.best.yaml"
    lock_in_best_config(best_params, output_path=out_file)

    assert out_file.is_file()
    with open(out_file, encoding="utf-8") as f:
        loaded = yaml.safe_load(f)

    assert loaded["tier1"]["image_branch"]["backbone"] == "efficientnet_b0"
    assert loaded["tier1"]["image_branch"]["dropout"] == 0.25
    assert loaded["optimization"]["learning_rate"] == 3e-4
    assert loaded["optimization"]["weight_decay"] == 2e-4
    assert loaded["tier1"]["track_branch"]["hidden_dim"] == 128
