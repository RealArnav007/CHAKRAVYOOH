"""Learning rate scheduling and layer-wise learning rate decay (LLRD) for cyclone neural models."""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple, Union
import torch
import torch.nn as nn
from torch.optim import Optimizer
from torch.optim.lr_scheduler import _LRScheduler, LambdaLR


class CosineWarmupScheduler(_LRScheduler):
    """Cosine Annealing Learning Rate Scheduler with Linear Warmup.

    Learning rate schedule phases:
    1. Linear Warmup: For step in [0, warmup_steps), lr scales linearly from min_lr to base_lr.
    2. Cosine Decay: For step in [warmup_steps, total_steps], lr decays following cosine curve to min_lr.
    """

    def __init__(
        self,
        optimizer: Optimizer,
        warmup_steps: int,
        total_steps: int,
        min_lr: float = 1e-6,
        last_epoch: int = -1,
    ) -> None:
        self.warmup_steps = max(1, warmup_steps)
        self.total_steps = max(self.warmup_steps + 1, total_steps)
        self.min_lr = min_lr
        super().__init__(optimizer, last_epoch)

    def get_lr(self) -> List[float]:
        step = self.last_epoch
        if step < self.warmup_steps:
            # Linear warmup
            alpha = float(step) / float(self.warmup_steps)
            return [self.min_lr + (base_lr - self.min_lr) * alpha for base_lr in self.base_lrs]
        elif step > self.total_steps:
            return [self.min_lr for _ in self.base_lrs]
        else:
            # Cosine decay
            progress = float(step - self.warmup_steps) / float(max(1, self.total_steps - self.warmup_steps))
            cosine_decay = 0.5 * (1.0 + math.cos(math.pi * progress))
            return [self.min_lr + (base_lr - self.min_lr) * cosine_decay for base_lr in self.base_lrs]


def get_cosine_schedule_with_warmup(
    optimizer: Optimizer,
    num_warmup_steps: int,
    num_training_steps: int,
    min_lr_ratio: float = 0.01,
) -> LambdaLR:
    """Creates a learning rate scheduler with linear warmup and cosine decay.

    Args:
        optimizer: PyTorch optimizer.
        num_warmup_steps: Steps spent linearly ramping learning rate.
        num_training_steps: Total steps across all training epochs.
        min_lr_ratio: Minimum learning rate floor as fraction of base LR.

    Returns:
        LambdaLR scheduler instance.
    """
    def lr_lambda(current_step: int) -> float:
        if current_step < num_warmup_steps:
            return float(current_step) / float(max(1, num_warmup_steps))
        progress = float(current_step - num_warmup_steps) / float(max(1, num_training_steps - num_warmup_steps))
        cosine_decay = 0.5 * (1.0 + math.cos(math.pi * min(1.0, progress)))
        return min_lr_ratio + (1.0 - min_lr_ratio) * cosine_decay

    return LambdaLR(optimizer, lr_lambda)


def get_layerwise_decay_param_groups(
    model: nn.Module,
    base_lr: float = 2e-4,
    weight_decay: float = 1e-4,
    backbone_lr_ratio: float = 0.1,
    layer_decay: float = 0.75,
    no_decay_bias_norm: bool = True,
) -> List[Dict[str, Any]]:
    r"""Builds optimizer parameter groups with Layer-wise Learning Rate Decay (LLRD).

    Atmospheric Vision Physics & Transfer Learning:
    - Pretrained early convolutional blocks detect generic edges and textures; updating them with
      high learning rates causes catastrophic forgetting of robust ImageNet features.
    - Deep feature representations and cyclone task heads (intensity regression, track decoding,
      environmental fusion) adapt rapidly with higher learning rates ($base\_lr$).
    - Biases and 1D normalization parameters (BatchNorm, LayerNorm) have weight decay set to 0.0.

    Args:
        model: FusionNet or Vision model.
        base_lr: Peak learning rate for heads and fusion trunk.
        weight_decay: Standard AdamW weight decay.
        backbone_lr_ratio: Multiplier for maximum backbone learning rate.
        layer_decay: Multiplicative decay factor per stage depth ($0 < layer\_decay \le 1.0$).
        no_decay_bias_norm: If True, disables weight decay for biases and 1D normalization weights.

    Returns:
        List of parameter group dictionaries for torch.optim.AdamW.
    """
    param_groups: List[Dict[str, Any]] = []

    # Identify if model contains image_branch backbone
    backbone_module = None
    if hasattr(model, "image_branch") and hasattr(model.image_branch, "backbone"):
        backbone_module = model.image_branch.backbone
    elif hasattr(model, "backbone"):
        backbone_module = model.backbone

    # Determine depth stages for backbone if present
    num_stages = 4
    decay_scales: Dict[str, float] = {}

    for name, param in model.named_parameters():
        if not param.requires_grad:
            continue

        # Check if parameter is 1D normalization or bias
        is_bias_or_norm = False
        if no_decay_bias_norm:
            if param.ndim <= 1 or name.endswith(".bias") or "norm" in name.lower() or "bn" in name.lower():
                is_bias_or_norm = True

        this_wd = 0.0 if is_bias_or_norm else weight_decay

        # Determine learning rate scale
        lr_scale = 1.0
        if backbone_module is not None and "backbone" in name:
            # Map layer depth: early layers get smaller scale
            stage_idx = 0
            # Common timm naming conventions (conv_stem, blocks.0, blocks.1, layer1, etc.)
            if "stem" in name or "conv1" in name or "bn1" in name:
                stage_idx = 0
            elif "blocks.0" in name or "blocks.1" in name or "layer1" in name:
                stage_idx = 1
            elif "blocks.2" in name or "blocks.3" in name or "layer2" in name:
                stage_idx = 2
            elif "blocks.4" in name or "blocks.5" in name or "layer3" in name:
                stage_idx = 3
            else:
                stage_idx = 4

            # Decay formula: backbone_lr_ratio * (layer_decay ^ (num_stages - stage_idx))
            lr_scale = backbone_lr_ratio * (layer_decay ** (num_stages - stage_idx))
        elif "image_branch" in name:
            lr_scale = backbone_lr_ratio

        group_lr = base_lr * lr_scale
        decay_scales[name] = lr_scale

        param_groups.append({
            "params": [param],
            "lr": group_lr,
            "weight_decay": this_wd,
            "name": name,
            "lr_scale": lr_scale,
        })

    return param_groups


def build_optimizer_with_llrd(
    model: nn.Module,
    lr: float = 2e-4,
    weight_decay: float = 1e-4,
    backbone_lr_ratio: float = 0.1,
    layer_decay: float = 0.75,
    extra_parameters: Optional[List[nn.Parameter]] = None,
) -> Optimizer:
    """Convenience constructor for AdamW with layer-wise learning rate decay.

    Args:
        model: Target PyTorch model (e.g. FusionNet).
        lr: Base learning rate.
        weight_decay: Regularization weight decay.
        backbone_lr_ratio: Scale factor for vision backbone learning rate.
        layer_decay: Per-stage decay factor.
        extra_parameters: Additional parameters outside model (e.g. MultiTaskLoss log_vars).

    Returns:
        Configured torch.optim.AdamW optimizer.
    """
    param_groups = get_layerwise_decay_param_groups(
        model=model,
        base_lr=lr,
        weight_decay=weight_decay,
        backbone_lr_ratio=backbone_lr_ratio,
        layer_decay=layer_decay,
    )

    if extra_parameters:
        param_groups.append({
            "params": extra_parameters,
            "lr": lr,
            "weight_decay": 0.0,
            "name": "extra_loss_parameters",
            "lr_scale": 1.0,
        })

    return torch.optim.AdamW(param_groups)


__all__ = [
    "CosineWarmupScheduler",
    "get_cosine_schedule_with_warmup",
    "get_layerwise_decay_param_groups",
    "build_optimizer_with_llrd",
]
