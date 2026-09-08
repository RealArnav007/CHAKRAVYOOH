"""Multi-task neural network prediction heads and standalone detection model."""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple, Union
import torch
import torch.nn as nn

from ml.cyclone.models.image_branch import ImageBranch


# -----------------------------------------------------------------------------
# 1. Detection Head
# -----------------------------------------------------------------------------


class DetectionHead(nn.Module):
    """Binary cyclone detection classification head (presence of organized depression/cyclone vs background)."""

    def __init__(
        self,
        embedding_dim: int = 512,
        hidden_dim: int = 128,
        dropout: float = 0.2,
    ) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(embedding_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
            nn.Dropout(p=dropout),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, embedding: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """Forward pass emitting raw logit and sigmoid probability.

        Args:
            embedding: Feature tensor of shape (B, embedding_dim).

        Returns:
            Tuple of (logits, probs) each of shape (B, 1).
        """
        logits = self.net(embedding)
        probs = torch.sigmoid(logits)
        return logits, probs


# -----------------------------------------------------------------------------
# 2. Standalone Detection Model (ImageBranch + DetectionHead)
# -----------------------------------------------------------------------------


class DetectionModel(nn.Module):
    """Standalone vision-only cyclone detection model combining ImageBranch with DetectionHead."""

    def __init__(
        self,
        backbone_name: str = "efficientnet_b0",
        pretrained: bool = True,
        embedding_dim: int = 512,
        dropout: float = 0.2,
    ) -> None:
        super().__init__()
        self.image_branch = ImageBranch(
            backbone_name=backbone_name,
            pretrained=pretrained,
            in_chans=1,
            embedding_dim=embedding_dim,
            dropout=dropout,
        )
        self.detection_head = DetectionHead(
            embedding_dim=embedding_dim,
            hidden_dim=128,
            dropout=dropout,
        )

    def forward(
        self,
        img: Optional[torch.Tensor] = None,
        image_available: Optional[torch.Tensor] = None,
    ) -> Dict[str, torch.Tensor]:
        """Runs image embedding and detection head.

        Args:
            img: Batch of single-channel IR images of shape (B, 1, H, W) or (B, H, W).
            image_available: Optional binary mask (B,) or (B, 1).

        Returns:
            Dict with 'logits' (B, 1), 'probs' (B, 1), 'detected' (B, 1), and 'embedding' (B, 512).
        """
        embedding = self.image_branch(img, image_available=image_available)
        logits, probs = self.detection_head(embedding)

        return {
            "logits": logits,
            "probs": probs,
            "detected": (probs >= 0.50).to(torch.float32),
            "embedding": embedding,
        }

    @classmethod
    def from_config(cls, cfg: Optional[Any] = None) -> DetectionModel:
        """Factory constructor instantiating DetectionModel from config."""
        from ml.cyclone.config import load_config
        if cfg is None:
            cfg = load_config()

        model_cfg = cfg.model if hasattr(cfg, "model") else {}
        img_cfg = getattr(model_cfg, "image_branch", {}) if hasattr(model_cfg, "image_branch") else {}
        backbone = getattr(img_cfg, "backbone", "efficientnet_b0") if hasattr(img_cfg, "backbone") else "efficientnet_b0"
        embedding_dim = getattr(img_cfg, "embedding_dim", 512) if hasattr(img_cfg, "embedding_dim") else 512

        return cls(
            backbone_name=backbone,
            pretrained=True,
            embedding_dim=embedding_dim,
        )


# -----------------------------------------------------------------------------
# 3. Lifecycle Stage Classification Head
# -----------------------------------------------------------------------------


class StageClassificationHead(nn.Module):
    """Multi-class lifecycle stage classification head (6 classes)."""

    def __init__(
        self,
        embedding_dim: int = 512,
        num_stages: int = 6,
        hidden_dim: int = 128,
        dropout: float = 0.2,
    ) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(embedding_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
            nn.Dropout(p=dropout),
            nn.Linear(hidden_dim, num_stages),
        )

    def forward(self, embedding: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """Emits raw stage logits (B, 6) and softmax probabilities (B, 6)."""
        logits = self.net(embedding)
        probs = torch.softmax(logits, dim=-1)
        return logits, probs


# -----------------------------------------------------------------------------
# 4. Intensity Estimation Head
# -----------------------------------------------------------------------------


class IntensityHead(nn.Module):
    """Intensity estimation head: Continuous wind (kt) & pressure (mb) regression + IMD 7-class logits."""

    def __init__(
        self,
        embedding_dim: int = 512,
        num_imd_levels: int = 7,
        hidden_dim: int = 128,
        dropout: float = 0.2,
    ) -> None:
        super().__init__()
        # Continuous regression trunk
        self.reg_mlp = nn.Sequential(
            nn.Linear(embedding_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
            nn.Dropout(p=dropout),
        )
        self.wind_out = nn.Linear(hidden_dim, 1)      # Wind speed (kt)
        self.pres_out = nn.Linear(hidden_dim, 1)      # Central pressure (mb)

        # Discrete IMD scale classifier
        self.imd_cls = nn.Linear(hidden_dim, num_imd_levels)

    def forward(self, embedding: torch.Tensor) -> Dict[str, torch.Tensor]:
        """Emits predicted wind_kt, pres_mb, and IMD level logits."""
        h = self.reg_mlp(embedding)
        wind_pred = self.wind_out(h)
        pres_pred = self.pres_out(h)
        imd_logits = self.imd_cls(h)

        return {
            "wind_kt": wind_pred,
            "pres_mb": pres_pred,
            "imd_logits": imd_logits,
            "imd_probs": torch.softmax(imd_logits, dim=-1),
        }


# -----------------------------------------------------------------------------
# 5. Trajectory Displacement & Gaussian Uncertainty Head
# -----------------------------------------------------------------------------


class TrackHead(nn.Module):
    """Track forecasting head predicting multi-horizon (dlat, dlon) displacements and log-variances."""

    def __init__(
        self,
        embedding_dim: int = 512,
        num_horizons: int = 5,  # 6h, 12h, 24h, 48h, 72h
        hidden_dim: int = 256,
        dropout: float = 0.2,
    ) -> None:
        super().__init__()
        self.num_horizons = num_horizons
        self.mlp = nn.Sequential(
            nn.Linear(embedding_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
            nn.Dropout(p=dropout),
            nn.Linear(hidden_dim, num_horizons * 4),  # [mu_dlat, mu_dlon, log_var_lat, log_var_lon] per horizon
        )

    def forward(self, embedding: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """Emits predicted displacements (B, H, 2) and heteroscedastic log-variances (B, H, 2)."""
        out = self.mlp(embedding).view(-1, self.num_horizons, 4)
        deltas = out[..., :2]       # [mu_dlat, mu_dlon]
        log_vars = out[..., 2:]     # [log_var_lat, log_var_lon]
        return deltas, log_vars


__all__ = [
    "DetectionHead",
    "DetectionModel",
    "StageClassificationHead",
    "IntensityHead",
    "TrackHead",
]
