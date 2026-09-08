"""Physically-valid satellite infrared (IR) imagery data augmentation pipeline."""

from __future__ import annotations

import random
from typing import Any

import torch
import torch.nn as nn
import torchvision.transforms.functional as TF

from ml.cyclone.config import AugmentationConfig, CycloneConfig, load_config


class SatelliteAugmentor(nn.Module):
    """Physically-valid augmentation engine for single-channel satellite IR imagery.

    Atmospheric Physics Principles:
    1. Full 0–360° Rotational Invariance: Tropical cyclones exhibit quasi-rotational symmetry
       around their convective core. Arbitrary 2D rotation produces physically valid cyclone structures.
    2. Reflection (Flips): Inverted vortex representations maintain realistic spiral rainband physics.
    3. Center / Translation Jitter: Accounts for operational vortex center positioning uncertainty (+/- 15 km).
    4. IR Photometric Jitter: Small brightness/contrast adjustments modeling radiometric calibration variations.
    5. Cutout / Random Erasing: Simulates local cirrus cloud occlusion and sensor telemetry dropouts.
    6. Non-Image Modality Protection: Environmental scalars (ERA5) and trajectory track sequences are
       strictly NEVER perturbed to preserve physical thermodynamic and kinematic consistency.
    """

    def __init__(
        self,
        random_rotation: bool = True,
        max_rotation_deg: float = 360.0,
        random_flip_h: bool = True,
        random_flip_v: bool = True,
        random_crop_scale: tuple[float, float] = (0.88, 1.0),
        brightness_jitter: float = 0.05,
        contrast_jitter: float = 0.05,
        cutout: bool = True,
        cutout_size_ratio: float = 0.12,
        is_train: bool = True,
    ) -> None:
        super().__init__()
        self.random_rotation = random_rotation
        self.max_rotation_deg = max_rotation_deg
        self.random_flip_h = random_flip_h
        self.random_flip_v = random_flip_v
        self.random_crop_scale = random_crop_scale
        self.brightness_jitter = brightness_jitter
        self.contrast_jitter = contrast_jitter
        self.cutout = cutout
        self.cutout_size_ratio = cutout_size_ratio
        self.is_train = is_train

    def forward(self, img_tensor: torch.Tensor) -> torch.Tensor:
        """Applies stochastic transforms to satellite IR image tensor.

        Args:
            img_tensor: Tensor of shape (1, H, W) or (B, 1, H, W) normalized to [0, 1].

        Returns:
            Augmented tensor of identical shape and dtype.
        """
        # Strictly no augmentation during validation, testing, or if disabled
        if not self.is_train or not self.training:
            return img_tensor

        # Handle batch or single image
        if img_tensor.ndim == 3:
            return self._augment_single(img_tensor)
        elif img_tensor.ndim == 4:
            augmented_list = [
                self._augment_single(img_tensor[i]) for i in range(img_tensor.size(0))
            ]
            return torch.stack(augmented_list, dim=0)
        else:
            return img_tensor

    def _augment_single(self, img: torch.Tensor) -> torch.Tensor:
        """Augments a single 3D image tensor (C, H, W)."""
        _, h, w = img.shape
        x = img.clone()

        # 1. Full 0–360° Random Rotation (Key Cyclone Lever)
        if self.random_rotation:
            angle = random.uniform(0.0, self.max_rotation_deg)
            x = TF.rotate(
                x,
                angle=angle,
                interpolation=TF.InterpolationMode.BILINEAR,
                expand=False,
                fill=float(x.mean().item()),
            )

        # 2. Random Horizontal & Vertical Flips
        if self.random_flip_h and random.random() > 0.5:
            x = TF.hflip(x)
        if self.random_flip_v and random.random() > 0.5:
            x = TF.vflip(x)

        # 3. Small Random Crop & Scale (Vortex Center Jitter)
        if self.random_crop_scale and self.random_crop_scale[0] < 1.0:
            scale = random.uniform(self.random_crop_scale[0], self.random_crop_scale[1])
            crop_h = int(round(h * scale))
            crop_w = int(round(w * scale))

            top = random.randint(0, h - crop_h)
            left = random.randint(0, w - crop_w)

            x_cropped = TF.crop(x, top=top, left=left, height=crop_h, width=crop_w)
            x = TF.resize(
                x_cropped, size=[h, w], interpolation=TF.InterpolationMode.BILINEAR, antialias=True
            )

        # 4. IR Photometric Jitter (Realistic brightness & contrast bounds)
        if self.brightness_jitter > 0.0:
            b_factor = random.uniform(1.0 - self.brightness_jitter, 1.0 + self.brightness_jitter)
            x = x * b_factor

        if self.contrast_jitter > 0.0:
            c_factor = random.uniform(1.0 - self.contrast_jitter, 1.0 + self.contrast_jitter)
            mean_val = x.mean()
            x = (x - mean_val) * c_factor + mean_val

        # Clamp to physical normalized bounds [0, 1]
        x = torch.clamp(x, min=0.0, max=1.0)

        # 5. Optional Cutout / Sensor Occlusion
        if self.cutout and random.random() > 0.5:
            cut_h = int(round(h * self.cutout_size_ratio))
            cut_w = int(round(w * self.cutout_size_ratio))
            if cut_h > 0 and cut_w > 0:
                top = random.randint(0, h - cut_h)
                left = random.randint(0, w - cut_w)
                x[:, top : top + cut_h, left : left + cut_w] = 0.0

        return x


def build_satellite_augmentation(
    config: AugmentationConfig | CycloneConfig | dict[str, Any] | None = None,
    is_train: bool = True,
) -> SatelliteAugmentor:
    """Factory builder for satellite imagery augmentor configured from project config.

    Args:
        config: AugmentationConfig, CycloneConfig, or dictionary of settings.
        is_train: Boolean flag enabling transforms only in training mode.

    Returns:
        Configured SatelliteAugmentor callable module.
    """
    if config is None:
        cfg = load_config()
        aug_cfg = cfg.train.augmentation
    elif isinstance(config, CycloneConfig):
        aug_cfg = config.train.augmentation
    elif isinstance(config, AugmentationConfig):
        aug_cfg = config
    elif isinstance(config, dict):
        aug_cfg = AugmentationConfig(
            **{k: v for k, v in config.items() if hasattr(AugmentationConfig, k)}
        )
    else:
        aug_cfg = AugmentationConfig()

    return SatelliteAugmentor(
        random_rotation=getattr(aug_cfg, "random_rotation", True),
        max_rotation_deg=360.0,
        random_flip_h=getattr(aug_cfg, "random_horizontal_flip", True),
        random_flip_v=getattr(aug_cfg, "random_vertical_flip", True),
        random_crop_scale=(0.88, 1.0),
        brightness_jitter=getattr(aug_cfg, "random_brightness_jitter", 0.05),
        contrast_jitter=0.05,
        cutout=True,
        cutout_size_ratio=0.12,
        is_train=is_train,
    )


__all__ = [
    "SatelliteAugmentor",
    "build_satellite_augmentation",
]
