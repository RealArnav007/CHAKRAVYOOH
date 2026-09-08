"""Pretraining pipeline for satellite IR cyclone detection CNN with imbalance handling."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from ml.cyclone.datasets.splits import make_splits
from ml.cyclone.datasets.torch_dataset import CycloneDataset, cyclone_collate_fn, generate_negative_samples
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
    artifact_dir: Optional[Path] = None,
    device: Optional[torch.device] = None,
) -> Dict[str, Any]:
    """Trains DetectionModel on satellite IR patches with class-weighted BCE loss.

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
        torch.device("mps") if torch.backends.mps.is_available()
        else torch.device("cuda") if torch.cuda.is_available()
        else torch.device("cpu")
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

    print(f"[TRAIN] Split counts -> Train: {len(train_indices)}, Val: {len(val_indices)}, Test: {len(test_indices)}")

    train_ds = CycloneDataset(all_samples, indices=train_indices, mode="image_only")
    val_ds = CycloneDataset(all_samples, indices=val_indices, mode="image_only")
    test_ds = CycloneDataset(all_samples, indices=test_indices, mode="image_only")

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, collate_fn=cyclone_collate_fn)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, collate_fn=cyclone_collate_fn)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False, collate_fn=cyclone_collate_fn)

    # 3. Model & Loss with Imbalance Weighting
    model = DetectionModel(backbone_name=backbone, pretrained=True).to(compute_device)

    # Calculate class imbalance ratio for pos_weight
    train_labels = [all_samples[i].get("wind_kt", 0.0) >= 17.0 for i in train_indices]
    n_pos = max(1, sum(train_labels))
    n_neg = max(1, len(train_labels) - n_pos)
    pos_weight_val = float(n_neg / n_pos)
    pos_weight = torch.tensor([pos_weight_val], dtype=torch.float32, device=compute_device)
    print(f"[TRAIN] Class balance in train: {n_pos} positive, {n_neg} negative (pos_weight = {pos_weight_val:.2f})")

    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=max(1, epochs))

    best_val_f1 = -1.0
    best_checkpoint_path = save_dir / "best_detection_model.pt"
    history: List[Dict[str, Any]] = []

    # 4. Training Loop
    print(f"[TRAIN] Starting training for {epochs} epochs...")
    for epoch in range(1, epochs + 1):
        model.train()
        train_losses = []

        for batch in train_loader:
            images = batch["image"].to(compute_device)
            available = batch["image_available"].to(compute_device)
            targets = batch["detected"].to(compute_device).unsqueeze(1)

            optimizer.zero_grad()
            out = model(images, image_available=available)
            loss = criterion(out["logits"], targets)
            loss.backward()
            optimizer.step()

            train_losses.append(loss.item())

        scheduler.step()
        mean_train_loss = float(np.mean(train_losses)) if train_losses else 0.0

        # Validation pass
        val_metrics = evaluate_detection(model, val_loader, compute_device)
        print(
            f"Epoch {epoch:02d}/{epochs:02d} | Train Loss: {mean_train_loss:.4f} | "
            f"Val Acc: {val_metrics['accuracy']:.4f} | Val F1: {val_metrics['macro_f1']:.4f} | "
            f"Val PR-AUC: {val_metrics['pr_auc']:.4f} | Val ECE: {val_metrics['ece']:.4f}"
        )

        history.append({
            "epoch": epoch,
            "train_loss": round(mean_train_loss, 4),
            "val_accuracy": val_metrics["accuracy"],
            "val_macro_f1": val_metrics["macro_f1"],
            "val_pr_auc": val_metrics["pr_auc"],
            "val_ece": val_metrics["ece"],
        })

        if val_metrics["macro_f1"] >= best_val_f1:
            best_val_f1 = val_metrics["macro_f1"]
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "backbone": backbone,
                "pos_weight": pos_weight_val,
                "val_metrics": val_metrics,
            }, best_checkpoint_path)

    # 5. Final Evaluation on Test Split
    print("[TRAIN] Evaluating best checkpoint on held-out test split...")
    best_ckpt = torch.load(best_checkpoint_path, map_location=compute_device)
    model.load_state_dict(best_ckpt["model_state_dict"])
    test_metrics = evaluate_detection(model, test_loader, compute_device)

    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "backbone": backbone,
        "epochs": epochs,
        "best_epoch": best_ckpt["epoch"],
        "val_metrics": best_ckpt["val_metrics"],
        "test_metrics": test_metrics,
        "history": history,
    }

    # Save metrics JSON
    metrics_path = save_dir / "detection_metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"[TRAIN] Checkpoint saved: {best_checkpoint_path}")
    print(f"[TRAIN] Test Results -> Acc: {test_metrics['accuracy']:.4f}, Macro-F1: {test_metrics['macro_f1']:.4f}, PR-AUC: {test_metrics['pr_auc']:.4f}, ECE: {test_metrics['ece']:.4f}")

    return results


def evaluate_detection(
    model: nn.Module,
    dataloader: DataLoader,
    device: torch.device,
) -> Dict[str, Any]:
    """Evaluates detection model emitting Accuracy, Macro-F1, PR-AUC, and ECE."""
    model.eval()
    y_true_list: List[int] = []
    y_pred_list: List[int] = []
    y_prob_list: List[float] = []

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
    results: Dict[str, Any],
    report_path: Optional[Path] = None,
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
