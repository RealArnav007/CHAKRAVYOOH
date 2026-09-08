"""Satellite IR Image Feature Extractor Branch using timm backbones."""

from __future__ import annotations

from typing import Any, Dict, Optional, Union
import timm
import torch
import torch.nn as nn

from ml.cyclone.config import CycloneConfig, load_config


class ImageBranch(nn.Module):
    """Deep convolutional/transformer vision branch extracting 512-d feature embeddings from satellite IR imagery.

    Architecture & Design:
    - Configurable timm backbone (default: 'efficientnet_b0', also supports 'resnet18', 'convnext_tiny').
    - Native single-channel IR support (`in_chans=1`) by adapting/summing pretrained ImageNet RGB weights.
    - Adaptive Global Average Pooling followed by a linear projection + LayerNorm + GELU yielding exactly 512-d embeddings.
    - Robust to missing images: Provides a learned or zero fallback embedding when image is missing/masked.
    """

    def __init__(
        self,
        backbone_name: str = "efficientnet_b0",
        pretrained: bool = True,
        in_chans: int = 1,
        embedding_dim: int = 512,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        self.backbone_name = backbone_name
        self.pretrained = pretrained
        self.in_chans = in_chans
        self.embedding_dim = embedding_dim

        # 1. Instantiate backbone with in_chans=1
        try:
            self.backbone = timm.create_model(
                backbone_name,
                pretrained=pretrained,
                in_chans=in_chans,
                num_classes=0,  # Strips classification head, outputs pooled features
            )
        except Exception:
            # Safe fallback if offline or weights cannot be downloaded
            self.backbone = timm.create_model(
                backbone_name,
                pretrained=False,
                in_chans=in_chans,
                num_classes=0,
            )

        # 2. Determine backbone output feature dimension
        num_features = getattr(self.backbone, "num_features", None)
        if num_features is None:
            # Probe feature dim dynamically with dummy forward pass
            with torch.no_grad():
                dummy = torch.zeros(1, in_chans, 224, 224)
                out = self.backbone(dummy)
                num_features = out.shape[-1] if out.ndim == 2 else out.view(1, -1).shape[-1]

        self.num_features = int(num_features)

        # 3. Projection projection head to 512-d embedding
        if self.num_features != self.embedding_dim:
            self.projection = nn.Sequential(
                nn.Linear(self.num_features, self.embedding_dim),
                nn.LayerNorm(self.embedding_dim),
                nn.GELU(),
                nn.Dropout(p=dropout),
            )
        else:
            self.projection = nn.Identity()

        # Learned fallback embedding for when image modality is unavailable
        self.missing_image_embedding = nn.Parameter(torch.zeros(1, self.embedding_dim))
        nn.init.normal_(self.missing_image_embedding, mean=0.0, std=0.02)

    def forward(
        self,
        img: Optional[torch.Tensor] = None,
        image_available: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """Extracts 512-d visual embeddings from input IR patches.

        Args:
            img: Batch of single-channel IR images. Shape (B, 1, H, W) or (B, H, W) with values in [0, 1].
            image_available: Optional binary mask (B,) or (B, 1) where 1 indicates valid image, 0 missing.

        Returns:
            Embedding tensor of shape (B, 512) float32.
        """
        if img is None:
            # Batch size cannot be inferred without img or image_available; fallback to batch=1
            return self.missing_image_embedding

        if img.ndim == 3:
            img = img.unsqueeze(1)  # (B, H, W) -> (B, 1, H, W)

        batch_size = img.shape[0]

        # Extract backbone features
        raw_feat = self.backbone(img)
        if raw_feat.ndim > 2:
            raw_feat = raw_feat.flatten(start_dim=1)

        embedding = self.projection(raw_feat)  # (B, 512)

        # Mask missing images with learned fallback embedding
        if image_available is not None:
            mask = image_available.view(batch_size, 1).to(dtype=embedding.dtype, device=embedding.device)
            fallback = self.missing_image_embedding.expand(batch_size, -1)
            embedding = mask * embedding + (1.0 - mask) * fallback

        return embedding

    @classmethod
    def from_config(cls, cfg: Optional[Union[CycloneConfig, Dict[str, Any]]] = None) -> ImageBranch:
        """Factory constructor instantiating ImageBranch from project configuration."""
        if cfg is None:
            cfg = load_config()

        model_cfg = cfg.model if hasattr(cfg, "model") else (cfg.get("model", {}) if isinstance(cfg, dict) else {})
        img_cfg = getattr(model_cfg, "image_branch", {}) if hasattr(model_cfg, "image_branch") else (
            model_cfg.get("image_branch", {}) if isinstance(model_cfg, dict) else {}
        )

        backbone = getattr(img_cfg, "backbone", "efficientnet_b0") if hasattr(img_cfg, "backbone") else img_cfg.get("backbone", "efficientnet_b0")
        pretrained = getattr(img_cfg, "pretrained", True) if hasattr(img_cfg, "pretrained") else img_cfg.get("pretrained", True)
        embedding_dim = getattr(img_cfg, "embedding_dim", 512) if hasattr(img_cfg, "embedding_dim") else img_cfg.get("embedding_dim", 512)

        return cls(
            backbone_name=backbone,
            pretrained=pretrained,
            in_chans=1,
            embedding_dim=embedding_dim,
        )


__all__ = ["ImageBranch"]
