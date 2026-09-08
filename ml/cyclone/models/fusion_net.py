"""Unified multi-modal Cyclone Brain (FusionNet) sharing a fused trunk across all prediction heads."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union
import torch
import torch.nn as nn

from ml.cyclone.config import CycloneConfig, load_config
from ml.cyclone.models.env_branch import EnvBranch
from ml.cyclone.models.heads import (
    DEFAULT_TRACK_HORIZONS,
    DetectionHead,
    IntensityHead,
    StageHead,
    TrackHead,
)
from ml.cyclone.models.image_branch import ImageBranch
from ml.cyclone.models.track_branch import TrackBranch


class FusionNet(nn.Module):
    """Unified Multi-Modal Cyclone Intelligence Neural Network.

    Architecture & Trunk Sharing:
    1. Vision Branch: Satellite IR ImageBranch -> 512-d visual embedding (with zero/learned fallback if image missing).
    2. Environmental Branch: ERA5 scalar EnvBranch -> 64-d atmospheric embedding.
    3. Trajectory Dynamics Branch: Temporal GRU TrackBranch -> 128-d kinematic embedding.
    4. Multi-Modal Fusion Trunk: Concat [512 + 64 + 128 = 704] -> 2-layer MLP with LayerNorm & GELU -> shared latent.
    5. Shared Prediction Heads:
       - DetectionHead: Binary cyclone presence probability.
       - StageHead: 6-class cyclone lifecycle stage.
       - IntensityHead: Continuous wind (kt) & pressure (mb) regression + 7-class IMD scale.
       - TrackHead: Multi-horizon trajectory displacements (dlat, dlon) + heteroscedastic log-variances.
    """

    def __init__(
        self,
        image_backbone: str = "efficientnet_b0",
        image_pretrained: bool = True,
        image_dim: int = 512,
        env_in_dim: int = 6,
        env_dim: int = 64,
        track_in_dim: int = 7,
        track_hidden_dim: int = 128,
        track_layers: int = 2,
        fusion_hidden_dim: int = 512,
        shared_dim: int = 256,
        num_stages: int = 6,
        num_imd_levels: int = 7,
        num_track_horizons: int = 5,
        track_decoder_type: str = "mlp",
        dropout: float = 0.2,
    ) -> None:
        super().__init__()
        self.image_dim = image_dim
        self.env_dim = env_dim
        self.track_dim = track_hidden_dim
        self.shared_dim = shared_dim
        self.num_track_horizons = num_track_horizons

        # 1. Modality branches
        self.image_branch = ImageBranch(
            backbone_name=image_backbone,
            pretrained=image_pretrained,
            in_chans=1,
            embedding_dim=image_dim,
            dropout=dropout,
        )

        self.env_branch = EnvBranch(
            in_dim=env_in_dim,
            hidden_dim=env_dim,
            out_dim=env_dim,
            dropout=dropout,
        )

        self.track_branch = TrackBranch(
            input_dim=track_in_dim,
            hidden_dim=track_hidden_dim,
            num_layers=track_layers,
            out_dim=track_hidden_dim,
            dropout=dropout,
        )

        # 2. Multi-modal fusion trunk
        raw_concat_dim = image_dim + env_dim + track_hidden_dim  # 512 + 64 + 128 = 704
        self.fusion_trunk = nn.Sequential(
            nn.Linear(raw_concat_dim, fusion_hidden_dim),
            nn.LayerNorm(fusion_hidden_dim),
            nn.GELU(),
            nn.Dropout(p=dropout),
            nn.Linear(fusion_hidden_dim, shared_dim),
            nn.LayerNorm(shared_dim),
            nn.GELU(),
            nn.Dropout(p=dropout),
        )

        # 3. All prediction heads branching off the shared trunk
        self.detection_head = DetectionHead(
            embedding_dim=shared_dim,
            hidden_dim=128,
            dropout=dropout,
        )

        self.stage_head = StageHead(
            embedding_dim=shared_dim,
            num_stages=num_stages,
            hidden_dim=128,
            dropout=dropout,
        )

        self.intensity_head = IntensityHead(
            embedding_dim=shared_dim,
            num_imd_levels=num_imd_levels,
            hidden_dim=128,
            dropout=dropout,
        )

        self.track_head = TrackHead(
            embedding_dim=shared_dim,
            num_horizons=num_track_horizons,
            hidden_dim=256,
            dropout=dropout,
            decoder_type=track_decoder_type,
        )

    def forward(
        self,
        img: Optional[torch.Tensor] = None,
        env_vector: Optional[torch.Tensor] = None,
        track_sequence: Optional[torch.Tensor] = None,
        image_available: Optional[torch.Tensor] = None,
        seq_lengths: Optional[torch.Tensor] = None,
    ) -> Dict[str, Any]:
        """Runs the multi-modal forward pass, gracefully handling missing images.

        Args:
            img: Optional batch of single-channel IR images (B, 1, H, W) or (B, H, W).
            env_vector: Atmospheric environmental tensor (B, 6).
            track_sequence: Historical trajectory tensor (B, N, 7).
            image_available: Optional binary mask (B,) or (B, 1) where 1 indicates image present, 0 missing.
            seq_lengths: Optional valid step counts per sequence for packed GRU execution.

        Returns:
            Dict containing predictions across all heads:
                - 'detection_logits' (B, 1), 'detection_probs' (B, 1), 'detected' (B, 1)
                - 'stage_logits' (B, 6), 'stage_probs' (B, 6), 'predicted_stage_idx' (B,)
                - 'intensity': {'wind_kt' (B, 1), 'pres_mb' (B, 1), 'imd_logits' (B, 7), 'imd_probs' (B, 7)}
                - 'track': {'deltas' (B, H, 2), 'log_vars' (B, H, 2)}
                - 'shared_embedding' (B, shared_dim)
        """
        batch_size = (
            env_vector.shape[0] if env_vector is not None
            else (track_sequence.shape[0] if track_sequence is not None
            else (img.shape[0] if img is not None else 1))
        )
        device = (
            env_vector.device if env_vector is not None
            else (track_sequence.device if track_sequence is not None
            else (img.device if img is not None else torch.device("cpu")))
        )

        # 1. Image embedding (graceful fallback if image missing or image_available=0)
        if img is not None:
            img_emb = self.image_branch(img, image_available=image_available)
        else:
            img_emb = self.image_branch.missing_image_embedding.expand(batch_size, -1).to(device)

        if image_available is not None:
            mask = image_available.view(batch_size, 1).to(dtype=img_emb.dtype, device=img_emb.device)
            img_emb = img_emb * mask

        # 2. Environmental embedding
        if env_vector is not None:
            env_clean = torch.nan_to_num(env_vector, nan=0.0)
            env_emb = self.env_branch(env_clean)
        else:
            env_emb = torch.zeros(batch_size, self.env_dim, device=device)

        # 3. Track dynamics embedding
        if track_sequence is not None:
            track_clean = torch.nan_to_num(track_sequence, nan=0.0)
            track_emb = self.track_branch(track_clean, seq_lengths=seq_lengths)
        else:
            track_emb = torch.zeros(batch_size, self.track_dim, device=device)

        # 4. Multi-modal fusion trunk
        concat_emb = torch.cat([img_emb, env_emb, track_emb], dim=-1)
        shared_emb = self.fusion_trunk(concat_emb)  # (B, shared_dim)

        # 5. Shared prediction heads
        det_logits, det_probs = self.detection_head(shared_emb)
        stage_logits, stage_probs = self.stage_head(shared_emb)
        int_out = self.intensity_head(shared_emb)
        track_deltas, track_logvars = self.track_head(shared_emb)

        return {
            "detection_logits": det_logits,
            "detection_probs": det_probs,
            "detected": (det_probs >= 0.50).to(torch.float32),
            "stage_logits": stage_logits,
            "stage_probs": stage_probs,
            "predicted_stage_idx": torch.argmax(stage_probs, dim=-1),
            "intensity": {
                "wind_kt": int_out["wind_kt"],
                "pres_mb": int_out["pres_mb"],
                "imd_logits": int_out["imd_logits"],
                "imd_probs": int_out["imd_probs"],
                "predicted_imd_idx": torch.argmax(int_out["imd_probs"], dim=-1),
            },
            "track": {
                "deltas": track_deltas,
                "log_vars": track_logvars,
            },
            "shared_embedding": shared_emb,
        }

    def load_pretrained_image_weights(
        self,
        checkpoint_path: Union[str, Path],
        freeze_early_blocks: int = 0,
    ) -> bool:
        """Loads pretrained vision weights into image_branch and optionally freezes early layers."""
        ckpt_p = Path(checkpoint_path)
        if not ckpt_p.is_file():
            return False

        try:
            ckpt = torch.load(ckpt_p, map_location="cpu")
            state_dict = ckpt.get("model_state_dict", ckpt)

            # Filter state dict for image_branch keys
            img_state: Dict[str, torch.Tensor] = {}
            for k, v in state_dict.items():
                if k.startswith("image_branch."):
                    img_state[k[len("image_branch."):]] = v
                elif not k.startswith("detection_head.") and not k.startswith("intensity_head.") and not k.startswith("stage_head."):
                    img_state[k] = v

            missing, unexpected = self.image_branch.load_state_dict(img_state, strict=False)

            # Freeze early backbone parameters if requested
            if freeze_early_blocks > 0:
                params = list(self.image_branch.backbone.parameters())
                freeze_count = min(freeze_early_blocks, len(params))
                for p in params[:freeze_count]:
                    p.requires_grad = False

            return True
        except Exception:
            return False

    @classmethod
    def from_config(cls, cfg: Optional[Union[CycloneConfig, Dict[str, Any]]] = None) -> FusionNet:
        """Factory constructor instantiating FusionNet from project configuration."""
        if cfg is None:
            cfg = load_config()

        model_cfg = cfg.model if hasattr(cfg, "model") else (cfg.get("model", {}) if isinstance(cfg, dict) else {})
        img_cfg = getattr(model_cfg, "image_branch", {}) if hasattr(model_cfg, "image_branch") else (
            model_cfg.get("image_branch", {}) if isinstance(model_cfg, dict) else {}
        )
        env_cfg = getattr(model_cfg, "env_branch", {}) if hasattr(model_cfg, "env_branch") else (
            model_cfg.get("env_branch", {}) if isinstance(model_cfg, dict) else {}
        )
        track_cfg = getattr(model_cfg, "track_branch", {}) if hasattr(model_cfg, "track_branch") else (
            model_cfg.get("track_branch", {}) if isinstance(model_cfg, dict) else {}
        )

        backbone = getattr(img_cfg, "backbone", "efficientnet_b0") if hasattr(img_cfg, "backbone") else img_cfg.get("backbone", "efficientnet_b0")
        pretrained = getattr(img_cfg, "pretrained", True) if hasattr(img_cfg, "pretrained") else img_cfg.get("pretrained", True)
        image_dim = getattr(img_cfg, "embedding_dim", 512) if hasattr(img_cfg, "embedding_dim") else img_cfg.get("embedding_dim", 512)

        env_in = getattr(env_cfg, "in_dim", 6) if hasattr(env_cfg, "in_dim") else env_cfg.get("in_dim", 6)
        env_out = getattr(env_cfg, "out_dim", 64) if hasattr(env_cfg, "out_dim") else env_cfg.get("out_dim", 64)

        track_in = getattr(track_cfg, "input_dim", 7) if hasattr(track_cfg, "input_dim") else track_cfg.get("input_dim", 7)
        track_hidden = getattr(track_cfg, "hidden_dim", 128) if hasattr(track_cfg, "hidden_dim") else track_cfg.get("hidden_dim", 128)
        track_layers = getattr(track_cfg, "num_layers", 2) if hasattr(track_cfg, "num_layers") else track_cfg.get("num_layers", 2)

        return cls(
            image_backbone=backbone,
            image_pretrained=pretrained,
            image_dim=image_dim,
            env_in_dim=env_in,
            env_dim=env_out,
            track_in_dim=track_in,
            track_hidden_dim=track_hidden,
            track_layers=track_layers,
            shared_dim=256,
            num_track_horizons=len(DEFAULT_TRACK_HORIZONS),
        )


__all__ = ["FusionNet"]
