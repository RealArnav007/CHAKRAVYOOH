"""Loss functions for cyclone trajectory forecasting, intensity regression, and multi-task learning."""

from __future__ import annotations

import math

import torch
import torch.nn as nn

from ml.cyclone.preprocess.geo import EARTH_RADIUS_KM


class GaussianNLLLoss(nn.Module):
    """Heteroscedastic Gaussian Negative Log-Likelihood Loss for probabilistic trajectory forecasting.

    Formula:
        NLL(y, mu, log_var) = 0.5 * (exp(-log_var) * (y - mu)^2 + log_var)

    Features:
    - End-of-storm horizon masking (only valid future horizons contribute).
    - Clamped log-variances in [-7.0, 7.0] to prevent gradient instability or infinite penalties.
    - Intensity sample weighting to prioritize high-risk severe cyclones.
    """

    def __init__(
        self,
        min_log_var: float = -7.0,
        max_log_var: float = 7.0,
        eps: float = 1e-6,
    ) -> None:
        super().__init__()
        self.min_log_var = min_log_var
        self.max_log_var = max_log_var
        self.eps = eps

    def forward(
        self,
        pred_mu: torch.Tensor,  # (B, H, 2)
        pred_log_var: torch.Tensor,  # (B, H, 2)
        target: torch.Tensor,  # (B, H, 2)
        horizon_masks: torch.Tensor,  # (B, H) bool
        sample_weights: torch.Tensor | None = None,  # (B,)
    ) -> torch.Tensor:
        """Computes masked Gaussian NLL loss."""
        batch_size, num_horizons, _ = pred_mu.shape

        # Clamp log-variances for numerical safety
        clamped_log_var = torch.clamp(pred_log_var, min=self.min_log_var, max=self.max_log_var)
        inv_var = torch.exp(-clamped_log_var)

        # Squared residual per coordinate
        sq_err = (target - pred_mu) ** 2  # (B, H, 2)

        # Component NLL
        nll_per_coord = 0.5 * (inv_var * sq_err + clamped_log_var)
        nll_per_step = torch.sum(nll_per_coord, dim=-1)  # (B, H)

        # Apply horizon mask
        valid_mask = horizon_masks.float()
        masked_nll = nll_per_step * valid_mask

        if sample_weights is not None:
            w = sample_weights.unsqueeze(1).expand(-1, num_horizons)
            masked_nll = masked_nll * w
            total_valid = torch.sum(valid_mask * w)
        else:
            total_valid = torch.sum(valid_mask)

        loss = torch.sum(masked_nll) / torch.clamp(total_valid, min=1.0)
        return loss


class HaversineMetricLoss(nn.Module):
    """Differentiable Great-Circle (Haversine) metric loss on spherical coordinates."""

    def __init__(self, eps: float = 1e-8) -> None:
        super().__init__()
        self.eps = eps

    def forward(
        self,
        pred_deltas: torch.Tensor,  # (B, H, 2) [dlat, dlon] in degrees
        target_deltas: torch.Tensor,  # (B, H, 2) [dlat, dlon] in degrees
        current_coords: torch.Tensor,  # (B, 2) [lat0, lon0] in degrees
        horizon_masks: torch.Tensor,  # (B, H) bool
        sample_weights: torch.Tensor | None = None,  # (B,)
    ) -> torch.Tensor:
        """Computes Great-Circle distance in kilometers with horizon masking."""
        batch_size, num_horizons, _ = pred_deltas.shape

        lat0 = current_coords[:, 0].unsqueeze(1).expand(-1, num_horizons)
        lon0 = current_coords[:, 1].unsqueeze(1).expand(-1, num_horizons)

        deg_to_rad = math.pi / 180.0
        p_lat_rad = (lat0 + pred_deltas[..., 0]) * deg_to_rad
        p_lon_rad = (lon0 + pred_deltas[..., 1]) * deg_to_rad

        t_lat_rad = (lat0 + target_deltas[..., 0]) * deg_to_rad
        t_lon_rad = (lon0 + target_deltas[..., 1]) * deg_to_rad

        dlat_rad = p_lat_rad - t_lat_rad
        dlon_rad = p_lon_rad - t_lon_rad

        sin_half_dlat = torch.sin(dlat_rad / 2.0)
        sin_half_dlon = torch.sin(dlon_rad / 2.0)

        a = (sin_half_dlat**2) + torch.cos(p_lat_rad) * torch.cos(t_lat_rad) * (sin_half_dlon**2)
        a = torch.clamp(a, min=0.0, max=1.0)

        safe_a = torch.clamp(a, min=1e-8, max=1.0 - 1e-7)
        c = torch.where(a > 1e-8, 2.0 * torch.asin(torch.sqrt(safe_a)), torch.zeros_like(a))

        dist_km = EARTH_RADIUS_KM * c

        valid_mask = horizon_masks.float()
        masked_dist = dist_km * valid_mask

        if sample_weights is not None:
            w = sample_weights.unsqueeze(1).expand(-1, num_horizons)
            masked_dist = masked_dist * w
            total_valid = torch.sum(valid_mask * w)
        else:
            total_valid = torch.sum(valid_mask)

        loss = torch.sum(masked_dist) / torch.clamp(total_valid, min=1.0)
        return loss


class MultiTaskLoss(nn.Module):
    """Multi-task loss with learnable homoscedastic uncertainty weighting (Kendall & Gal 2018).

    Mathematical Formulation:
    For regression tasks (intensity_reg, track):
        L_task = 0.5 * exp(-s_i) * L_raw + 0.5 * s_i
    For classification tasks (detection, stage, intensity_cls):
        L_task = exp(-s_i) * L_raw + 0.5 * s_i

    where s_i = log(sigma_i^2) is a learnable homoscedastic task variance parameter.
    As s_i increases, the penalty for raw error decreases while the regularizer (0.5 * s_i) prevents s_i -> infinity.
    """

    def __init__(
        self,
        class_weights: Dict[str, torch.Tensor] | None = None,
        init_log_vars: Dict[str, float] | None = None,
        huber_beta: float = 5.0,
        min_log_var: float = -4.0,
        max_log_var: float = 6.0,
    ) -> None:
        super().__init__()
        self.min_log_var = min_log_var
        self.max_log_var = max_log_var

        # Learnable log-variance parameters s_i = log(sigma_i^2)
        inits = init_log_vars or {}
        self.log_vars = nn.ParameterDict(
            {
                "detection": nn.Parameter(torch.tensor(float(inits.get("detection", 0.0)))),
                "stage": nn.Parameter(torch.tensor(float(inits.get("stage", 0.0)))),
                "intensity_reg": nn.Parameter(torch.tensor(float(inits.get("intensity_reg", 0.0)))),
                "intensity_cls": nn.Parameter(torch.tensor(float(inits.get("intensity_cls", 0.0)))),
                "track": nn.Parameter(torch.tensor(float(inits.get("track", 0.0)))),
            }
        )

        # Task loss functions
        cw = class_weights or {}
        self.bce_loss = nn.BCEWithLogitsLoss(pos_weight=cw.get("detection"))
        self.stage_ce = nn.CrossEntropyLoss(weight=cw.get("stage"))
        self.imd_ce = nn.CrossEntropyLoss(weight=cw.get("intensity_cls"))
        self.huber_loss = nn.SmoothL1Loss(beta=huber_beta, reduction="mean")
        self.track_nll = GaussianNLLLoss(min_log_var=-7.0, max_log_var=7.0)

    def forward(
        self,
        predictions: Dict[str, Any],
        targets: Dict[str, Any],
        sample_weights: torch.Tensor | None = None,
    ) -> Dict[str, Any]:
        """Computes homoscedastic uncertainty-weighted multi-task loss.

        Args:
            predictions: Output dictionary from FusionNet containing:
                - 'detection_logits' (B, 1)
                - 'stage_logits' (B, 6)
                - 'intensity': {'wind_kt' (B, 1), 'pres_mb' (B, 1), 'imd_logits' (B, 7)}
                - 'track': {'deltas' (B, H, 2), 'log_vars' (B, H, 2)}
            targets: Dictionary containing ground truth targets:
                - 'detected' (B,) or (B, 1)
                - 'stage_idx' (B,)
                - 'wind_kt' (B,) or (B, 1)
                - 'pres_mb' (B,) or (B, 1) [optional]
                - 'imd_level_idx' (B,)
                - 'future_deltas' (B, H, 2)
                - 'horizon_masks' (B, H)
            sample_weights: Optional sample intensity weight tensor (B,).

        Returns:
            Dict containing 'loss' (total scalar tensor), 'task_losses' (raw floats),
            'weighted_losses' (weighted floats), and 'task_variances' (sigma^2 floats).
        """
        raw_losses: Dict[str, torch.Tensor] = {}
        weighted_losses: Dict[str, torch.Tensor] = {}
        task_variances: Dict[str, float] = {}

        # 1. Detection Loss (BCE)
        det_logits = predictions.get("detection_logits")
        if det_logits is not None and "detected" in targets:
            det_target = targets["detected"].view(-1, 1).float()
            raw_det = self.bce_loss(det_logits, det_target)
            s_det = torch.clamp(self.log_vars["detection"], self.min_log_var, self.max_log_var)
            w_det = torch.exp(-s_det) * raw_det + 0.5 * s_det
            raw_losses["detection"] = raw_det
            weighted_losses["detection"] = w_det
            task_variances["detection"] = round(float(torch.exp(s_det).item()), 4)

        # 2. Lifecycle Stage Loss (Cross-Entropy)
        stage_logits = predictions.get("stage_logits")
        if stage_logits is not None and "stage_idx" in targets:
            stage_target = targets["stage_idx"].view(-1).long()
            raw_stage = self.stage_ce(stage_logits, stage_target)
            s_stage = torch.clamp(self.log_vars["stage"], self.min_log_var, self.max_log_var)
            w_stage = torch.exp(-s_stage) * raw_stage + 0.5 * s_stage
            raw_losses["stage"] = raw_stage
            weighted_losses["stage"] = w_stage
            task_variances["stage"] = round(float(torch.exp(s_stage).item()), 4)

        # 3. Intensity Regression Loss (Huber)
        int_out = predictions.get("intensity", {})
        wind_pred = int_out.get("wind_kt")
        if wind_pred is not None and "wind_kt" in targets:
            wind_target = targets["wind_kt"].view(-1, 1).float()
            valid_wind = ~torch.isnan(wind_target)
            if torch.any(valid_wind):
                raw_wind = self.huber_loss(wind_pred[valid_wind], wind_target[valid_wind])
            else:
                raw_wind = torch.tensor(0.0, device=wind_pred.device)

            s_ireg = torch.clamp(self.log_vars["intensity_reg"], self.min_log_var, self.max_log_var)
            w_ireg = 0.5 * torch.exp(-s_ireg) * raw_wind + 0.5 * s_ireg
            raw_losses["intensity_reg"] = raw_wind
            weighted_losses["intensity_reg"] = w_ireg
            task_variances["intensity_reg"] = round(float(torch.exp(s_ireg).item()), 4)

        # 4. Intensity Classification Loss (IMD CE)
        imd_logits = int_out.get("imd_logits")
        if imd_logits is not None and "imd_level_idx" in targets:
            imd_target = targets["imd_level_idx"].view(-1).long()
            raw_imd = self.imd_ce(imd_logits, imd_target)
            s_icls = torch.clamp(self.log_vars["intensity_cls"], self.min_log_var, self.max_log_var)
            w_icls = torch.exp(-s_icls) * raw_imd + 0.5 * s_icls
            raw_losses["intensity_cls"] = raw_imd
            weighted_losses["intensity_cls"] = w_icls
            task_variances["intensity_cls"] = round(float(torch.exp(s_icls).item()), 4)

        # 5. Track Trajectory Loss (Gaussian NLL)
        track_out = predictions.get("track", {})
        t_deltas = track_out.get("deltas")
        t_logvars = track_out.get("log_vars")
        if t_deltas is not None and t_logvars is not None and "future_deltas" in targets:
            fut_target = targets["future_deltas"].float()
            h_masks = targets["horizon_masks"].bool()
            raw_track = self.track_nll(
                pred_mu=t_deltas,
                pred_log_var=t_logvars,
                target=fut_target,
                horizon_masks=h_masks,
                sample_weights=sample_weights,
            )
            s_track = torch.clamp(self.log_vars["track"], self.min_log_var, self.max_log_var)
            w_track = 0.5 * torch.exp(-s_track) * raw_track + 0.5 * s_track
            raw_losses["track"] = raw_track
            weighted_losses["track"] = w_track
            task_variances["track"] = round(float(torch.exp(s_track).item()), 4)

        # Total multi-task loss
        total_loss = sum(weighted_losses.values()) if weighted_losses else torch.tensor(0.0)

        return {
            "loss": total_loss,
            "raw_losses": {k: float(v.item()) for k, v in raw_losses.items()},
            "weighted_losses": {k: float(v.item()) for k, v in weighted_losses.items()},
            "task_variances": task_variances,
        }

    def get_task_weights(self) -> Dict[str, float]:
        """Returns the current scaling factor exp(-s_i) for each task."""
        return {
            k: round(
                float(torch.exp(-torch.clamp(v, self.min_log_var, self.max_log_var)).item()), 4
            )
            for k, v in self.log_vars.items()
        }


__all__ = [
    "GaussianNLLLoss",
    "HaversineMetricLoss",
    "MultiTaskLoss",
]
