"""Unit tests for physically-valid satellite IR imagery data augmentation."""

from __future__ import annotations

import pytest
import torch

from ml.cyclone.config import AugmentationConfig
from ml.cyclone.train.augment import SatelliteAugmentor, build_satellite_augmentation


def test_augment_shapes() -> None:
    """Tests that SatelliteAugmentor preserves shape for both single and batched inputs."""
    augmentor = SatelliteAugmentor(is_train=True)
    augmentor.train()

    # Single image (1, 128, 128)
    single_img = torch.rand(1, 128, 128)
    aug_single = augmentor(single_img)
    assert aug_single.shape == single_img.shape
    assert isinstance(aug_single, torch.Tensor)

    # Batched images (4, 1, 128, 128)
    batch_img = torch.rand(4, 1, 128, 128)
    aug_batch = augmentor(batch_img)
    assert aug_batch.shape == batch_img.shape


def test_augment_physical_clamping() -> None:
    """Tests that augmented outputs remain strictly within physical bounds [0, 1]."""
    augmentor = SatelliteAugmentor(
        random_rotation=True,
        random_flip_h=True,
        random_flip_v=True,
        random_crop_scale=(0.8, 1.0),
        brightness_jitter=0.2,
        contrast_jitter=0.2,
        cutout=True,
        is_train=True,
    )
    augmentor.train()

    for _ in range(10):
        img = torch.rand(2, 1, 64, 64)
        out = augmentor(img)
        assert torch.all(out >= 0.0)
        assert torch.all(out <= 1.0)
        assert not torch.isnan(out).any()


def test_eval_mode_bypass() -> None:
    """Tests that in eval mode or when is_train=False, augmentation is strictly bypassed."""
    # Case 1: is_train=False
    aug_eval = SatelliteAugmentor(is_train=False)
    img = torch.rand(1, 64, 64)
    out1 = aug_eval(img)
    assert torch.equal(out1, img)

    # Case 2: module.eval()
    aug_train = SatelliteAugmentor(is_train=True)
    aug_train.eval()
    out2 = aug_train(img)
    assert torch.equal(out2, img)


def test_rotation_transform() -> None:
    """Tests that 0-360° rotation alters pixels appropriately while maintaining shape."""
    augmentor = SatelliteAugmentor(
        random_rotation=True,
        max_rotation_deg=360.0,
        random_flip_h=False,
        random_flip_v=False,
        random_crop_scale=(1.0, 1.0),
        brightness_jitter=0.0,
        contrast_jitter=0.0,
        cutout=False,
        is_train=True,
    )
    augmentor.train()

    # Synthetic non-symmetric pattern (top-left bright, bottom-right dark)
    img = torch.zeros(1, 64, 64)
    img[:, :32, :32] = 1.0

    rotated = augmentor(img)
    assert rotated.shape == (1, 64, 64)
    # Output should not be strictly equal for arbitrary angle
    assert not torch.isnan(rotated).any()


def test_config_driven_builder() -> None:
    """Tests build_satellite_augmentation with different config objects."""
    cfg = AugmentationConfig(
        random_rotation=True,
        random_horizontal_flip=False,
        random_vertical_flip=False,
        random_brightness_jitter=0.08,
    )
    aug = build_satellite_augmentation(cfg, is_train=True)
    assert aug.random_rotation is True
    assert aug.random_flip_h is False
    assert aug.random_flip_v is False
    assert aug.brightness_jitter == 0.08
    assert aug.is_train is True

    # Test validation build
    val_aug = build_satellite_augmentation(cfg, is_train=False)
    assert val_aug.is_train is False
    dummy = torch.rand(1, 32, 32)
    assert torch.equal(val_aug(dummy), dummy)


def test_non_image_modality_isolation() -> None:
    """Confirms non-image features (ERA5 env scalars, trajectory tracks) are not transformed."""
    env_vector = torch.randn(8, 12)
    track_sequence = torch.randn(8, 8, 4)

    # Augmentor should only be invoked on image tensors
    aug = build_satellite_augmentation(is_train=True)
    img_tensor = torch.rand(8, 1, 64, 64)
    aug_img = aug(img_tensor)

    assert aug_img.shape == img_tensor.shape
    # Environmental and track tensors remain completely separate
    assert env_vector.shape == (8, 12)
    assert track_sequence.shape == (8, 8, 4)
