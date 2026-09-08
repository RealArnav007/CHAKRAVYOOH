"""Pretraining pipeline for satellite IR cyclone detection CNN with imbalance handling."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from ml.cyclone.datasets.splits import make_splits
from ml.cyclone.datasets.torch_dataset import (
    CycloneDataset,
    cyclone_collate_fn,
    generate_negative_samples,
)
from ml.cyclone.eval.metrics import (
    classification_metrics,
    expected_calibration_error,
)
from ml.cyclone.ingest.ibtracs import load_tracks
from ml.cyclone.models.heads import DetectionModel
from ml.cyclone.preprocess.align import resample_track
from ml.cyclone.preprocess.clean import clean_tracks
from ml.cyclone.preprocess.colocalize import build_samples


def train_detection(
    epochs: int = 10,
    batch_size: int = 8,
    lr: float = 1e-4,
    weight_decay: float = 1e-4,
    backbone: str = "efficientnet_b0",
    artifact_dir: Path | None = None,
    device: torch.device | None = None,
) -> dict[str, Any]:
    """Trains DetectionModel on satellite IR patches with class-weighted BCE loss using unified Trainer.

    Args:
        epochs: Number of training epochs.
        batch_size: Mini-batch size.
        lr: Initial learning rate.
        weight_decay: AdamW weight decay.
        backbone: timm backbone identifier (default: 'efficientnet_b0').
        artifact_dir: Destination directory for model weights and metrics JSON.
        device: Torch compute device (CPU/MPS/CUDA).

    Returns:
        Dictionary of final validation and test metrics.
    """
    save_dir = artifact_dir or (Path(__file__).resolve().parent.parent / "artifacts" / "detection")
    save_dir.mkdir(parents=True, exist_ok=True)

    compute_device = device or (
        torch.device("mps")
        if torch.backends.mps.is_available()
        else torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
    )
    print(f"[TRAIN] Using compute device: {compute_device}")

    # 1. Prepare positive and negative training samples
    print("[TRAIN] Preparing training samples...")
    raw_tracks = load_tracks()
    clean_df, _ = clean_tracks(raw_tracks)
    resampled_df = resample_track(clean_df, step_hours=6)
    pos_samples = build_samples(resampled_df, history_steps=8)

    # Generate negative open-ocean non-cyclone background patches
    neg_samples = generate_negative_samples(num_samples=max(20, len(pos_samples) // 2), seed=42)
    all_samples = pos_samples + neg_samples

    # 2. Spatio-temporal split
    splits = make_splits(all_samples, train_ratio=0.70, val_ratio=0.15, test_ratio=0.15)
    train_indices = splits["train"]
    val_indices = splits["val"]
    test_indices = splits["test"]

    print(
        f"[TRAIN] Split counts -> Train: {len(train_indices)}, Val: {len(val_indices)}, Test: {len(test_indices)}"
    )

    train_ds = CycloneDataset(all_samples, indices=train_indices, mode="image_only")
    val_ds = CycloneDataset(all_samples, indices=val_indices, mode="image_only")
    test_ds = CycloneDataset(all_samples, indices=test_indices, mode="image_only")

    train_loader = DataLoader(
        train_ds, batch_size=batch_size, shuffle=True, collate_fn=cyclone_collate_fn
    )
    val_loader = DataLoader(
        val_ds, batch_size=batch_size, shuffle=False, collate_fn=cyclone_collate_fn
    )
    test_loader = DataLoader(
        test_ds, batch_size=batch_size, shuffle=False, collate_fn=cyclone_collate_fn
    )

    # 3. Model & Loss with Imbalance Weighting
    model = DetectionModel(backbone_name=backbone, pretrained=True)

    train_labels = [all_samples[i].get("wind_kt", 0.0) >= 17.0 for i in train_indices]
    n_pos = max(1, sum(train_labels))
    n_neg = max(1, len(train_labels) - n_pos)
    pos_weight_val = float(n_neg / n_pos)
    pos_weight = torch.tensor([pos_weight_val], dtype=torch.float32, device=compute_device)
    print(
        f"[TRAIN] Class balance in train: {n_pos} positive, {n_neg} negative (pos_weight = {pos_weight_val:.2f})"
    )

    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=max(1, epochs))

    def step_fn(
        m: nn.Module, batch: dict[str, Any], crit: Any, dev: torch.device
    ) -> Tuple[torch.Tensor, dict[str, Any]]:
        imgs = batch["image"].to(dev)
        avail = batch["image_available"].to(dev)
        targets = batch["detected"].to(dev).unsqueeze(1)
        out = m(imgs, image_available=avail)
        loss = crit(out["logits"], targets)
        return loss, {"loss": loss.item()}

    # 4. Setup Experiment Tracker & Trainer
    tracker = ExperimentTracker(
        experiment_name="detection_pretrain",
        run_dir=save_dir,
        config={"backbone": backbone, "lr": lr, "batch_size": batch_size, "epochs": epochs},
        split_indices=splits,
    )

    trainer = Trainer(
        model=model,
        criterion=criterion,
        train_loader=train_loader,
        val_loader=val_loader,
        test_loader=test_loader,
        optimizer=optimizer,
        scheduler=scheduler,
        device=compute_device,
        save_dir=save_dir,
        tracker=tracker,
        step_fn=step_fn,
        eval_fn=evaluate_detection,
        early_stopping_metric="macro_f1",
        early_stopping_mode="max",
        early_stopping_patience=10,
        checkpoint_prefix="best_detection_model",
    )

    trainer_summary = trainer.train(epochs=epochs)

    # 5. Package results
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "backbone": backbone,
        "epochs": epochs,
        "best_epoch": trainer_summary["best_epoch"],
        "val_metrics": trainer.validate(),
        "test_metrics": trainer_summary["test_metrics"],
        "history": trainer.history,
    }

    metrics_path = save_dir / "detection_metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    return results


def evaluate_detection(
    model: nn.Module,
    dataloader: DataLoader,
    device: torch.device,
) -> dict[str, Any]:
    """Evaluates detection model emitting Accuracy, Macro-F1, PR-AUC, and ECE."""
    model.eval()
    y_true_list: list[int] = []
    y_pred_list: list[int] = []
    y_prob_list: list[float] = []

    with torch.no_grad():
        for batch in dataloader:
            images = batch["image"].to(device)
            available = batch["image_available"].to(device)
            targets = batch["detected"].cpu().numpy()

            out = model(images, image_available=available)
            probs = out["probs"].squeeze().cpu().numpy()
            probs = np.atleast_1d(probs)

            for t_val, p_val in zip(targets, probs):
                y_true_list.append(int(t_val >= 0.5))
                y_prob_list.append(float(p_val))
                y_pred_list.append(int(p_val >= 0.5))

    metrics = classification_metrics(
        y_true=y_true_list,
        y_pred=y_pred_list,
        y_prob=y_prob_list,
        classes=[0, 1],
    )
    ece_val = expected_calibration_error(y_true=y_true_list, y_prob=y_prob_list)

    return {
        "accuracy": metrics["accuracy"],
        "macro_f1": metrics["macro_f1"],
        "pr_auc": metrics["pr_auc"] if metrics["pr_auc"] is not None else 0.0,
        "ece": ece_val,
        "confusion_matrix": metrics["confusion_matrix"],
    }


def append_to_models_report(
    results: dict[str, Any],
    report_path: Path | None = None,
) -> None:
    """Appends model benchmark performance to models_report.md."""
    rep_path = report_path or (Path("ml/cyclone/eval/models_report.md"))
    rep_path.parent.mkdir(parents=True, exist_ok=True)

    t_met = results["test_metrics"]
    v_met = results["val_metrics"]

    content = f"""# Chakravyuh Neural Model Benchmark Report

**Updated:** {results['timestamp']}  
**Latest Evaluated Model:** Tier-1 Satellite IR Detection CNN (`DetectionModel` with `{results['backbone']}`)  
**Task:** Binary Cyclone Detection (Active Convective System vs Background Ocean)

---

## 1. Detection Model Performance Summary

| Split | Accuracy | Macro F1 | PR-AUC | ECE (Calibration) |
| :--- | :--- | :--- | :--- | :--- |
| **Validation** | **{v_met['accuracy']:.4f}** | **{v_met['macro_f1']:.4f}** | **{v_met['pr_auc']:.4f}** | **{v_met['ece']:.4f}** |
| **Test (Held-Out)** | **{t_met['accuracy']:.4f}** | **{t_met['macro_f1']:.4f}** | **{t_met['pr_auc']:.4f}** | **{t_met['ece']:.4f}** |

### Confusion Matrix (Test Split)
```
{t_met['confusion_matrix']}
```
*(Rows: Ground Truth [0: Non-Cyclone, 1: Cyclone], Columns: Predicted [0: Non-Cyclone, 1: Cyclone])*

---

## 2. Model Architecture & Training Details

- **Vision Backbone:** `{results['backbone']}` with ImageNet initialization and single-channel IR channel aggregation.
- **Feature Embedding:** Global Average Pooling + LayerNorm projection $\\to$ 512-d latent representation.
- **Classification Head:** 2-layer MLP ($512 \\to 128 \\to 1$) with GELU and dropout ($p=0.2$).
- **Imbalance Handling:** Pos-weight scaled `BCEWithLogitsLoss` accounting for open ocean background preponderance.
- **Optimization:** AdamW with Cosine Annealing learning rate schedule.
- **Best Model Checkpoint:** `ml/cyclone/artifacts/detection/best_detection_model.pt`

---
"""
    with open(rep_path, "w", encoding="utf-8") as f:
        f.write(content)

    # Also mirror to eval/models_report.md
    mirror_path = Path("eval/models_report.md")
    mirror_path.parent.mkdir(parents=True, exist_ok=True)
    with open(mirror_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[REPORT] Models report updated at {rep_path} and {mirror_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Train satellite IR cyclone detection CNN.")
    parser.add_argument("--epochs", type=int, default=5, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=8, help="Batch size")
    parser.add_argument("--lr", type=float, default=1e-4, help="Learning rate")
    parser.add_argument("--backbone", type=str, default="efficientnet_b0", help="Backbone name")
    args = parser.parse_args()

    results = train_detection(
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        backbone=args.backbone,
    )
    append_to_models_report(results)


if __name__ == "__main__":
    main()
