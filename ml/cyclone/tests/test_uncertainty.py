"""Unit tests for learned uncertainty cones, Gaussian NLL loss, and Monte Carlo dropout."""

import numpy as np
import pytest
import torch

from ml.cyclone.models.heads import TrackModel
from ml.cyclone.models.uncertainty import (
    monte_carlo_dropout_predict,
    predict_cone_radii,
)
from ml.cyclone.train.losses import GaussianNLLLoss


def test_predict_cone_radii_properties():
    """Asserts predict_cone_radii adheres to physical constraints: r(0)=0, monotonicity, and scaling."""
    # (5 horizons, 2 coordinates)
    log_vars = np.array(
        [
            [-2.0, -2.0],  # 6h
            [-1.5, -1.5],  # 12h
            [-1.0, -1.0],  # 24h
            [-0.5, -0.5],  # 48h
            [0.0, 0.0],  # 72h
        ]
    )

    radii_95 = predict_cone_radii(log_vars, current_lat=15.0, coverage_level=0.95)
    radii_68 = predict_cone_radii(log_vars, current_lat=15.0, coverage_level=0.68)

    # 1. Anchor check: t=0 is 0.0 km
    assert radii_95[0] == 0.0
    assert radii_68[0] == 0.0
    assert len(radii_95) == 6  # 0h + 5 horizons

    # 2. Monotonicity check
    for i in range(1, len(radii_95)):
        assert radii_95[i] >= radii_95[i - 1], f"Horizon {i} radius ({radii_95[i]}) not monotonic"

    # 3. Higher confidence level implies larger radius
    for i in range(1, len(radii_95)):
        assert (
            radii_95[i] >= radii_68[i]
        ), f"95% radius ({radii_95[i]}) should exceed 68% ({radii_68[i]})"

    # 4. Torch tensor input support
    t_log_vars = torch.tensor(log_vars, dtype=torch.float32)
    radii_from_tensor = predict_cone_radii(t_log_vars, current_lat=15.0)
    assert len(radii_from_tensor) == 6
    assert pytest.approx(radii_from_tensor[1], abs=1e-2) == radii_95[1]


def test_gaussian_nll_loss_mechanics():
    """Asserts GaussianNLLLoss behaves properly on exact vs noisy targets and respects horizon masks."""
    criterion = GaussianNLLLoss(min_log_var=-7.0, max_log_var=7.0)

    # Perfect prediction with log_var=0 (sigma=1)
    pred_mu = torch.zeros(2, 5, 2, dtype=torch.float32, requires_grad=True)
    pred_lv = torch.zeros(2, 5, 2, dtype=torch.float32, requires_grad=True)
    target = torch.zeros(2, 5, 2, dtype=torch.float32)
    masks = torch.ones(2, 5, dtype=torch.bool)

    loss = criterion(pred_mu, pred_lv, target, masks)
    # NLL for y=0, mu=0, log_var=0: 0.5 * (1 * 0 + 0) = 0.0 per coordinate -> 0.0 total
    assert pytest.approx(loss.item(), abs=1e-4) == 0.0

    # Gradient check
    loss.backward()
    assert pred_mu.grad is not None
    assert pred_lv.grad is not None

    # Masked horizons check
    masks_zero = torch.zeros(2, 5, dtype=torch.bool)
    loss_masked = criterion(pred_mu, pred_lv, target, masks_zero)
    assert loss_masked.item() == 0.0


def test_monte_carlo_dropout_uncertainty_decomposition():
    """Asserts MC-dropout runs K stochastic draws and decomposes epistemic & aleatoric variance."""
    model = TrackModel(env_dim=6, track_dim=7, num_horizons=5)

    dummy_env = torch.rand(1, 6, dtype=torch.float32)
    dummy_track = torch.rand(1, 8, 7, dtype=torch.float32)

    mc_res = monte_carlo_dropout_predict(
        model=model,
        env_vector=dummy_env,
        track_sequence=dummy_track,
        num_samples=10,
        coverage_level=0.95,
        current_lat=18.0,
    )

    assert "mean_deltas" in mc_res
    assert "epistemic_variance" in mc_res
    assert "aleatoric_variance" in mc_res
    assert "total_variance" in mc_res
    assert "cone_radii_km" in mc_res

    assert mc_res["mean_deltas"].shape == (5, 2)
    assert mc_res["epistemic_variance"].shape == (5, 2)
    assert mc_res["aleatoric_variance"].shape == (5, 2)
    assert mc_res["total_variance"].shape == (5, 2)

    # Total variance should equal epistemic + aleatoric
    expected_tot = mc_res["epistemic_variance"] + mc_res["aleatoric_variance"]
    np.testing.assert_allclose(mc_res["total_variance"], expected_tot, rtol=1e-4, atol=1e-5)

    # Cone radii anchored at 0.0 km with length 6
    assert len(mc_res["cone_radii_km"]) == 6
    assert mc_res["cone_radii_km"][0] == 0.0
    for r in mc_res["cone_radii_km"][1:]:
        assert r > 0.0
