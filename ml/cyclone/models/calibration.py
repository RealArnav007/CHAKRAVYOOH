"""Post-hoc confidence calibration and uncertainty cone variance recalibration."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn as nn


class TemperatureScaler(nn.Module):
    """Post-hoc Temperature Scaling for probability calibration (Guo et al., 2017).

    Learns a single scalar parameter T > 0 on the validation split by minimizing Negative Log-Likelihood (NLL).
    Temperature scaling softens or sharpens logits without changing the argmax prediction (preserving accuracy).
    """

    def __init__(
        self, initial_temp: float = 1.5, min_temp: float = 0.05, max_temp: float = 10.0
    ) -> None:
        super().__init__()
        self.min_temp = min_temp
        self.max_temp = max_temp
        self.temperature = nn.Parameter(torch.tensor([float(initial_temp)], dtype=torch.float32))

    def forward(self, logits: torch.Tensor) -> torch.Tensor:
        """Scales logits by temperature: scaled_logits = logits / T."""
        temp = torch.clamp(self.temperature, min=self.min_temp, max=self.max_temp)
        return logits / temp

    def fit(
        self,
        logits: torch.Tensor | np.ndarray,
        targets: torch.Tensor | np.ndarray,
        is_binary: bool = False,
        lr: float = 0.01,
        max_iter: int = 150,
    ) -> float:
        """Optimizes temperature T on validation split logits and targets using L-BFGS/Adam.

        Args:
            logits: (N,) or (N, 1) for binary, or (N, C) for multi-class.
            targets: (N,) true integer classes or binary floats.
            is_binary: If True, uses BCEWithLogitsLoss; otherwise CrossEntropyLoss.
            lr: Learning rate for optimization.
            max_iter: Maximum optimization iterations.

        Returns:
            Fitted temperature float value.
        """
        if isinstance(logits, np.ndarray):
            logits_t = torch.tensor(logits, dtype=torch.float32)
        else:
            logits_t = logits.detach().float()

        if isinstance(targets, np.ndarray):
            targets_t = torch.tensor(targets)
        else:
            targets_t = targets.detach()

        # Detach and set up optimizer
        self.temperature.data.fill_(1.5)
        optimizer = torch.optim.LBFGS([self.temperature], lr=lr, max_iter=max_iter)

        if is_binary:
            criterion = nn.BCEWithLogitsLoss()
            target_f = targets_t.view(-1, 1).float()
            logits_f = logits_t.view(-1, 1)

            def eval_loss() -> torch.Tensor:
                optimizer.zero_grad()
                temp = torch.clamp(self.temperature, min=self.min_temp, max=self.max_temp)
                scaled = logits_f / temp
                loss = criterion(scaled, target_f)
                loss.backward()
                return loss

        else:
            criterion = nn.CrossEntropyLoss()
            target_f = targets_t.view(-1).long()

            def eval_loss() -> torch.Tensor:
                optimizer.zero_grad()
                temp = torch.clamp(self.temperature, min=self.min_temp, max=self.max_temp)
                scaled = logits_t / temp
                loss = criterion(scaled, target_f)
                loss.backward()
                return loss

        optimizer.step(eval_loss)

        fitted_t = float(torch.clamp(self.temperature, min=self.min_temp, max=self.max_temp).item())
        self.temperature.data.fill_(fitted_t)
        return round(fitted_t, 4)

    def predict_proba(
        self, logits: torch.Tensor | np.ndarray, is_binary: bool = False
    ) -> np.ndarray:
        """Returns calibrated probabilities after temperature scaling."""
        t_val = float(torch.clamp(self.temperature, min=self.min_temp, max=self.max_temp).item())
        logits_arr = (
            logits.detach().cpu().numpy()
            if isinstance(logits, torch.Tensor)
            else np.asarray(logits)
        )

        scaled = logits_arr / t_val
        if is_binary:
            # Sigmoid
            scaled_clip = np.clip(scaled, -30.0, 30.0)
            return 1.0 / (1.0 + np.exp(-scaled_clip))
        else:
            # Softmax
            exp_s = np.exp(scaled - np.max(scaled, axis=-1, keepdims=True))
            return exp_s / np.sum(exp_s, axis=-1, keepdims=True)

    def to_dict(self) -> dict[str, Any]:
        return {"temperature": float(self.temperature.item())}

    def from_dict(self, data: dict[str, Any]) -> None:
        self.temperature.data.fill_(float(data.get("temperature", 1.0)))


class VarianceRecalibrator:
    """Empirical Variance & Quantile Recalibrator for Trajectory Uncertainty Cones.

    Recalibrates predicted cone radii so that the empirical coverage on validation data
    matches the target nominal probability (e.g. 95% of future cyclone positions lie within the cone).
    """

    def __init__(
        self,
        target_coverage: float = 0.95,
        global_multiplier: float = 1.0,
        per_horizon_multipliers: dict[str, float] | None = None,
    ) -> None:
        self.target_coverage = target_coverage
        self.global_multiplier = global_multiplier
        self.per_horizon_multipliers = per_horizon_multipliers or {
            "6h": 1.0,
            "12h": 1.0,
            "24h": 1.0,
            "48h": 1.0,
            "72h": 1.0,
        }

    def fit(
        self,
        track_errors: Sequence[float],
        raw_cone_radii: Sequence[float],
        horizons: Sequence[int] | None = None,
        target_coverage: float | None = None,
    ) -> dict[str, Any]:
        """Fits calibration scaling factors gamma on validation pairs (error, raw_radius).

        Mathematical Principle:
        Find multiplier gamma such that P(error <= gamma * raw_radius) = target_coverage.
        This corresponds directly to the p-th empirical quantile of (error / raw_radius).
        """
        p = target_coverage or self.target_coverage
        self.target_coverage = p

        errs = np.asarray(track_errors, dtype=float)
        rads = np.asarray(raw_cone_radii, dtype=float)
        valid = (rads > 1e-3) & (~np.isnan(errs)) & (~np.isnan(rads))

        if not np.any(valid) or len(errs[valid]) < 2:
            return {
                "global_multiplier": 1.0,
                "per_horizon_multipliers": self.per_horizon_multipliers,
            }

        ratios = errs[valid] / rads[valid]

        # Global empirical quantile
        gamma_global = float(np.percentile(ratios, p * 100.0))
        self.global_multiplier = round(max(0.5, min(5.0, gamma_global)), 4)

        # Per-horizon empirical quantiles if horizons provided
        if horizons is not None and len(horizons) == len(track_errors):
            hz_arr = np.asarray(horizons)[valid]
            for h in [6, 12, 24, 48, 72]:
                h_mask = hz_arr == h
                if np.sum(h_mask) >= 2:
                    gamma_h = float(np.percentile(ratios[h_mask], p * 100.0))
                    self.per_horizon_multipliers[f"{h}h"] = round(max(0.5, min(5.0, gamma_h)), 4)
                else:
                    self.per_horizon_multipliers[f"{h}h"] = self.global_multiplier

        return {
            "target_coverage": self.target_coverage,
            "global_multiplier": self.global_multiplier,
            "per_horizon_multipliers": self.per_horizon_multipliers,
        }

    def recalibrate_radii(
        self,
        raw_cone_radii: Sequence[float],
        horizon_hours: int | None = None,
        use_per_horizon: bool = True,
    ) -> list[float]:
        """Applies calibrated variance multiplier to raw cone radii."""
        mult = self.global_multiplier
        if use_per_horizon and horizon_hours is not None:
            mult = self.per_horizon_multipliers.get(f"{horizon_hours}h", self.global_multiplier)

        recalibrated = []
        for i, r in enumerate(raw_cone_radii):
            if i == 0:
                recalibrated.append(0.0)  # r(0) is strictly 0.0 km
            else:
                recalibrated.append(round(float(r * mult), 2))
        return recalibrated

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_coverage": self.target_coverage,
            "global_multiplier": self.global_multiplier,
            "per_horizon_multipliers": self.per_horizon_multipliers,
        }

    def from_dict(self, data: dict[str, Any]) -> None:
        self.target_coverage = float(data.get("target_coverage", 0.95))
        self.global_multiplier = float(data.get("global_multiplier", 1.0))
        self.per_horizon_multipliers = data.get(
            "per_horizon_multipliers", self.per_horizon_multipliers
        )


class ModelCalibrator:
    """Unified Calibrator coordinating Temperature Scalers and Cone Recalibration."""

    def __init__(self) -> None:
        self.detection_scaler = TemperatureScaler(initial_temp=1.0)
        self.stage_scaler = TemperatureScaler(initial_temp=1.0)
        self.intensity_scaler = TemperatureScaler(initial_temp=1.0)
        self.cone_recalibrator = VarianceRecalibrator(target_coverage=0.95)

    def save(self, filepath: str | Path) -> Path:
        """Persists all calibration parameters to JSON with git commit and config hash provenance."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        from ml.cyclone.train.track_experiment import get_git_commit_hash

        git_hash = get_git_commit_hash()
        config_p = Path("ml/cyclone/config/model.best.yaml")
        config_hash = "none"
        if config_p.is_file():
            import hashlib

            config_hash = hashlib.sha256(config_p.read_bytes()).hexdigest()[:16]

        data = {
            "metadata": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "git_commit": git_hash,
                "config_hash": config_hash,
            },
            "detection": self.detection_scaler.to_dict(),
            "stage": self.stage_scaler.to_dict(),
            "intensity_cls": self.intensity_scaler.to_dict(),
            "track_cone": self.cone_recalibrator.to_dict(),
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return path

    def load(self, filepath: str | Path) -> None:
        """Loads calibration parameters from JSON."""
        path = Path(filepath)
        if not path.is_file():
            return
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if "detection" in data:
            self.detection_scaler.from_dict(data["detection"])
        if "stage" in data:
            self.stage_scaler.from_dict(data["stage"])
        if "intensity_cls" in data:
            self.intensity_scaler.from_dict(data["intensity_cls"])
        if "track_cone" in data:
            self.cone_recalibrator.from_dict(data["track_cone"])


__all__ = [
    "TemperatureScaler",
    "VarianceRecalibrator",
    "ModelCalibrator",
]
