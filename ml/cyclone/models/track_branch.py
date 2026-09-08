"""Temporal recurrent track dynamics branch using GRU for trajectory modeling."""

from __future__ import annotations

from typing import Any, Dict, Optional, Union
import torch
import torch.nn as nn
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence

from ml.cyclone.config import CycloneConfig, load_config


class TrackBranch(nn.Module):
    """Temporal GRU processing historical trajectory sequences into a 128-d motion embedding.

    Inputs:
    - Track sequence of shape (B, N, 7) where features are:
      [t_offset_h, lat, lon, wind_kt, pres_mb, speed_kt, heading_deg]

    Output:
    - 128-dimensional dense recurrent trajectory embedding vector representing translational
      velocity, acceleration, curvature, and intensity rate of change (dV/dt, dP/dt).
    """

    def __init__(
        self,
        input_dim: int = 7,
        hidden_dim: int = 128,
        num_layers: int = 2,
        out_dim: int = 128,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.out_dim = out_dim

        # Input feature projection + LayerNorm
        self.in_proj = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
        )

        # Recurrent GRU trunk
        self.gru = nn.GRU(
            input_size=hidden_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )

        # Output projection head
        if hidden_dim != out_dim:
            self.out_proj = nn.Sequential(
                nn.Linear(hidden_dim, out_dim),
                nn.LayerNorm(out_dim),
                nn.GELU(),
            )
        else:
            self.out_proj = nn.LayerNorm(out_dim)

    def forward(
        self,
        track_sequence: torch.Tensor,
        seq_lengths: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """Forward pass through recurrent GRU.

        Args:
            track_sequence: Sequence tensor of shape (B, N, 7) or (N, 7).
            seq_lengths: Optional 1D tensor of valid step lengths per sample.

        Returns:
            Tensor of shape (B, 128) float32.
        """
        if track_sequence.ndim == 2:
            track_sequence = track_sequence.unsqueeze(0)  # (N, 7) -> (1, N, 7)

        batch_size, seq_len, _ = track_sequence.shape

        # Handle NaN values safely
        x = torch.nan_to_num(track_sequence, nan=0.0)

        # Project step features
        h_seq = self.in_proj(x)  # (B, N, hidden_dim)

        if seq_lengths is not None and seq_len > 1:
            # Packed sequence execution for variable lengths
            clamped_lengths = torch.clamp(seq_lengths.cpu(), min=1, max=seq_len)
            packed = pack_padded_sequence(
                h_seq,
                lengths=clamped_lengths,
                batch_first=True,
                enforce_sorted=False,
            )
            _, h_n = self.gru(packed)
        else:
            # Standard sequential execution
            _, h_n = self.gru(h_seq)

        # Extract top-layer final hidden state
        final_hidden = h_n[-1]  # (B, hidden_dim)

        # Output projection and normalization
        out = self.out_proj(final_hidden)  # (B, out_dim)
        return out

    @classmethod
    def from_config(cls, cfg: Optional[Union[CycloneConfig, Dict[str, Any]]] = None) -> TrackBranch:
        """Factory constructor instantiating TrackBranch from configuration."""
        if cfg is None:
            cfg = load_config()

        model_cfg = cfg.model if hasattr(cfg, "model") else (cfg.get("model", {}) if isinstance(cfg, dict) else {})
        track_cfg = getattr(model_cfg, "track_branch", {}) if hasattr(model_cfg, "track_branch") else (
            model_cfg.get("track_branch", {}) if isinstance(model_cfg, dict) else {}
        )

        in_dim = getattr(track_cfg, "input_dim", 7) if hasattr(track_cfg, "input_dim") else track_cfg.get("input_dim", 7)
        hidden_dim = getattr(track_cfg, "hidden_dim", 128) if hasattr(track_cfg, "hidden_dim") else track_cfg.get("hidden_dim", 128)
        num_layers = getattr(track_cfg, "num_layers", 2) if hasattr(track_cfg, "num_layers") else track_cfg.get("num_layers", 2)
        out_dim = getattr(track_cfg, "out_dim", 128) if hasattr(track_cfg, "out_dim") else track_cfg.get("out_dim", 128)

        return cls(
            input_dim=in_dim,
            hidden_dim=hidden_dim,
            num_layers=num_layers,
            out_dim=out_dim,
        )


__all__ = ["TrackBranch"]
