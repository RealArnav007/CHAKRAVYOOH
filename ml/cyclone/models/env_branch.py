"""Environmental atmospheric & oceanic scalar feature branch (MLP)."""

from __future__ import annotations

from typing import Any

import torch
import torch.nn as nn

from ml.cyclone.config import CycloneConfig, load_config


class EnvBranch(nn.Module):
    """Deep MLP processing ERA5 reanalysis environmental scalars into a 64-d representation.

    Inputs (6-d):
    - Sea Surface Temperature (SST, °C)
    - 850–200 hPa Deep-Layer Vertical Wind Shear (m/s)
    - 500 hPa Relative Humidity (%)
    - 850 hPa Relative Vorticity (* 10^-5 s^-1)
    - Mean Sea Level Pressure (MSLP, mb)
    - 10m Surface Wind Speed (m/s)

    Output:
    - 64-dimensional dense environmental embedding vector with BatchNorm and Dropout regularization.
    """

    def __init__(
        self,
        in_dim: int = 6,
        hidden_dim: int = 64,
        out_dim: int = 64,
        dropout: float = 0.15,
    ) -> None:
        super().__init__()
        self.in_dim = in_dim
        self.hidden_dim = hidden_dim
        self.out_dim = out_dim

        self.net = nn.Sequential(
            nn.Linear(in_dim, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.GELU(),
            nn.Dropout(p=dropout),
            nn.Linear(hidden_dim, out_dim),
            nn.BatchNorm1d(out_dim),
            nn.GELU(),
        )

    def forward(self, env_vector: torch.Tensor) -> torch.Tensor:
        """Forward pass extracting dense atmospheric embeddings.

        Args:
            env_vector: Tensor of shape (B, 6) or (6,).

        Returns:
            Tensor of shape (B, 64) float32.
        """
        if env_vector.ndim == 1:
            env_vector = env_vector.unsqueeze(0)

        # Handle batch size of 1 with BatchNorm in eval mode or LayerNorm fallback
        if env_vector.shape[0] == 1 and self.training:
            # Temporarily toggle eval for BatchNorm when B=1 to avoid variance division error
            self.eval()
            out = self.net(env_vector)
            self.train()
            return out

        return self.net(env_vector)

    @classmethod
    def from_config(cls, cfg: CycloneConfig | dict[str, Any] | None = None) -> EnvBranch:
        """Factory constructor instantiating EnvBranch from configuration."""
        if cfg is None:
            cfg = load_config()

        model_cfg = (
            cfg.model
            if hasattr(cfg, "model")
            else (cfg.get("model", {}) if isinstance(cfg, dict) else {})
        )
        env_cfg = (
            getattr(model_cfg, "env_branch", {})
            if hasattr(model_cfg, "env_branch")
            else (model_cfg.get("env_branch", {}) if isinstance(model_cfg, dict) else {})
        )

        in_dim = (
            getattr(env_cfg, "in_dim", 6)
            if hasattr(env_cfg, "in_dim")
            else env_cfg.get("in_dim", 6)
        )
        out_dim = (
            getattr(env_cfg, "out_dim", 64)
            if hasattr(env_cfg, "out_dim")
            else env_cfg.get("out_dim", 64)
        )

        return cls(in_dim=in_dim, out_dim=out_dim)


__all__ = ["EnvBranch"]
