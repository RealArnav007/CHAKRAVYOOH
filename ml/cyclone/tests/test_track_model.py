"""Unit tests for learned TrackHead, TrackModel, and differentiable Haversine loss."""

import pytest
import torch

from ml.cyclone.models.heads import TrackHead, TrackModel
from ml.cyclone.train.train_track import haversine_loss


def test_track_head_mlp_and_gru_decoders():
    """Asserts TrackHead decodes (B, H, 2) displacements and uncertainty using both MLP and GRU modes."""
    # 1. MLP Decoder
    head_mlp = TrackHead(embedding_dim=192, num_horizons=5, decoder_type="mlp")
    dummy_emb = torch.rand(3, 192, dtype=torch.float32)

    deltas_mlp, log_vars_mlp = head_mlp(dummy_emb)
    assert deltas_mlp.shape == (3, 5, 2)
    assert log_vars_mlp.shape == (3, 5, 2)

    # 2. GRU Decoder
    head_gru = TrackHead(embedding_dim=192, num_horizons=5, decoder_type="gru")
    deltas_gru, log_vars_gru = head_gru(dummy_emb)
    assert deltas_gru.shape == (3, 5, 2)
    assert log_vars_gru.shape == (3, 5, 2)

    # 3. deltas_to_path conversion helper
    sample_deltas = torch.tensor([[0.5, 0.2], [1.0, 0.5], [2.0, 1.0], [3.5, 2.0], [5.0, 3.5]])
    path = TrackHead.deltas_to_path(current_lat=15.0, current_lon=85.0, deltas=sample_deltas)

    assert len(path) == 6  # t=0 plus 5 horizons
    assert path[0]["t_plus_h"] == 0
    assert path[0]["lat"] == 15.0 and path[0]["lon"] == 85.0
    assert path[1]["t_plus_h"] == 6
    assert path[1]["lat"] == 15.5 and path[1]["lon"] == 85.2


def test_differentiable_haversine_loss_exact_and_masked():
    """Asserts haversine_loss returns 0 for zero displacement error and handles horizon masking."""
    # Case 1: Exact match (loss = 0.0)
    pred_deltas = torch.zeros(2, 5, 2, dtype=torch.float32, requires_grad=True)
    target_deltas = torch.zeros(2, 5, 2, dtype=torch.float32)
    coords = torch.tensor([[10.0, 80.0], [15.0, 85.0]], dtype=torch.float32)
    masks = torch.ones(2, 5, dtype=torch.bool)

    loss_zero = haversine_loss(pred_deltas, target_deltas, coords, masks)
    assert pytest.approx(loss_zero.item(), abs=1e-4) == 0.0

    # Gradient flow check
    loss_zero.backward()
    assert pred_deltas.grad is not None

    # Case 2: 1-degree latitude displacement (~111.19 km)
    pred_shifted = torch.zeros(1, 1, 2, dtype=torch.float32)
    pred_shifted[0, 0, 0] = 1.0  # +1 degree lat
    target_orig = torch.zeros(1, 1, 2, dtype=torch.float32)
    coords_eq = torch.tensor([[0.0, 0.0]], dtype=torch.float32)
    masks_single = torch.ones(1, 1, dtype=torch.bool)

    loss_dist = haversine_loss(pred_shifted, target_orig, coords_eq, masks_single)
    assert 111.0 <= loss_dist.item() <= 112.0

    # Case 3: Masked horizon (should not contribute to loss)
    masks_off = torch.zeros(1, 1, dtype=torch.bool)
    loss_masked = haversine_loss(pred_shifted, target_orig, coords_eq, masks_off)
    assert loss_masked.item() == 0.0


def test_track_model_forward_and_training_step():
    """Asserts TrackModel forward pass and end-to-end training gradient step."""
    model = TrackModel(env_dim=6, track_dim=7, num_horizons=5)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)

    dummy_env = torch.rand(4, 6, dtype=torch.float32)
    dummy_track = torch.rand(4, 8, 7, dtype=torch.float32)
    dummy_target_deltas = torch.rand(4, 5, 2, dtype=torch.float32)
    dummy_coords = torch.tensor(
        [[12.0, 82.0], [14.0, 84.0], [16.0, 86.0], [18.0, 88.0]], dtype=torch.float32
    )
    dummy_masks = torch.tensor(
        [
            [True, True, True, True, True],
            [True, True, True, False, False],
            [True, True, False, False, False],
            [True, False, False, False, False],
        ],
        dtype=torch.bool,
    )

    optimizer.zero_grad()
    out = model(env_vector=dummy_env, track_sequence=dummy_track)
    assert out["deltas"].shape == (4, 5, 2)
    assert out["log_vars"].shape == (4, 5, 2)

    loss = haversine_loss(out["deltas"], dummy_target_deltas, dummy_coords, dummy_masks)
    loss.backward()
    optimizer.step()

    assert not torch.isnan(loss)
    assert loss.item() > 0.0
