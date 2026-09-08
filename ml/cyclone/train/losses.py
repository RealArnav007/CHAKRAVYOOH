"""Loss functions for cyclone trajectory forecasting, intensity regression, and multi-task learning."""

from __future__ import annotations

import math
from typing import Optional
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
        pred_mu: torch.Tensor,              # (B, H, 2)
        pred_log_var: torch.Tensor,         # (B, H, 2)
        target: torch.Tensor,               # (B, H, 2)
        horizon_masks: torch.Tensor,        # (B, H) bool
        sample_weights: Optional[torch.Tensor] = None,  # (B,)
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
        pred_deltas: torch.Tensor,       # (B, H, 2) [dlat, dlon] in degrees
        target_deltas: torch.Tensor,     # (B, H, 2) [dlat, dlon] in degrees
        current_coords: torch.Tensor,    # (B, 2) [lat0, lon0] in degrees
        horizon_masks: torch.Tensor,     # (B, H) bool
        sample_weights: Optional[torch.Tensor] = None,  # (B,)
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

        a = (sin_half_dlat ** 2) + torch.cos(p_lat_rad) * torch.cos(t_lat_rad) * (sin_half_dlon ** 2)
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


__all__ = [
    "GaussianNLLLoss",
    "HaversineMetricLoss",
]
