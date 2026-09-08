"""Hyperparameter sweep runner for Multi-Modal FusionNet with composite metric ranking."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import itertools
import json
from pathlib import Path
import random
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import torch
import yaml

from ml.cyclone.datasets.splits import make_splits
from ml.cyclone.datasets.torch_dataset import CycloneDataset, cyclone_collate_fn
from ml.cyclone.ingest.ibtracs import load_tracks
from ml.cyclone.models.fusion_net import FusionNet
from ml.cyclone.models.heads import DEFAULT_TRACK_HORIZONS
from ml.cyclone.preprocess.align import resample_track
from ml.cyclone.preprocess.clean import clean_tracks
from ml.cyclone.preprocess.colocalize import build_samples
from ml.cyclone.train.losses import MultiTaskLoss
from ml.cyclone.train.schedule import CosineWarmupScheduler, build_optimizer_with_llrd
from ml.cyclone.train.track_experiment import ExperimentTracker
from ml.cyclone.train.train_fusion import evaluate_fusion_net
from ml.cyclone.train.trainer import Trainer


@dataclass
class SweepConfigSpace:
    """Configurable parameter search space for FusionNet optimization."""

    learning_rates: List[float] = field(default_factory=lambda: [1e-4, 2e-4, 3e-4])
    weight_decays: List[float] = field(default_factory=lambda: [1e-4, 5e-4])
    dropouts: List[float] = field(default_factory=lambda: [0.1, 0.2, 0.3])
    backbones: List[str] = field(default_factory=lambda: ["efficientnet_b0", "resnet18"])
    track_hidden_dims: List[int] = field(default_factory=lambda: [64, 128])
    fusion_hidden_dims: List[int] = field(default_factory=lambda: [256, 512])
    task_loss_inits: List[Dict[str, float]] = field(default_factory=lambda: [
        {"detection": 0.0, "stage": 0.0, "intensity_reg": 0.0, "intensity_cls": 0.0, "track": 0.0},
        {"detection": 0.0, "stage": 0.0, "intensity_reg": -0.2, "intensity_cls": 0.0, "track": -0.2},
    ])


def compute_composite_val_score(
    val_metrics: Dict[str, Any],
    w_track: float = 0.01,
    w_intensity: float = 0.1,
    w_stage: float = 1.0,
    w_loss: float = 0.05,
) -> float:
    """Computes a multi-task composite validation score.

    Composite Score Formula:
        Score = w_track * track_mean_error_km + w_intensity * intensity_wind_rmse_kt - w_stage * stage_macro_f1 + w_loss * val_loss

    Lower score indicates superior multi-task performance across track, intensity, and lifecycle prediction.
    """
    track_err = float(val_metrics.get("track_mean_error_km", 300.0))
    int_rmse = float(val_metrics.get("intensity_wind_rmse_kt", 15.0))
    stage_f1 = float(val_metrics.get("stage_macro_f1", 0.0))
    val_loss = float(val_metrics.get("val_loss", 50.0))

    score = (w_track * track_err) + (w_intensity * int_rmse) - (w_stage * stage_f1) + (w_loss * val_loss)
    return round(score, 4)


def run_hyperparameter_sweep(
    num_trials: int = 4,
    epochs_per_trial: int = 3,
    batch_size: int = 8,
    search_strategy: str = "random",
    config_space: Optional[SweepConfigSpace] = None,
    output_dir: Optional[Path] = None,
    device: Optional[torch.device] = None,
) -> Dict[str, Any]:
    """Executes a multi-task hyperparameter optimization sweep over FusionNet architecture & regularizers.

    Args:
        num_trials: Number of parameter combinations to evaluate.
        epochs_per_trial: Training duration for each trial run.
        batch_size: Mini-batch size.
        search_strategy: "random" or "grid".
        config_space: SweepConfigSpace definition.
        output_dir: Output directory for trial checkpoints and artifacts.
        device: Torch compute device.

    Returns:
        Dictionary summarizing all trial results, rankings, and the winning configuration.
    """
    save_dir = output_dir or (Path(__file__).resolve().parent.parent / "artifacts" / "sweep")
    save_dir.mkdir(parents=True, exist_ok=True)

    space = config_space or SweepConfigSpace()
    compute_device = device or (
        torch.device("mps") if torch.backends.mps.is_available()
        else torch.device("cuda") if torch.cuda.is_available()
        else torch.device("cpu")
    )
    print(f"[SWEEP] Initializing HPO Sweep ({num_trials} trials, strategy={search_strategy}) on {compute_device}")

    # 1. Load Multi-Modal Dataset
    raw_tracks = load_tracks()
    clean_df, _ = clean_tracks(raw_tracks)
    resampled_df = resample_track(clean_df, step_hours=6)
    all_samples = build_samples(resampled_df, history_steps=8)

    splits = make_splits(all_samples, train_ratio=0.70, val_ratio=0.15, test_ratio=0.15)
    train_ds = CycloneDataset(all_samples, indices=splits["train"], mode="multimodal")
    val_ds = CycloneDataset(all_samples, indices=splits["val"], mode="multimodal")
    test_ds = CycloneDataset(all_samples, indices=splits["test"], mode="multimodal")

    from torch.utils.data import DataLoader
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, collate_fn=cyclone_collate_fn)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, collate_fn=cyclone_collate_fn)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False, collate_fn=cyclone_collate_fn)

    # 2. Generate Candidate Configurations
    all_combinations = list(itertools.product(
        space.learning_rates,
        space.weight_decays,
        space.dropouts,
        space.backbones,
        space.track_hidden_dims,
        space.fusion_hidden_dims,
        space.task_loss_inits,
    ))

    if search_strategy == "random":
        random.seed(42)
        selected_combos = random.sample(all_combinations, min(num_trials, len(all_combinations)))
    else:
        selected_combos = all_combinations[:num_trials]

    trial_results: List[Dict[str, Any]] = []

    for trial_idx, (lr, wd, drop, backbone, track_dim, fusion_dim, loss_init) in enumerate(selected_combos):
        trial_id = f"trial_{trial_idx + 1:02d}"
        trial_dir = save_dir / trial_id
        trial_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n[SWEEP] === Running {trial_id}/{len(selected_combos)}: lr={lr}, wd={wd}, drop={drop}, bb={backbone}, track_dim={track_dim}, fusion_dim={fusion_dim} ===")

        # Build Model with trial hyperparameters
        model = FusionNet(
            image_backbone=backbone,
            image_pretrained=True,
            image_dim=512,
            env_in_dim=6,
            env_dim=64,
            track_in_dim=7,
            track_hidden_dim=track_dim,
            fusion_hidden_dim=fusion_dim,
            shared_dim=256,
            dropout=drop,
            num_stages=6,
            num_imd_levels=7,
            num_track_horizons=len(DEFAULT_TRACK_HORIZONS),
        )

        # Multi-task loss with custom task variance initialization
        criterion = MultiTaskLoss(init_log_vars=loss_init)

        # Optimizer with Layer-wise LR Decay (LLRD)
        optimizer = build_optimizer_with_llrd(
            model=model,
            lr=lr,
            weight_decay=wd,
            backbone_lr_ratio=0.1,
            layer_decay=0.75,
            extra_parameters=list(criterion.parameters()),
        )

        # Cosine warmup scheduler
        scheduler = CosineWarmupScheduler(
            optimizer=optimizer,
            warmup_steps=1,
            total_steps=max(1, epochs_per_trial),
            min_lr=lr * 0.01,
        )

        tracker = ExperimentTracker(
            experiment_name=f"sweep_{trial_id}",
            run_dir=trial_dir,
            config={
                "lr": lr,
                "weight_decay": wd,
                "dropout": drop,
                "backbone": backbone,
                "track_hidden_dim": track_dim,
                "fusion_hidden_dim": fusion_dim,
                "loss_init": loss_init,
            },
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
            save_dir=trial_dir,
            tracker=tracker,
            eval_fn=evaluate_fusion_net,
            early_stopping_metric="track_mean_error_km",
            early_stopping_mode="min",
            early_stopping_patience=5,
            checkpoint_prefix=f"model_{trial_id}",
        )

        summary = trainer.train(epochs=epochs_per_trial)
        val_metrics = trainer.validate()
        test_metrics = summary.get("test_metrics", {})
        composite_score = compute_composite_val_score(val_metrics)

        trial_record = {
            "trial_id": trial_id,
            "params": {
                "learning_rate": lr,
                "weight_decay": wd,
                "dropout": drop,
                "backbone": backbone,
                "track_hidden_dim": track_dim,
                "fusion_hidden_dim": fusion_dim,
                "task_loss_init": loss_init,
            },
            "composite_val_score": composite_score,
            "val_metrics": {
                "track_mean_error_km": val_metrics.get("track_mean_error_km", 0.0),
                "intensity_wind_rmse_kt": val_metrics.get("intensity_wind_rmse_kt", 0.0),
                "stage_macro_f1": val_metrics.get("stage_macro_f1", 0.0),
                "detection_accuracy": val_metrics.get("detection_accuracy", 0.0),
                "cone_coverage_pct": val_metrics.get("cone_coverage_pct", 0.0),
            },
            "test_metrics": {
                "track_mean_error_km": test_metrics.get("track_mean_error_km", 0.0),
                "intensity_wind_rmse_kt": test_metrics.get("intensity_wind_rmse_kt", 0.0),
                "stage_macro_f1": test_metrics.get("stage_macro_f1", 0.0),
                "detection_accuracy": test_metrics.get("detection_accuracy", 0.0),
                "cone_coverage_pct": test_metrics.get("cone_coverage_pct", 0.0),
            },
            "learned_task_weights": criterion.get_task_weights(),
        }
        trial_results.append(trial_record)
        print(f"[SWEEP] {trial_id} Finished -> Composite Val Score: {composite_score:.4f} (Track: {val_metrics.get('track_mean_error_km', 0):.1f}km, Int: {val_metrics.get('intensity_wind_rmse_kt', 0):.2f}kt, Stage F1: {val_metrics.get('stage_macro_f1', 0):.4f})")

    # Rank trials by composite validation score (ascending: lower is better)
    trial_results.sort(key=lambda t: t["composite_val_score"])
    best_trial = trial_results[0]

    sweep_summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_trials": len(trial_results),
        "best_trial_id": best_trial["trial_id"],
        "best_params": best_trial["params"],
        "best_composite_score": best_trial["composite_val_score"],
        "best_trial_val_metrics": best_trial["val_metrics"],
        "best_trial_test_metrics": best_trial["test_metrics"],
        "ranked_trials": trial_results,
    }

    # Save sweep summary JSON
    with open(save_dir / "sweep_results.json", "w", encoding="utf-8") as f:
        json.dump(sweep_summary, f, indent=2)

    # Write winning config to model.best.yaml
    lock_in_best_config(best_trial["params"])

    return sweep_summary


def lock_in_best_config(
    best_params: Dict[str, Any],
    output_path: Optional[Path] = None,
) -> Path:
    """Locks in and writes the winning hyperparameter configuration to model.best.yaml."""
    target_path = output_path or (Path(__file__).resolve().parent.parent / "config" / "model.best.yaml")
    target_path.parent.mkdir(parents=True, exist_ok=True)

    best_config_dict = {
        "model_name": "chakravyuh-fusion-net-best",
        "model_version": "1.0.0-tuned",
        "device": "auto",
        "hpo_status": "locked_best",
        "tier1": {
            "image_branch": {
                "backbone": best_params.get("backbone", "efficientnet_b0"),
                "pretrained": True,
                "in_channels": 1,
                "embedding_dim": 512,
                "dropout": best_params.get("dropout", 0.2),
            },
            "env_branch": {
                "input_dim": 6,
                "hidden_dims": [64, 128],
                "embedding_dim": 64,
                "dropout": best_params.get("dropout", 0.2) * 0.5,
            },
            "track_branch": {
                "input_dim": 7,
                "hidden_dim": best_params.get("track_hidden_dim", 128),
                "num_layers": 2,
                "embedding_dim": best_params.get("track_hidden_dim", 128),
                "bidirectional": False,
                "dropout": best_params.get("dropout", 0.2) * 0.5,
            },
            "fusion_trunk": {
                "hidden_dims": [best_params.get("fusion_hidden_dim", 512), 256],
                "dropout": best_params.get("dropout", 0.2),
            },
            "heads": {
                "forecast_horizons_hours": [0, 6, 12, 24, 48, 72],
                "num_stage_classes": 6,
                "num_intensity_classes": 7,
                "uncertainty_method": "heteroscedastic",
            },
        },
        "optimization": {
            "learning_rate": best_params.get("learning_rate", 2e-4),
            "weight_decay": best_params.get("weight_decay", 1e-4),
            "backbone_lr_ratio": 0.1,
            "layer_decay": 0.75,
            "scheduler": "cosine_with_warmup",
            "warmup_epochs": 1,
            "early_stopping_patience": 5,
        },
        "loss_weights": {
            "strategy": "homoscedastic_learnable",
            "initial_weights": best_params.get("task_loss_init", {
                "detection": 0.0,
                "stage": 0.0,
                "intensity_reg": 0.0,
                "intensity_cls": 0.0,
                "track": 0.0,
            }),
        },
    }

    with open(target_path, "w", encoding="utf-8") as f:
        yaml.dump(best_config_dict, f, default_flow_style=False, sort_keys=False)

    # Mirror to root config/model.best.yaml
    mirror_path = Path("config/model.best.yaml")
    mirror_path.parent.mkdir(parents=True, exist_ok=True)
    with open(mirror_path, "w", encoding="utf-8") as f:
        yaml.dump(best_config_dict, f, default_flow_style=False, sort_keys=False)

    print(f"[SWEEP] Locked in winning configuration at {target_path} and {mirror_path}")
    return target_path


def update_models_report_sweep(
    sweep_summary: Dict[str, Any],
    report_path: Optional[Path] = None,
) -> None:
    """Records the HPO hyperparameter sweep summary and best config lock-in to models_report.md."""
    rep_path = report_path or Path("ml/cyclone/eval/models_report.md")
    rep_path.parent.mkdir(parents=True, exist_ok=True)

    trials_table_rows = []
    for t in sweep_summary["ranked_trials"]:
        p = t["params"]
        vm = t["val_metrics"]
        rank_icon = "🥇 **WINNER**" if t["trial_id"] == sweep_summary["best_trial_id"] else "Runner-up"
        row = f"| **{t['trial_id']}** ({rank_icon}) | `{p['backbone']}` | {p['learning_rate']:.1e} | {p['dropout']} | {p['track_hidden_dim']} | {p['fusion_hidden_dim']} | {p['weight_decay']:.1e} | **{t['composite_val_score']:.4f}** | {vm['track_mean_error_km']:.1f} km | {vm['intensity_wind_rmse_kt']:.2f} kt | {vm['stage_macro_f1']:.4f} |"
        trials_table_rows.append(row)

    trials_table_str = "\n".join(trials_table_rows)
    best_p = sweep_summary["best_params"]
    best_tm = sweep_summary["best_trial_test_metrics"]

    section = f"""
## 7. Multi-Modal FusionNet Hyperparameter Optimization & Best-Config Lock-In

**Updated:** {sweep_summary['timestamp']}  
**Search Strategy:** Lightweight Grid/Random Multi-Task Sweep ({sweep_summary['total_trials']} trials)  
**Selection Criterion:** Composite Multi-Task Validation Score:
$$\\text{{Score}} = 0.01 \\cdot \\text{{Track Error (km)}} + 0.1 \\cdot \\text{{Intensity RMSE (kt)}} - 1.0 \\cdot \\text{{Stage Macro F1}} + 0.05 \\cdot \\text{{Val Loss}}$$
**Winning Configuration:** `{sweep_summary['best_trial_id']}` (Locked in `config/model.best.yaml`)

### 7.1 HPO Sweep Trial Comparison Matrix

| Trial ID & Status | Backbone | Learning Rate | Dropout | GRU Dim | Fusion Width | Weight Decay | Composite Val Score | Val Track Error | Val Intensity RMSE | Val Stage F1 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
{trials_table_str}

### 7.2 Locked-in Optimal Hyperparameter Configuration
- **Vision Backbone:** `{best_p['backbone']}` with Layer-wise LR Decay (LLRD: $\\text{{scale}} = 0.1 \\times 0.75^{{4 - d}}$)
- **Base Learning Rate:** `{best_p['learning_rate']}` with Cosine Annealing and Linear Warmup (`CosineWarmupScheduler`)
- **Regularization:** Weight Decay `{best_p['weight_decay']}`, Multi-Modal Dropout `{best_p['dropout']}` in trunk and branches
- **Fused Representation:** Kinematic GRU Hidden Dim `{best_p['track_hidden_dim']}` $\\to$ Fusion MLP `{best_p['fusion_hidden_dim']} \\to 256`
- **Multi-Task Balance:** Learnable Homoscedastic Task Uncertainty Loss with balanced priors
- **Test Performance on Locked Configuration:**
  - **Track Forecast Error:** **{best_tm['track_mean_error_km']:.1f} km**
  - **Intensity Wind RMSE:** **{best_tm['intensity_wind_rmse_kt']:.2f} kt**
  - **Stage Macro F1:** **{best_tm['stage_macro_f1']:.4f}**
  - **Detection Accuracy:** **{best_tm['detection_accuracy'] * 100.0:.1f}%**
  - **95% Cone Coverage:** **{best_tm['cone_coverage_pct']:.1f}%**
- **Config Lock-in File:** `ml/cyclone/config/model.best.yaml`
"""

    existing_content = ""
    if rep_path.is_file():
        with open(rep_path, "r", encoding="utf-8") as f:
            existing_content = f.read()

    if "## 7. " in existing_content:
        parts = existing_content.split("## 7. ")
        new_content = parts[0].rstrip() + "\n\n" + section.strip() + "\n"
    else:
        new_content = existing_content.rstrip() + "\n\n" + section.strip() + "\n"

    with open(rep_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    mirror_path = Path("eval/models_report.md")
    mirror_path.parent.mkdir(parents=True, exist_ok=True)
    with open(mirror_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"[REPORT] Sweep results recorded to {rep_path} and {mirror_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run HPO sweep and lock in best FusionNet config.")
    parser.add_argument("--num-trials", type=int, default=3, help="Number of sweep trials to run")
    parser.add_argument("--epochs-per-trial", type=int, default=2, help="Epochs per trial")
    parser.add_argument("--batch-size", type=int, default=8, help="Mini-batch size")
    parser.add_argument("--strategy", type=str, default="random", choices=["random", "grid"], help="Search strategy")
    args = parser.parse_args()

    summary = run_hyperparameter_sweep(
        num_trials=args.num_trials,
        epochs_per_trial=args.epochs_per_trial,
        batch_size=args.batch_size,
        search_strategy=args.strategy,
    )
    update_models_report_sweep(summary)


if __name__ == "__main__":
    main()
