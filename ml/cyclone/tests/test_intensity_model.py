"""Unit tests for Automated-Dvorak IntensityModel and multi-task loss computation."""

import numpy as np
import torch

from ml.cyclone.models.heads import IntensityModel
from ml.cyclone.preprocess.scales import wind_kt_to_imd_level
from ml.cyclone.schema.models import IntensityLevelEnum


def test_intensity_model_forward_shapes():
    """Asserts IntensityModel outputs continuous wind/pressure and 7-class IMD distribution."""
    model = IntensityModel(backbone_name="efficientnet_b0", pretrained=False, embedding_dim=512)
    dummy_img = torch.rand(3, 1, 224, 224, dtype=torch.float32)

    out = model(dummy_img)

    assert "wind_kt" in out
    assert "pres_mb" in out
    assert "imd_logits" in out
    assert "imd_probs" in out
    assert "embedding" in out

    assert out["wind_kt"].shape == (3, 1)
    assert out["pres_mb"].shape == (3, 1)
    assert out["imd_logits"].shape == (3, 7)
    assert out["imd_probs"].shape == (3, 7)
    assert out["embedding"].shape == (3, 512)

    # Probabilities sum to 1.0
    prob_sums = out["imd_probs"].sum(dim=-1).detach().numpy()
    np.testing.assert_allclose(prob_sums, 1.0, atol=1e-5)


def test_intensity_model_multi_task_loss_step():
    """Asserts multi-task Huber + Cross-Entropy training step executes cleanly."""
    model = IntensityModel(backbone_name="efficientnet_b0", pretrained=False, embedding_dim=512)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
    huber_fn = torch.nn.SmoothL1Loss(beta=2.0)
    ce_fn = torch.nn.CrossEntropyLoss()

    dummy_img = torch.rand(4, 1, 224, 224, dtype=torch.float32)
    target_w = torch.tensor([[35.0], [65.0], [90.0], [25.0]], dtype=torch.float32)
    target_imd = torch.tensor([2, 4, 5, 0], dtype=torch.long)

    optimizer.zero_grad()
    out = model(dummy_img)
    loss_reg = huber_fn(out["wind_kt"], target_w)
    loss_cls = ce_fn(out["imd_logits"], target_imd)
    total_loss = loss_reg + 0.5 * loss_cls

    total_loss.backward()
    optimizer.step()

    assert not torch.isnan(total_loss)
    assert total_loss.item() > 0.0


def test_scale_derivation_from_regressed_wind():
    """Asserts regressed continuous winds properly map to IMD categories via scales.py."""
    test_winds = [20.0, 30.0, 40.0, 55.0, 75.0, 100.0, 130.0]
    expected_levels = [
        IntensityLevelEnum.DEPRESSION,
        IntensityLevelEnum.DEEP_DEPRESSION,
        IntensityLevelEnum.CYCLONIC_STORM,
        IntensityLevelEnum.SEVERE_CYCLONIC_STORM,
        IntensityLevelEnum.VERY_SEVERE_CYCLONIC_STORM,
        IntensityLevelEnum.EXTREMELY_SEVERE_CYCLONIC_STORM,
        IntensityLevelEnum.SUPER_CYCLONIC_STORM,
    ]

    for w, exp in zip(test_winds, expected_levels):
        res = wind_kt_to_imd_level(w)
        assert res == exp
