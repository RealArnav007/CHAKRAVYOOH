"""Heteroscedastic aleatoric and epistemic uncertainty modeling for cyclone trajectory forecasting."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import torch
import torch.nn as nn

KM_PER_DEG_LAT = 111.195


# -----------------------------------------------------------------------------
# 1. Learned Uncertainty Cone Radius Derivation
# -----------------------------------------------------------------------------


def predict_cone_radii(
    log_vars: torch.Tensor | np.ndarray,
    current_lat: float = 15.0,
    coverage_level: float = 0.95,
) -> list[float]:
    """Converts predicted log-variances [log_var_lat, log_var_lon] into IMD-compatible cone radii in km.

    Mathematical Formulation:
    1. Per-axis spatial standard deviations:
       sigma_lat_km = sqrt(exp(log_var_lat)) * 111.195 km/deg
       sigma_lon_km = sqrt(exp(log_var_lon)) * 111.195 * cos(lat) km/deg
    2. Effective isotropic spatial dispersion:
       sigma_eff = sqrt((sigma_lat_km^2 + sigma_lon_km^2) / 2)
    3. 2D Gaussian quantile for specified coverage probability p:
       r(t) = sigma_eff * sqrt(-2 * ln(1 - p))  [for p=0.95, multiplier ~= 2.4477]
    4. Enforces r(0) = 0.0 km and non-decreasing monotonic growth.

    Args:
        log_vars: (H, 2) or (1, H, 2) tensor/array of [log_var_lat, log_var_lon].
        current_lat: Analysis latitude in degrees for spherical longitude scaling.
        coverage_level: Target cumulative coverage probability (default: 0.95 for 95% cone).

    Returns:
        List of float cone radii in km starting strictly with 0.0 km at analysis time t=0.
    """
    lv_arr = (
        log_vars.detach().cpu().numpy()
        if isinstance(log_vars, torch.Tensor)
        else np.asarray(log_vars)
    )
    if lv_arr.ndim == 3:
        lv_arr = lv_arr.squeeze(0)

    # Chi-squared 2D multiplier: sqrt(-2 * ln(1 - p))
    p = float(np.clip(coverage_level, 0.50, 0.999))
    quantile_multiplier = math.sqrt(-2.0 * math.log(1.0 - p))

    cos_lat = max(0.2, math.cos(math.radians(current_lat)))

    radii: list[float] = [0.0]  # Anchor r(0) = 0.0 km
    prev_r = 0.0

    for h_idx in range(len(lv_arr)):
        log_v_lat = float(np.clip(lv_arr[h_idx, 0], -8.0, 8.0))
        log_v_lon = float(np.clip(lv_arr[h_idx, 1], -8.0, 8.0))

        std_lat_km = math.sqrt(math.exp(log_v_lat)) * KM_PER_DEG_LAT
        std_lon_km = math.sqrt(math.exp(log_v_lon)) * KM_PER_DEG_LAT * cos_lat

        sigma_eff = math.sqrt((std_lat_km**2 + std_lon_km**2) / 2.0)
        raw_radius_km = sigma_eff * quantile_multiplier

        # Enforce physical minimum threshold and monotonicity over forecast horizon
        r_km = max(prev_r + 5.0, raw_radius_km) if h_idx > 0 else raw_radius_km
        r_km = round(float(np.clip(r_km, 10.0, 800.0)), 2)
        radii.append(r_km)
        prev_r = r_km

    return radii


# -----------------------------------------------------------------------------
# 2. Monte Carlo Dropout for Epistemic Uncertainty Estimation
# -----------------------------------------------------------------------------


def monte_carlo_dropout_predict(
    model: nn.Module,
    env_vector: torch.Tensor,
    track_sequence: torch.Tensor,
    seq_lengths: torch.Tensor | None = None,
    num_samples: int = 20,
    coverage_level: float = 0.95,
    current_lat: float = 15.0,
) -> dict[str, Any]:
    """Draws K stochastic forward passes with dropout enabled to quantify epistemic and aleatoric uncertainty.

    Total Uncertainty Decomposition:
    sigma_total^2 = sigma_epistemic^2 (model uncertainty) + sigma_aleatoric^2 (data noise)

    Args:
        model: TrackModel or Multi-modal Neural Network.
        env_vector: Atmospheric environmental tensor (1, 6).
        track_sequence: Historical sequence tensor (1, N, 7).
        seq_lengths: Optional sequence length.
        num_samples: Number of Monte Carlo stochastic passes K (default: 20).
        coverage_level: Target cone coverage level (default: 0.95).
        current_lat: Analysis latitude in degrees.

    Returns:
        Dict containing predictive mean deltas, epistemic variances, aleatoric variances, and total cone radii.
    """
    # Enable dropout during inference
    model.train()

    mc_deltas: list[torch.Tensor] = []
    mc_log_vars: list[torch.Tensor] = []

    with torch.no_grad():
        for _ in range(num_samples):
            out = model(
                env_vector=env_vector, track_sequence=track_sequence, seq_lengths=seq_lengths
            )
            mc_deltas.append(out["deltas"])  # (1, H, 2)
            mc_log_vars.append(out["log_vars"])  # (1, H, 2)

    # Stack draws: (K, 1, H, 2)
    deltas_stack = torch.stack(mc_deltas, dim=0).squeeze(1)  # (K, H, 2)
    log_vars_stack = torch.stack(mc_log_vars, dim=0).squeeze(1)  # (K, H, 2)

    # 1. Predictive Mean: E[y]
    mean_deltas = torch.mean(deltas_stack, dim=0)  # (H, 2)

    # 2. Epistemic Uncertainty: Var_K[E[y]]
    epistemic_var = torch.var(deltas_stack, dim=0, unbiased=True)  # (H, 2)

    # 3. Aleatoric Uncertainty: E_K[exp(log_var)]
    aleatoric_var = torch.mean(torch.exp(torch.clamp(log_vars_stack, -8.0, 8.0)), dim=0)  # (H, 2)

    # 4. Total Predictive Variance
    total_var = epistemic_var + aleatoric_var  # (H, 2)
    total_log_var = torch.log(torch.clamp(total_var, min=1e-6))

    # Derive calibrated cone radii
    cone_radii = predict_cone_radii(
        log_vars=total_log_var,
        current_lat=current_lat,
        coverage_level=coverage_level,
    )

    model.eval()

    return {
        "mean_deltas": mean_deltas.cpu().numpy(),
        "epistemic_variance": epistemic_var.cpu().numpy(),
        "aleatoric_variance": aleatoric_var.cpu().numpy(),
        "total_variance": total_var.cpu().numpy(),
        "cone_radii_km": cone_radii,
    }


__all__ = [
    "predict_cone_radii",
    "monte_carlo_dropout_predict",
    "KM_PER_DEG_LAT",
]
