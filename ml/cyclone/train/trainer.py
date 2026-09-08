"""Reusable PyTorch Trainer with AMP mixed-precision, gradient clipping, checkpointing, and early stopping."""

from __future__ import annotations

import random
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from ml.cyclone.train.track_experiment import ExperimentTracker


def seed_everything(seed: int = 42) -> None:
    """Sets deterministic random seed across Python, NumPy, and PyTorch backends."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


class Trainer:
    """Unified, production-grade PyTorch Trainer for cyclone forecasting models.

    Key Capabilities:
    1. Automatic Mixed Precision (AMP) via `torch.amp.autocast` and `GradScaler`.
    2. Gradient norm clipping (`torch.nn.utils.clip_grad_norm_`).
    3. Resumable Checkpointing: Saves `best_checkpoint.pt` and `last_checkpoint.pt` containing model, optimizer, scheduler, and epoch state.
    4. Early Stopping on configurable validation metric ('min' or 'max' mode with patience).
    5. Integrated Experiment Tracking (CSV, TensorBoard, Weights & Biases).
    """

    def __init__(
        self,
        model: nn.Module,
        criterion: nn.Module | Callable[..., Any],
        train_loader: DataLoader,
        val_loader: DataLoader | None = None,
        test_loader: DataLoader | None = None,
        optimizer: torch.optim.Optimizer | None = None,
        scheduler: Any | None = None,
        device: torch.device | None = None,
        save_dir: str | Path | None = None,
        tracker: ExperimentTracker | None = None,
        step_fn: (
            Callable[
                [nn.Module, dict[str, Any], nn.Module | Callable, torch.device],
                tuple[torch.Tensor, dict[str, Any]],
            ]
            | None
        ) = None,
        eval_fn: Callable[[nn.Module, DataLoader, torch.device], dict[str, Any]] | None = None,
        test_eval_fn: Callable[[nn.Module, DataLoader, torch.device], dict[str, Any]] | None = None,
        early_stopping_metric: str = "val_loss",
        early_stopping_mode: str = "min",
        early_stopping_patience: int = 10,
        gradient_clip_val: float = 5.0,
        use_amp: bool = True,
        checkpoint_prefix: str = "best_model",
        seed: int = 42,
    ) -> None:
        seed_everything(seed)
        self.device = device or (
            torch.device("mps")
            if torch.backends.mps.is_available()
            else torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
        )
        self.model = model.to(self.device)
        self.criterion = (
            criterion.to(self.device) if isinstance(criterion, nn.Module) else criterion
        )

        self.train_loader = train_loader
        self.val_loader = val_loader
        self.test_loader = test_loader

        self.optimizer = optimizer or torch.optim.AdamW(
            self.model.parameters(), lr=3e-4, weight_decay=1e-4
        )
        self.scheduler = scheduler
        self.save_dir = Path(save_dir) if save_dir else Path("artifacts")
        self.save_dir.mkdir(parents=True, exist_ok=True)

        self.tracker = tracker
        self.step_fn = step_fn
        self.eval_fn = eval_fn
        self.test_eval_fn = test_eval_fn or eval_fn

        self.early_stopping_metric = early_stopping_metric
        self.early_stopping_mode = early_stopping_mode.lower()
        self.early_stopping_patience = early_stopping_patience
        self.gradient_clip_val = gradient_clip_val
        self.checkpoint_prefix = checkpoint_prefix

        # AMP Configuration
        self.use_amp = use_amp and (self.device.type in ["cuda", "mps"])
        self.device_type = (
            "cuda"
            if self.device.type == "cuda"
            else ("cpu" if self.device.type == "cpu" else "mps")
        )
        self.scaler = (
            torch.amp.GradScaler("cuda") if (self.use_amp and self.device.type == "cuda") else None
        )

        # State tracking
        self.best_metric_val = float("inf") if self.early_stopping_mode == "min" else float("-inf")
        self.best_epoch = 0
        self.patience_counter = 0
        self.history: list[dict[str, Any]] = []

    def _default_step(
        self,
        batch: dict[str, Any],
    ) -> tuple[torch.Tensor, dict[str, Any]]:
        """Default batch execution for MultiTask and single-head pipelines."""
        if self.step_fn is not None:
            return self.step_fn(self.model, batch, self.criterion, self.device)

        # Multi-modal CycloneDataset batch structure
        img = batch.get("image")
        if img is not None:
            img = img.to(self.device)
        avail = batch.get("image_available")
        if avail is not None:
            avail = avail.to(self.device)

        env = batch.get("env_vector")
        if env is not None:
            env = torch.nan_to_num(env.to(self.device), nan=0.0)

        track = batch.get("track_sequence")
        if track is not None:
            track = torch.nan_to_num(track.to(self.device), nan=0.0)

        targets = batch.get("targets", {})
        device_targets = {}
        for k, v in targets.items():
            if isinstance(v, torch.Tensor):
                device_targets[k] = v.to(self.device)
            else:
                device_targets[k] = v

        # Forward pass
        if img is not None and env is not None and track is not None:
            preds = self.model(img=img, env_vector=env, track_sequence=track, image_available=avail)
        elif img is not None:
            preds = self.model(img=img, image_available=avail)
        elif env is not None and track is not None:
            preds = self.model(env_vector=env, track_sequence=track)
        else:
            raise ValueError("Unsupported batch input structure for Trainer.")

        loss_out = self.criterion(preds, device_targets)
        loss = loss_out["loss"] if isinstance(loss_out, dict) and "loss" in loss_out else loss_out

        aux = loss_out if isinstance(loss_out, dict) else {"loss": loss.item()}
        return loss, aux

    def train_epoch(self, epoch: int) -> dict[str, float]:
        """Runs one full training epoch."""
        self.model.train()
        epoch_losses: list[float] = []
        task_losses_accum: dict[str, list[float]] = {}

        for batch in self.train_loader:
            self.optimizer.zero_grad()

            if self.scaler is not None:
                with torch.amp.autocast(device_type="cuda"):
                    loss, aux = self._default_step(batch)

                if torch.isnan(loss) or torch.isinf(loss):
                    continue

                self.scaler.scale(loss).backward()
                if self.gradient_clip_val > 0:
                    self.scaler.unscale_(self.optimizer)
                    torch.nn.utils.clip_grad_norm_(
                        self.model.parameters(), max_norm=self.gradient_clip_val
                    )
                self.scaler.step(self.optimizer)
                self.scaler.update()
            else:
                loss, aux = self._default_step(batch)

                if torch.isnan(loss) or torch.isinf(loss):
                    continue

                loss.backward()
                if self.gradient_clip_val > 0:
                    torch.nn.utils.clip_grad_norm_(
                        self.model.parameters(), max_norm=self.gradient_clip_val
                    )
                self.optimizer.step()

            epoch_losses.append(loss.item())

            # Accumulate sub-losses if dictionary
            if isinstance(aux, dict):
                raw_l = aux.get("raw_losses", {})
                for k, v in raw_l.items():
                    if k not in task_losses_accum:
                        task_losses_accum[k] = []
                    task_losses_accum[k].append(float(v))

        metrics = {"train_loss": round(float(np.mean(epoch_losses)), 4) if epoch_losses else 0.0}
        for k, v_list in task_losses_accum.items():
            metrics[f"train_{k}_loss"] = round(float(np.mean(v_list)), 4)

        return metrics

    def validate(self) -> dict[str, Any]:
        """Runs validation using custom eval_fn or default validation loss."""
        if self.val_loader is None:
            return {}

        if self.eval_fn is not None:
            return self.eval_fn(self.model, self.val_loader, self.device)

        self.model.eval()
        val_losses: list[float] = []

        with torch.no_grad():
            for batch in self.val_loader:
                loss, _ = self._default_step(batch)
                if not (torch.isnan(loss) or torch.isinf(loss)):
                    val_losses.append(loss.item())

        return {"val_loss": round(float(np.mean(val_losses)), 4) if val_losses else 0.0}

    def train(
        self,
        epochs: int = 10,
        resume_from: str | Path | None = None,
    ) -> dict[str, Any]:
        """Runs end-to-end training loop with early stopping, checkpointing, and evaluation.

        Args:
            epochs: Total number of epochs to train.
            resume_from: Optional path to checkpoint to resume training state.

        Returns:
            Dictionary containing best checkpoint metadata, test evaluation results, and training history.
        """
        start_epoch = 1
        if resume_from and Path(resume_from).is_file():
            start_epoch = self.load_checkpoint(resume_from) + 1
            print(f"[TRAINER] Resumed state from {resume_from} (Starting at epoch {start_epoch})")

        print(
            f"[TRAINER] Starting training on {self.device} for {epochs} epochs (AMP: {self.use_amp})..."
        )
        best_ckpt_path = self.save_dir / f"{self.checkpoint_prefix}.pt"
        last_ckpt_path = self.save_dir / f"last_{self.checkpoint_prefix}.pt"

        for epoch in range(start_epoch, epochs + 1):
            train_metrics = self.train_epoch(epoch)

            if self.scheduler is not None:
                self.scheduler.step()

            # Validation
            val_metrics = self.validate()
            combined_metrics = {**train_metrics, **val_metrics}

            # Log to tracker
            if self.tracker is not None:
                self.tracker.log_epoch(epoch=epoch, metrics=combined_metrics)

            self.history.append({"epoch": epoch, **combined_metrics})

            # Check early stopping metric
            curr_val = val_metrics.get(self.early_stopping_metric, train_metrics["train_loss"])
            is_improvement = (
                (curr_val < self.best_metric_val)
                if self.early_stopping_mode == "min"
                else (curr_val > self.best_metric_val)
            )

            # Print status
            val_summary = " | ".join(
                [
                    f"{k}: {v:.4f}" if isinstance(v, float) else f"{k}: {v}"
                    for k, v in val_metrics.items()
                ]
            )
            print(
                f"Epoch {epoch:02d}/{epochs:02d} | Train Loss: {train_metrics['train_loss']:.4f} | {val_summary}"
            )

            # Save last checkpoint
            self.save_checkpoint(
                file_path=last_ckpt_path,
                epoch=epoch,
                metric_val=curr_val,
                val_metrics=val_metrics,
            )

            if is_improvement:
                self.best_metric_val = curr_val
                self.best_epoch = epoch
                self.patience_counter = 0
                self.save_checkpoint(
                    file_path=best_ckpt_path,
                    epoch=epoch,
                    metric_val=curr_val,
                    val_metrics=val_metrics,
                )
            else:
                self.patience_counter += 1
                if self.patience_counter >= self.early_stopping_patience:
                    print(
                        f"[TRAINER] Early stopping triggered at epoch {epoch} (No improvement for {self.early_stopping_patience} epochs)."
                    )
                    break

        # Final Test Split Evaluation using best model checkpoint
        test_results = {}
        if self.test_loader is not None and best_ckpt_path.is_file():
            print(
                f"[TRAINER] Loading best checkpoint from {best_ckpt_path} for test split evaluation..."
            )
            best_ckpt = torch.load(best_ckpt_path, map_location=self.device)
            self.model.load_state_dict(best_ckpt["model_state_dict"])
            test_results = (
                self.test_eval_fn(self.model, self.test_loader, self.device)
                if self.test_eval_fn
                else self.validate()
            )

        summary = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "best_epoch": self.best_epoch,
            "best_metric": self.early_stopping_metric,
            "best_metric_value": self.best_metric_val,
            "best_checkpoint_path": str(best_ckpt_path),
            "test_metrics": test_results,
            "history": self.history,
        }

        if self.tracker is not None:
            self.tracker.log_summary(summary)
            self.tracker.finish()

        return summary

    def save_checkpoint(
        self,
        file_path: Path,
        epoch: int,
        metric_val: float,
        val_metrics: dict[str, Any],
    ) -> None:
        """Saves full resumable model and optimizer state dictionary with git commit and config hash provenance."""
        from ml.cyclone.train.track_experiment import get_git_commit_hash

        git_hash = get_git_commit_hash()

        config_p = Path("ml/cyclone/config/model.best.yaml")
        config_hash = "none"
        if config_p.is_file():
            import hashlib

            config_hash = hashlib.sha256(config_p.read_bytes()).hexdigest()[:16]

        ckpt = {
            "epoch": epoch,
            "git_commit": git_hash,
            "config_hash": config_hash,
            "model_state_dict": self.model.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "scheduler_state_dict": self.scheduler.state_dict() if self.scheduler else None,
            "metric_value": metric_val,
            "val_metrics": val_metrics,
            "history": self.history,
        }
        torch.save(ckpt, file_path)

    def load_checkpoint(self, checkpoint_path: str | Path) -> int:
        """Loads model and optimizer state, returning resumed epoch index."""
        ckpt = torch.load(checkpoint_path, map_location=self.device)
        self.model.load_state_dict(ckpt["model_state_dict"])
        if "optimizer_state_dict" in ckpt and self.optimizer:
            self.optimizer.load_state_dict(ckpt["optimizer_state_dict"])
        if "scheduler_state_dict" in ckpt and self.scheduler and ckpt["scheduler_state_dict"]:
            self.scheduler.load_state_dict(ckpt["scheduler_state_dict"])
        return int(ckpt.get("epoch", 0))


__all__ = [
    "Trainer",
    "seed_everything",
]
