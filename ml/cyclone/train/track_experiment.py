"""Experiment tracking and metric logging layer supporting CSV, TensorBoard, and Weights & Biases."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np


def get_git_commit_hash() -> str:
    """Retrieves current Git commit hash or returns 'unknown' if unavailable."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        if res.returncode == 0:
            return res.stdout.strip()
    except Exception:
        pass
    return "unknown"


def compute_split_manifest_hash(split_dict: dict[str, Sequence[int]] | None = None) -> str:
    """Computes SHA-256 hash of dataset split indices to guarantee data provenance and reproducibility."""
    if not split_dict:
        return "none"
    serialized = json.dumps({k: sorted(list(v)) for k, v in sorted(split_dict.items())})
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:16]


class ExperimentTracker:
    """Thin, robust experiment tracking layer logging to CSV, TensorBoard, and Weights & Biases.

    Hygiene Features:
    1. CSV logger (`metrics.csv`) in `run_dir`.
    2. TensorBoard scalar logging via `torch.utils.tensorboard.SummaryWriter`.
    3. Weights & Biases logging active only if `WANDB_API_KEY` environment variable is set.
    4. Provenance tracking: Logs git commit hash, dataset split manifest hash, and config parameters.
    """

    def __init__(
        self,
        experiment_name: str,
        run_dir: str | Path,
        config: dict[str, Any] | None = None,
        split_indices: dict[str, Sequence[int]] | None = None,
        project_name: str = "chakravyuh-cyclone-ml",
        tags: list[str] | None = None,
    ) -> None:
        self.experiment_name = experiment_name
        self.run_dir = Path(run_dir)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.config = config or {}
        self.project_name = project_name
        self.tags = tags or ["cyclone", "imd"]

        # Provenance metadata
        self.git_commit = get_git_commit_hash()
        self.split_hash = compute_split_manifest_hash(split_indices)
        self.timestamp = datetime.now(timezone.utc).isoformat()

        # 1. Setup CSV logging
        self.csv_path = self.run_dir / "metrics.csv"
        self._csv_writer = None
        self._csv_file = None
        self._csv_headers: list[str] = []

        # 2. Setup TensorBoard logging
        self.tb_writer = None
        try:
            from torch.utils.tensorboard import SummaryWriter

            tb_log_dir = self.run_dir / "tensorboard"
            tb_log_dir.mkdir(parents=True, exist_ok=True)
            self.tb_writer = SummaryWriter(log_dir=str(tb_log_dir))
        except Exception:
            self.tb_writer = None

        # 3. Setup Weights & Biases (only if WANDB_API_KEY present)
        self.wandb_run = None
        wandb_key = os.environ.get("WANDB_API_KEY")
        if wandb_key and wandb_key.strip():
            try:
                import wandb

                self.wandb_run = wandb.init(
                    project=self.project_name,
                    name=f"{self.experiment_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    config={
                        **self.config,
                        "git_commit": self.git_commit,
                        "split_manifest_hash": self.split_hash,
                    },
                    tags=self.tags,
                    dir=str(self.run_dir),
                    reinit=True,
                )
            except Exception as e:
                print(f"[TRACKER] W&B initialization skipped: {e}")
                self.wandb_run = None

        # Save run metadata JSON
        meta = {
            "experiment_name": self.experiment_name,
            "timestamp": self.timestamp,
            "git_commit": self.git_commit,
            "split_manifest_hash": self.split_hash,
            "config": self.config,
        }
        with open(self.run_dir / "run_metadata.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

    def log_epoch(self, epoch: int, metrics: dict[str, Any], step: int | None = None) -> None:
        """Logs per-epoch metrics to CSV, TensorBoard, and Weights & Biases.

        Args:
            epoch: Epoch integer index (1-indexed).
            metrics: Dictionary of metric names and numeric scalar values.
            step: Optional global step.
        """
        curr_step = step if step is not None else epoch

        # Filter numeric scalars for logging
        numeric_metrics = {"epoch": epoch}
        for k, v in metrics.items():
            if isinstance(v, (int, float, np.floating, np.integer)) and not np.isnan(v):
                numeric_metrics[k] = float(v)
            elif isinstance(v, dict):
                # Flatten single-level subdictionaries (e.g. task_losses)
                for sub_k, sub_v in v.items():
                    if isinstance(sub_v, (int, float, np.floating, np.integer)) and not np.isnan(
                        sub_v
                    ):
                        numeric_metrics[f"{k}/{sub_k}"] = float(sub_v)

        # 1. CSV Logging
        if self._csv_file is None:
            self._csv_file = open(self.csv_path, "w", newline="", encoding="utf-8")
            self._csv_headers = list(numeric_metrics.keys())
            self._csv_writer = csv.DictWriter(self._csv_file, fieldnames=self._csv_headers)
            self._csv_writer.writeheader()
        else:
            # Update headers if new keys appeared
            new_keys = [k for k in numeric_metrics.keys() if k not in self._csv_headers]
            if new_keys:
                self._csv_headers.extend(new_keys)
                self._csv_file.close()
                # Reopen with all headers and write entire history if needed
                self._csv_file = open(self.csv_path, "a", newline="", encoding="utf-8")
                self._csv_writer = csv.DictWriter(self._csv_file, fieldnames=self._csv_headers)

        if self._csv_writer:
            self._csv_writer.writerow(numeric_metrics)
            self._csv_file.flush()

        # 2. TensorBoard Logging
        if self.tb_writer is not None:
            for k, v in numeric_metrics.items():
                if k != "epoch":
                    self.tb_writer.add_scalar(k, v, global_step=curr_step)
            self.tb_writer.flush()

        # 3. Weights & Biases Logging
        if self.wandb_run is not None:
            try:
                import wandb

                wandb.log(numeric_metrics, step=curr_step)
            except Exception:
                pass

    def log_summary(self, summary_metrics: dict[str, Any]) -> None:
        """Logs final summary metrics and saves summary JSON."""
        summary_path = self.run_dir / "summary_metrics.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary_metrics, f, indent=2)

        if self.wandb_run is not None:
            try:
                for k, v in summary_metrics.items():
                    if isinstance(v, (int, float, str, bool)):
                        self.wandb_run.summary[k] = v
            except Exception:
                pass

    def finish(self) -> None:
        """Closes all file handles and terminates active experiment sessions."""
        if self._csv_file is not None and not self._csv_file.closed:
            self._csv_file.close()

        if self.tb_writer is not None:
            try:
                self.tb_writer.close()
            except Exception:
                pass

        if self.wandb_run is not None:
            try:
                import wandb

                wandb.finish()
            except Exception:
                pass


__all__ = [
    "ExperimentTracker",
    "get_git_commit_hash",
    "compute_split_manifest_hash",
]
