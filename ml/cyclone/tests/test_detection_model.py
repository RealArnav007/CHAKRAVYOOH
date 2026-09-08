"""Unit tests for ImageBranch, DetectionModel, and negative sample generator."""

import torch

from ml.cyclone.datasets.torch_dataset import generate_negative_samples
from ml.cyclone.models.heads import DetectionModel
from ml.cyclone.models.image_branch import ImageBranch


def test_image_branch_forward_and_embedding_dim():
    """Asserts ImageBranch adapts single-channel IR inputs to 512-d feature embeddings."""
    branch = ImageBranch(backbone_name="efficientnet_b0", pretrained=False, embedding_dim=512)
    dummy_img = torch.rand(2, 1, 224, 224, dtype=torch.float32)

    emb = branch(dummy_img)
    assert emb.shape == (2, 512)
    assert emb.dtype == torch.float32

    # Test missing image fallback
    missing_avail = torch.tensor([1.0, 0.0])
    emb_masked = branch(dummy_img, image_available=missing_avail)
    assert emb_masked.shape == (2, 512)


def test_detection_head_and_model_forward():
    """Asserts DetectionHead and standalone DetectionModel emit proper logits and probabilities."""
    model = DetectionModel(backbone_name="efficientnet_b0", pretrained=False, embedding_dim=512)
    dummy_img = torch.rand(3, 1, 224, 224, dtype=torch.float32)

    out = model(dummy_img)
    assert "logits" in out
    assert "probs" in out
    assert "detected" in out
    assert "embedding" in out

    assert out["logits"].shape == (3, 1)
    assert out["probs"].shape == (3, 1)
    assert out["embedding"].shape == (3, 512)
    assert torch.all(out["probs"] >= 0.0) and torch.all(out["probs"] <= 1.0)


def test_generate_negative_samples():
    """Asserts synthetic negative sample generator produces non-cyclone ocean background patches."""
    neg_samples = generate_negative_samples(num_samples=10, seed=123)
    assert len(neg_samples) == 10

    for s in neg_samples:
        assert s["wind_kt"] < 15.0
        assert s["pres_mb"] >= 1010.0
        assert s["image_tensor"] is not None
        assert s["image_tensor"].shape == (1, 224, 224)


def test_detection_training_step():
    """Asserts backpropagation and optimizer step on DetectionModel with BCE loss."""
    model = DetectionModel(backbone_name="efficientnet_b0", pretrained=False, embedding_dim=512)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
    criterion = torch.nn.BCEWithLogitsLoss()

    dummy_img = torch.rand(4, 1, 224, 224, dtype=torch.float32)
    targets = torch.tensor([[1.0], [0.0], [1.0], [0.0]], dtype=torch.float32)

    optimizer.zero_grad()
    out = model(dummy_img)
    loss = criterion(out["logits"], targets)
    loss.backward()
    optimizer.step()

    assert not torch.isnan(loss)
    assert loss.item() > 0.0
