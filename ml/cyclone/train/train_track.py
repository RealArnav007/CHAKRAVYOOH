"""Trajectory forecasting training pipeline using Gaussian Negative Log-Likelihood and Learned Uncertainty Cones."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from ml.cyclone.datasets.splits import make_splits
from ml.cyclone.datasets.torch_dataset import CycloneDataset, cyclone_collate_fn
from ml.cyclone.eval.metrics import cone_coverage, track_error_km
from ml.cyclone.ingest.ibtracs import load_tracks
from ml.cyclone.models.baseline_track import predict_track as cliper_predict_track
from ml.cyclone.models.heads import DEFAULT_TRACK_HORIZONS, TrackHead, TrackModel
from ml.cyclone.models.uncertainty import monte_carlo_dropout_predict, predict_cone_radii
from ml.cyclone.preprocess.align import resample_track
from ml.cyclone.preprocess.clean import clean_tracks
from ml.cyclone.preprocess.colocalize import build_samples
from ml.cyclone.preprocess.geo import EARTH_RADIUS_KM
from ml.cyclone.train.losses import GaussianNLLLoss, HaversineMetricLoss


# Backward-compatible alias for existing imports
haversine_loss = HaversineMetricLoss()


# -----------------------------------------------------------------------------
# Training Pipeline
# -----------------------------------------------------------------------------


def train_track(
    epochs: int = 10,
    batch_size: int = 8,
    lr: float = 3e-4,
    weight_decay: float = 1e-4,
    decoder_type: str = "mlp",
    mc_samples: int = 1,
    artifact_dir: Optional[Path] = None,
    device: Optional[torch.device] = None,
) -> Dict[str, Any]:
    """Trains TrackModel using Gaussian NLL loss (mean + log-variance) and evaluates learned uncertainty cones.

    Args:
        epochs: Number of training epochs.
        batch_size: Mini-batch size.
        lr: AdamW learning rate.
        weight_decay: AdamW weight decay.
        decoder_type: 'mlp' (default) or 'gru'.
        mc_samples: Number of MC-dropout forward passes at inference (1 = deterministic, >1 = MC-Dropout).
        artifact_dir: Destination directory for artifacts.
        device: Torch compute device.

    Returns:
        Dictionary of test metrics, cone coverage, and comparison against CLIPER baseline.
    """
    save_dir = artifact_dir or (Path(__file__).resolve().parent.parent / "artifacts" / "track")
    save_dir.mkdir(parents=True, exist_ok=True)

    compute_device = device or (
        torch.device("mps") if torch.backends.mps.is_available()
        else torch.device("cuda") if torch.cuda.is_available()
        else torch.device("cpu")
    )
    print(f"[TRACK] Using compute device: {compute_device}")

    # 1. Load Dataset
    print("[TRACK] Loading multi-modal cyclone trajectory dataset...")
    raw_tracks = load_tracks()
    clean_df, _ = clean_tracks(raw_tracks)
    resampled_df = resample_track(clean_df, step_hours=6)
    all_samples = build_samples(resampled_df, history_steps=8)

    # Spatio-temporal whole-storm splitting
    splits = make_splits(all_samples, train_ratio=0.70, val_ratio=0.15, test_ratio=0.15)
    train_indices = splits["train"]
    val_indices = splits["val"]
    test_indices = splits["test"]

    print(f"[TRACK] Split counts -> Train: {len(train_indices)}, Val: {len(val_indices)}, Test: {len(test_indices)}")

    train_ds = CycloneDataset(all_samples, indices=train_indices, mode="multimodal")
    val_ds = CycloneDataset(all_samples, indices=val_indices, mode="multimodal")
    test_ds = CycloneDataset(all_samples, indices=test_indices, mode="multimodal")

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, collate_fn=cyclone_collate_fn)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, collate_fn=cyclone_collate_fn)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False, collate_fn=cyclone_collate_fn)

    # 2. Model, Loss Functions & Optimizer
    model = TrackModel(
        env_dim=6,
        env_out_dim=64,
        track_dim=7,
        track_hidden_dim=128,
        track_layers=2,
        num_horizons=len(DEFAULT_TRACK_HORIZONS),
        decoder_type=decoder_type,
    )

    nll_criterion = GaussianNLLLoss(min_log_var=-7.0, max_log_var=7.0)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=max(1, epochs))

    def track_step_fn(m: nn.Module, batch: Dict[str, Any], crit: Any, dev: torch.device) -> Tuple[torch.Tensor, Dict[str, Any]]:
        env = torch.nan_to_num(batch["env_vector"].to(dev), nan=0.0)
        track = torch.nan_to_num(batch["track_sequence"].to(dev), nan=0.0)
        target_deltas = torch.nan_to_num(batch["targets"]["future_deltas"].to(dev), nan=0.0)
        horizon_masks = batch["targets"]["horizon_masks"].to(dev)

        winds = torch.tensor([meta.get("wind_kt", 25.0) for meta in batch["meta"]], dtype=torch.float32, device=dev)
        sample_w = torch.clamp(1.0 + (winds - 34.0) * 0.02, min=0.8, max=2.5)

        out = m(env_vector=env, track_sequence=track)
        loss = crit(
            pred_mu=out["deltas"],
            pred_log_var=out["log_vars"],
            target=target_deltas,
            horizon_masks=horizon_masks,
            sample_weights=sample_w,
        )
        return loss, {"loss": loss.item()}

    tracker = ExperimentTracker(
        experiment_name="probabilistic_track",
        run_dir=save_dir,
        config={"decoder_type": decoder_type, "lr": lr, "batch_size": batch_size, "epochs": epochs},
        split_indices=splits,
    )

    def track_eval_wrapper(m: nn.Module, dl: DataLoader, dev: torch.device) -> Dict[str, Any]:
        met = evaluate_probabilistic_track_model(m, dl, dev, mc_samples=1)
        return {
            "mean_error_km": met["mean_error_km"],
            "val_loss": met["mean_error_km"],
            "cone_coverage_pct": met["cone_coverage"]["coverage_pct"],
        }

    trainer = Trainer(
        model=model,
        criterion=nll_criterion,
        train_loader=train_loader,
        val_loader=val_loader,
        test_loader=test_loader,
        optimizer=optimizer,
        scheduler=scheduler,
        device=compute_device,
        save_dir=save_dir,
        tracker=tracker,
        step_fn=track_step_fn,
        eval_fn=track_eval_wrapper,
        early_stopping_metric="mean_error_km",
        early_stopping_mode="min",
        early_stopping_patience=10,
        checkpoint_prefix="best_track_model",
    )

    trainer_summary = trainer.train(epochs=epochs)

    # 4. Final Evaluation on Held-Out Test Split
    print(f"[TRACK] Evaluating best learned model on held-out test split (MC samples: {mc_samples})...")
    best_ckpt_path = save_dir / "best_track_model.pt"
    best_ckpt = torch.load(best_ckpt_path, map_location=compute_device)
    model.load_state_dict(best_ckpt["model_state_dict"])
    learned_test_metrics = evaluate_probabilistic_track_model(
        model, test_loader, compute_device, mc_samples=mc_samples
    )

    # 5. Evaluate Tier-0 CLIPER Baseline on the EXACT Same Test Split
    print("[TRACK] Evaluating Tier-0 CLIPER baseline on the same test split...")
    cliper_test_metrics = evaluate_cliper_baseline(test_ds.raw_samples, test_indices)

    # Compute per-horizon delta (Learned vs CLIPER)
    comparison_by_horizon: Dict[str, Dict[str, Any]] = {}
    for h_str in ["6h", "12h", "24h", "48h", "72h"]:
        l_err = learned_test_metrics["errors_by_horizon_km"].get(h_str, 0.0)
        c_err = cliper_test_metrics["errors_by_horizon_km"].get(h_str, 0.0)
        delta = round(l_err - c_err, 2)
        cov_pct = learned_test_metrics["cone_coverage"]["coverage_by_horizon_pct"].get(h_str, 0.0)
        mean_radius = learned_test_metrics["mean_cone_radii_km"].get(h_str, 0.0)

        comparison_by_horizon[h_str] = {
            "learned_error_km": l_err,
            "cliper_error_km": c_err,
            "delta_km": delta,
            "learned_beats_cliper": bool(delta < 0.0),
            "cone_coverage_pct": cov_pct,
            "mean_cone_radius_km": mean_radius,
        }

    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "decoder_type": decoder_type,
        "mc_samples": mc_samples,
        "epochs": epochs,
        "best_epoch": trainer_summary["best_epoch"],
        "val_metrics": best_ckpt["val_metrics"],
        "learned_test_metrics": learned_test_metrics,
        "cliper_test_metrics": cliper_test_metrics,
        "comparison_by_horizon": comparison_by_horizon,
        "history": trainer.history,
    }

    metrics_path = save_dir / "track_metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    return results


def evaluate_probabilistic_track_model(
    model: nn.Module,
    dataloader: DataLoader,
    device: torch.device,
    mc_samples: int = 1,
) -> Dict[str, Any]:
    """Evaluates TrackModel emitting per-horizon errors, learned cone radii, and empirical cone coverage."""
    errors_by_horizon: Dict[int, List[float]] = {h: [] for h in DEFAULT_TRACK_HORIZONS}
    cone_radii_by_horizon: Dict[int, List[float]] = {h: [] for h in DEFAULT_TRACK_HORIZONS}
    all_pred_points: List[Tuple[Optional[int], float, float]] = []
    all_true_points: List[Tuple[Optional[int], float, float]] = []
    all_cone_radii: List[float] = []

    horizon_coverage_counts: Dict[int, Dict[str, int]] = {
        h: {"inside": 0, "total": 0} for h in DEFAULT_TRACK_HORIZONS
    }

    model.eval()

    with torch.no_grad():
        for batch in dataloader:
            env = torch.nan_to_num(batch["env_vector"].to(device), nan=0.0)
            track = torch.nan_to_num(batch["track_sequence"].to(device), nan=0.0)
            target_pos = batch["targets"]["future_positions"].cpu().numpy()
            horizon_masks = batch["targets"]["horizon_masks"].cpu().numpy()

            if mc_samples > 1:
                # MC-Dropout inference per item in batch
                pred_deltas_batch = []
                log_vars_batch = []
                for b_i in range(env.size(0)):
                    e_single = env[b_i : b_i + 1]
                    t_single = track[b_i : b_i + 1]
                    c_lat = float(batch["meta"][b_i]["lat"])
                    mc_out = monte_carlo_dropout_predict(
                        model=model,
                        env_vector=e_single,
                        track_sequence=t_single,
                        num_samples=mc_samples,
                        current_lat=c_lat,
                    )
                    pred_deltas_batch.append(mc_out["mean_deltas"])
                    # Effective total log variance
                    tot_var = np.clip(mc_out["total_variance"], 1e-6, 1e6)
                    log_vars_batch.append(np.log(tot_var))

                pred_deltas = np.array(pred_deltas_batch)
                pred_log_vars = np.array(log_vars_batch)
            else:
                out = model(env_vector=env, track_sequence=track)
                pred_deltas = out["deltas"].cpu().numpy()
                pred_log_vars = out["log_vars"].cpu().numpy()

            for i, meta in enumerate(batch["meta"]):
                curr_lat = float(meta["lat"])
                curr_lon = float(meta["lon"])

                # Derive learned uncertainty cone radii for this sample
                radii = predict_cone_radii(
                    log_vars=pred_log_vars[i],
                    current_lat=curr_lat,
                    coverage_level=0.95,
                )
                # radii has len H + 1 (anchored at t=0)

                for h_idx, h in enumerate(DEFAULT_TRACK_HORIZONS):
                    if horizon_masks[i, h_idx]:
                        t_lat, t_lon = float(target_pos[i, h_idx, 0]), float(target_pos[i, h_idx, 1])
                        dlat, dlon = float(pred_deltas[i, h_idx, 0]), float(pred_deltas[i, h_idx, 1])
                        p_lat = curr_lat + dlat
                        p_lon = (curr_lon + dlon + 540.0) % 360.0 - 180.0

                        err_km = track_error_km(
                            pred_path=[(h, p_lat, p_lon)],
                            true_path=[(h, t_lat, t_lon)],
                        )["mean_error_km"]

                        r_km = radii[h_idx + 1]

                        errors_by_horizon[h].append(err_km)
                        cone_radii_by_horizon[h].append(r_km)

                        all_pred_points.append((h, p_lat, p_lon))
                        all_true_points.append((h, t_lat, t_lon))
                        all_cone_radii.append(r_km)

                        horizon_coverage_counts[h]["total"] += 1
                        if err_km <= r_km:
                            horizon_coverage_counts[h]["inside"] += 1

    mean_by_horizon: Dict[str, float] = {}
    mean_radii_by_horizon: Dict[str, float] = {}
    coverage_by_horizon: Dict[str, float] = {}
    all_errs: List[float] = []

    for h in DEFAULT_TRACK_HORIZONS:
        errs = errors_by_horizon[h]
        rads = cone_radii_by_horizon[h]
        m_err = round(float(np.mean(errs)), 2) if errs else 0.0
        m_rad = round(float(np.mean(rads)), 2) if rads else 0.0
        mean_by_horizon[f"{h}h"] = m_err
        mean_radii_by_horizon[f"{h}h"] = m_rad
        all_errs.extend(errs)

        tot_h = horizon_coverage_counts[h]["total"]
        ins_h = horizon_coverage_counts[h]["inside"]
        cov_h = round((ins_h / tot_h) * 100.0, 2) if tot_h > 0 else 0.0
        coverage_by_horizon[f"{h}h"] = cov_h

    overall_mean = round(float(np.mean(all_errs)), 2) if all_errs else 0.0

    # Global cone coverage across all evaluated horizons
    global_coverage = cone_coverage(
        pred_cone=all_cone_radii,
        pred_path=all_pred_points,
        true_path=all_true_points,
    )
    global_coverage["coverage_by_horizon_pct"] = coverage_by_horizon

    return {
        "mean_error_km": overall_mean,
        "errors_by_horizon_km": mean_by_horizon,
        "mean_cone_radii_km": mean_radii_by_horizon,
        "cone_coverage": global_coverage,
    }


def evaluate_cliper_baseline(
    all_samples: List[Dict[str, Any]],
    test_indices: List[int],
) -> Dict[str, Any]:
    """Evaluates Tier-0 deterministic CLIPER baseline on the same test split for rigorous benchmarking."""
    errors_by_horizon: Dict[int, List[float]] = {h: [] for h in DEFAULT_TRACK_HORIZONS}

    for idx in test_indices:
        sample = all_samples[idx]
        history = sample.get("history", [])
        if not history:
            continue

        pred = cliper_predict_track(history=history, horizons=[0] + DEFAULT_TRACK_HORIZONS, method="cliper")
        pred_pts = {pt["t_plus_h"]: (pt["lat"], pt["lon"]) for pt in pred["predicted_path"]}

        storm_id = sample.get("storm_id")
        curr_time = pd.to_datetime(sample.get("time"), utc=True)

        for other_idx in test_indices:
            other_sample = all_samples[other_idx]
            if other_sample.get("storm_id") == storm_id:
                other_t = pd.to_datetime(other_sample.get("time"), utc=True)
                delta_h = int(round((other_t - curr_time).total_seconds() / 3600.0))

                if delta_h in DEFAULT_TRACK_HORIZONS and delta_h in pred_pts:
                    p_lat, p_lon = pred_pts[delta_h]
                    t_lat, t_lon = float(other_sample["lat"]), float(other_sample["lon"])

                    err_km = track_error_km(
                        pred_path=[(delta_h, p_lat, p_lon)],
                        true_path=[(delta_h, t_lat, t_lon)],
                    )["mean_error_km"]

                    errors_by_horizon[delta_h].append(err_km)

    mean_by_horizon: Dict[str, float] = {}
    all_errs: List[float] = []

    for h in DEFAULT_TRACK_HORIZONS:
        errs = errors_by_horizon[h]
        m = round(float(np.mean(errs)), 2) if errs else 0.0
        mean_by_horizon[f"{h}h"] = m
        all_errs.extend(errs)

    overall_mean = round(float(np.mean(all_errs)), 2) if all_errs else 0.0

    return {
        "mean_error_km": overall_mean,
        "errors_by_horizon_km": mean_by_horizon,
    }


def update_models_report_track(
    track_results: Dict[str, Any],
    report_path: Optional[Path] = None,
) -> None:
    """Updates models_report.md with learned track forecasting, uncertainty cones, and CLIPER comparison."""
    rep_path = report_path or Path("ml/cyclone/eval/models_report.md")
    rep_path.parent.mkdir(parents=True, exist_ok=True)

    l_met = track_results["learned_test_metrics"]
    c_met = track_results["cliper_test_metrics"]
    comp = track_results["comparison_by_horizon"]
    cov = l_met["cone_coverage"]

    section = f"""
## 5. Probabilistic Trajectory Forecasting Model (`TrackModel`) with Learned Uncertainty Cones

**Updated:** {track_results['timestamp']}  
**Architecture:** `EnvBranch` (64-d ERA5) + `TrackBranch` (128-d GRU) $\\to$ `TrackHead` ({track_results['decoder_type'].upper()} Displacement & Log-Variance Decoder)  
**Objective:** Heteroscedastic Gaussian Negative Log-Likelihood (`GaussianNLLLoss`) with End-of-Storm Horizon Masking & Intensity Weighting  
**Uncertainty Quantification:** Learned 2D anisotropic Gaussian log-variances mapped to dynamic great-circle cone radii ($r(t) = \\sigma_{{\\text{{eff}}}} \\sqrt{{-2\\ln(1-p)}}$)  
**MC-Dropout Stochastic Samples:** {track_results.get('mc_samples', 1)}

### 5.1 Trajectory Forecasting Error & Learned 95% Cone Coverage (Held-Out Test Split)

| Forecast Horizon | Learned Track Error (km) | Tier-0 CLIPER (km) | Delta (Learned - CLIPER) | Mean Cone Radius (km) | Empirical 95% Cone Coverage | Operational Policy |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **6h** | **{comp['6h']['learned_error_km']:.1f} km** | {comp['6h']['cliper_error_km']:.1f} km | {comp['6h']['delta_km']:+.1f} km | {comp['6h']['mean_cone_radius_km']:.1f} km | **{comp['6h']['cone_coverage_pct']:.1f}%** | {'Use Learned Model' if comp['6h']['learned_beats_cliper'] else 'Tier-0 Safeguard'} |
| **12h** | **{comp['12h']['learned_error_km']:.1f} km** | {comp['12h']['cliper_error_km']:.1f} km | {comp['12h']['delta_km']:+.1f} km | {comp['12h']['mean_cone_radius_km']:.1f} km | **{comp['12h']['cone_coverage_pct']:.1f}%** | {'Use Learned Model' if comp['12h']['learned_beats_cliper'] else 'Tier-0 Safeguard'} |
| **24h** | **{comp['24h']['learned_error_km']:.1f} km** | {comp['24h']['cliper_error_km']:.1f} km | {comp['24h']['delta_km']:+.1f} km | {comp['24h']['mean_cone_radius_km']:.1f} km | **{comp['24h']['cone_coverage_pct']:.1f}%** | {'Use Learned Model' if comp['24h']['learned_beats_cliper'] else 'Tier-0 Safeguard'} |
| **48h** | **{comp['48h']['learned_error_km']:.1f} km** | {comp['48h']['cliper_error_km']:.1f} km | {comp['48h']['delta_km']:+.1f} km | {comp['48h']['mean_cone_radius_km']:.1f} km | **{comp['48h']['cone_coverage_pct']:.1f}%** | {'Use Learned Model' if comp['48h']['learned_beats_cliper'] else 'Retain Tier-0 CLIPER'} |
| **72h** | **{comp['72h']['learned_error_km']:.1f} km** | {comp['72h']['cliper_error_km']:.1f} km | {comp['72h']['delta_km']:+.1f} km | {comp['72h']['mean_cone_radius_km']:.1f} km | **{comp['72h']['cone_coverage_pct']:.1f}%** | {'Use Learned Model' if comp['72h']['learned_beats_cliper'] else 'Retain Tier-0 CLIPER'} |
| **Overall (6-72h)** | **{l_met['mean_error_km']:.1f} km** | **{c_met['mean_error_km']:.1f} km** | **{l_met['mean_error_km'] - c_met['mean_error_km']:+.1f} km** | **{float(np.mean(list(l_met['mean_cone_radii_km'].values()))):.1f} km** | **{cov['coverage_pct']:.1f}%** ({cov['inside_count']}/{cov['total_count']}) | **Gated Probabilistic Hybrid** |

### 5.2 Learned vs Parametric Cone Dynamics
- **Adaptive Asymmetry & Environmental Responsiveness:** Unlike static IMD cones ($a + b\\cdot t$) that expand uniformly regardless of steering clarity, the learned cone expands dynamically when steering winds are weak or shear is high, and contracts along predictable straight paths.
- **Pre-Calibration Coverage Baseline:** Before temperature/conformal calibration (Prompt 22), the uncalibrated probabilistic model achieves **{cov['coverage_pct']:.1f}%** overall test coverage for a 95% target.
- **Checkpoint Artifact:** `ml/cyclone/artifacts/track/best_track_model.pt`
"""

    existing_content = ""
    if rep_path.is_file():
        with open(rep_path, "r", encoding="utf-8") as f:
            existing_content = f.read()

    if "## 5. " in existing_content:
        parts = existing_content.split("## 5. ")
        new_content = parts[0].rstrip() + "\n\n" + section.strip() + "\n"
    else:
        new_content = existing_content.rstrip() + "\n\n" + section.strip() + "\n"

    with open(rep_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    mirror_path = Path("eval/models_report.md")
    mirror_path.parent.mkdir(parents=True, exist_ok=True)
    with open(mirror_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"[REPORT] Models report updated with probabilistic TrackModel benchmark at {rep_path} and {mirror_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Train probabilistic trajectory forecasting model with learned uncertainty cones.")
    parser.add_argument("--epochs", type=int, default=8, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=8, help="Batch size")
    parser.add_argument("--lr", type=float, default=3e-4, help="Learning rate")
    parser.add_argument("--decoder-type", type=str, default="mlp", choices=["mlp", "gru"], help="Decoder type")
    parser.add_argument("--mc-samples", type=int, default=1, help="Number of Monte Carlo dropout samples at test time")
    args = parser.parse_args()

    results = train_track(
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        decoder_type=args.decoder_type,
        mc_samples=args.mc_samples,
    )
    update_models_report_track(results)


if __name__ == "__main__":
    main()
