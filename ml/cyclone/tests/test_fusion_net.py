"""Unit tests for multi-modal FusionNet architecture and learnable MultiTaskLoss."""

import torch

from ml.cyclone.models.fusion_net import FusionNet
from ml.cyclone.train.losses import MultiTaskLoss


def test_fusion_net_mixed_batch_forward_and_head_shapes():
    """Asserts FusionNet forward pass handles a mixed batch (some images present, some missing)."""
    batch_size = 4
    model = FusionNet(
        image_backbone="efficientnet_b0",
        image_pretrained=False,
        image_dim=512,
        env_in_dim=6,
        env_dim=64,
        track_in_dim=7,
        track_hidden_dim=128,
        fusion_hidden_dim=512,
        shared_dim=256,
        num_stages=6,
        num_imd_levels=7,
        num_track_horizons=5,
    )

    # Mixed batch: 2 valid images, 2 missing images
    dummy_imgs = torch.rand(batch_size, 1, 224, 224, dtype=torch.float32)
    image_available = torch.tensor([1.0, 0.0, 1.0, 0.0], dtype=torch.float32)
    dummy_env = torch.rand(batch_size, 6, dtype=torch.float32)
    dummy_track = torch.rand(batch_size, 8, 7, dtype=torch.float32)

    out = model(
        img=dummy_imgs,
        env_vector=dummy_env,
        track_sequence=dummy_track,
        image_available=image_available,
    )

    # 1. Check shared trunk embedding shape
    assert "shared_embedding" in out
    assert out["shared_embedding"].shape == (batch_size, 256)

    # 2. Check detection head shapes
    assert out["detection_logits"].shape == (batch_size, 1)
    assert out["detection_probs"].shape == (batch_size, 1)
    assert out["detected"].shape == (batch_size, 1)

    # 3. Check stage head shapes
    assert out["stage_logits"].shape == (batch_size, 6)
    assert out["stage_probs"].shape == (batch_size, 6)
    assert out["predicted_stage_idx"].shape == (batch_size,)

    # 4. Check intensity head shapes
    assert out["intensity"]["wind_kt"].shape == (batch_size, 1)
    assert out["intensity"]["pres_mb"].shape == (batch_size, 1)
    assert out["intensity"]["imd_logits"].shape == (batch_size, 7)
    assert out["intensity"]["imd_probs"].shape == (batch_size, 7)

    # 5. Check track head shapes
    assert out["track"]["deltas"].shape == (batch_size, 5, 2)
    assert out["track"]["log_vars"].shape == (batch_size, 5, 2)


def test_multitask_loss_learnable_weights_and_backward_step():
    """Asserts MultiTaskLoss computes finite loss and updates learnable homoscedastic task weights."""
    model = FusionNet(
        image_backbone="efficientnet_b0",
        image_pretrained=False,
        shared_dim=256,
        num_track_horizons=5,
    )
    criterion = MultiTaskLoss()
    optimizer = torch.optim.AdamW(list(model.parameters()) + list(criterion.parameters()), lr=1e-3)

    batch_size = 4
    dummy_imgs = torch.rand(batch_size, 1, 224, 224, dtype=torch.float32)
    image_available = torch.tensor([1.0, 1.0, 0.0, 0.0], dtype=torch.float32)
    dummy_env = torch.rand(batch_size, 6, dtype=torch.float32)
    dummy_track = torch.rand(batch_size, 8, 7, dtype=torch.float32)

    targets = {
        "detected": torch.tensor([1.0, 1.0, 0.0, 1.0], dtype=torch.float32),
        "stage_idx": torch.tensor([1, 2, 0, 3], dtype=torch.long),
        "wind_kt": torch.tensor([45.0, 65.0, 25.0, 80.0], dtype=torch.float32),
        "pres_mb": torch.tensor([990.0, 970.0, 1005.0, 955.0], dtype=torch.float32),
        "imd_level_idx": torch.tensor([2, 3, 0, 4], dtype=torch.long),
        "future_deltas": torch.rand(batch_size, 5, 2, dtype=torch.float32),
        "horizon_masks": torch.ones(batch_size, 5, dtype=torch.bool),
    }

    optimizer.zero_grad()
    predictions = model(
        img=dummy_imgs,
        env_vector=dummy_env,
        track_sequence=dummy_track,
        image_available=image_available,
    )

    loss_dict = criterion(predictions, targets)

    assert "loss" in loss_dict
    assert "raw_losses" in loss_dict
    assert "weighted_losses" in loss_dict
    assert "task_variances" in loss_dict

    total_loss = loss_dict["loss"]
    assert torch.isfinite(total_loss)
    assert total_loss.item() > 0.0

    # Verify backward pass computes gradients for trunk and task log_vars
    total_loss.backward()
    optimizer.step()

    for task_name, param in criterion.log_vars.items():
        assert param.grad is not None, f"Gradient missing for task {task_name}"

    # Verify task weights retrieval
    weights = criterion.get_task_weights()
    assert "detection" in weights
    assert "track" in weights
    for w in weights.values():
        assert w > 0.0


def test_fusion_net_from_config():
    """Asserts FusionNet can be instantiated from default config object."""
    model = FusionNet.from_config()
    assert isinstance(model, FusionNet)
    assert model.shared_dim == 256
    assert model.num_track_horizons == 5
