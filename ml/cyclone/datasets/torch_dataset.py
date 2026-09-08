"""PyTorch Dataset and custom Collate Function for multi-modal cyclone modeling."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Union
import numpy as np
import torch
from torch.utils.data import Dataset

from ml.cyclone.features.fusion import FusedSample, make_fused_sample


class CycloneDataset(Dataset):
    """PyTorch Dataset yielding multi-modal tensors and supervision targets from FusedSample objects."""

    def __init__(
        self,
        samples: Sequence[Union[FusedSample, Dict[str, Any]]],
        indices: Optional[Sequence[int]] = None,
        mode: str = "multimodal",
        image_shape: tuple[int, int] = (224, 224),
        transform: Optional[Callable[[torch.Tensor], torch.Tensor]] = None,
    ) -> None:
        """Initializes CycloneDataset.

        Args:
            samples: Sequence of FusedSample objects or raw sample dictionaries.
            indices: Optional subset of integer indices to subselect (e.g. from make_splits).
            mode: 'multimodal' (default, returns full sensor trunk) or 'image_only' (pretraining).
            image_shape: (H, W) spatial resolution for satellite tensors.
            transform: Optional torchvision transform callable.
        """
        self.raw_samples = samples
        self.indices = list(indices) if indices is not None else list(range(len(samples)))
        self.mode = mode
        self.image_shape = image_shape
        self.transform = transform

    def __len__(self) -> int:
        return len(self.indices)

    def __getitem__(self, item_idx: int) -> Dict[str, Any]:
        raw_idx = self.indices[item_idx]
        sample_obj = self.raw_samples[raw_idx]

        # Convert raw dict to FusedSample if necessary
        if isinstance(sample_obj, dict):
            fused: FusedSample = make_fused_sample(sample_obj, image_target_size=self.image_shape)
        else:
            fused = sample_obj

        # 1. Image tensor handling (zero tensor + availability flag if missing)
        if fused.image_tensor is not None:
            image_tensor = torch.from_numpy(fused.image_tensor).float()
            image_available = torch.tensor(1.0, dtype=torch.float32)
            if self.transform is not None:
                image_tensor = self.transform(image_tensor)
        else:
            image_tensor = torch.zeros((1, self.image_shape[0], self.image_shape[1]), dtype=torch.float32)
            image_available = torch.tensor(0.0, dtype=torch.float32)

        # Targets
        targets_dict = {
            "wind_kt": torch.tensor(fused.targets["wind_kt"], dtype=torch.float32),
            "pres_mb": torch.tensor(fused.targets["pres_mb"], dtype=torch.float32),
            "imd_level_idx": torch.tensor(fused.targets["imd_level_idx"], dtype=torch.long),
            "stage_idx": torch.tensor(fused.targets["stage_idx"], dtype=torch.long),
            "detected": torch.tensor(fused.targets["detected"], dtype=torch.float32),
            "future_deltas": torch.from_numpy(fused.targets["future_deltas"]).float(),
            "future_positions": torch.from_numpy(fused.targets["future_positions"]).float(),
            "horizon_masks": torch.from_numpy(fused.targets["horizon_masks"]).bool(),
        }

        # 2. Return payload according to execution mode
        if self.mode == "image_only":
            return {
                "image": image_tensor,
                "image_available": image_available,
                "wind_kt": targets_dict["wind_kt"],
                "pres_mb": targets_dict["pres_mb"],
                "imd_level_idx": targets_dict["imd_level_idx"],
                "stage_idx": targets_dict["stage_idx"],
                "meta": fused.meta,
            }

        # Full multimodal mode
        return {
            "image": image_tensor,
            "image_available": image_available,
            "env_vector": torch.from_numpy(fused.env_vector).float(),
            "motion_vector": torch.from_numpy(fused.motion_vector).float(),
            "track_sequence": torch.from_numpy(fused.track_sequence).float(),
            "targets": targets_dict,
            "meta": fused.meta,
        }


def cyclone_collate_fn(batch: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Custom batch collator for CycloneDataset handling multi-modal variable presence and horizon masks.

    Args:
        batch: List of individual item dictionaries returned by CycloneDataset.

    Returns:
        Batched dictionary of stacked PyTorch tensors.
    """
    if not batch:
        return {}

    first = batch[0]
    is_image_only = "env_vector" not in first

    images = torch.stack([item["image"] for item in batch], dim=0)
    images_available = torch.stack([item["image_available"] for item in batch], dim=0)
    metas = [item["meta"] for item in batch]

    if is_image_only:
        return {
            "image": images,
            "image_available": images_available,
            "wind_kt": torch.stack([item["wind_kt"] for item in batch], dim=0),
            "pres_mb": torch.stack([item["pres_mb"] for item in batch], dim=0),
            "imd_level_idx": torch.stack([item["imd_level_idx"] for item in batch], dim=0),
            "stage_idx": torch.stack([item["stage_idx"] for item in batch], dim=0),
            "meta": metas,
        }

    env_vectors = torch.stack([item["env_vector"] for item in batch], dim=0)
    motion_vectors = torch.stack([item["motion_vector"] for item in batch], dim=0)
    track_sequences = torch.stack([item["track_sequence"] for item in batch], dim=0)

    # Collate targets sub-dictionary
    targets_collated = {
        "wind_kt": torch.stack([item["targets"]["wind_kt"] for item in batch], dim=0),
        "pres_mb": torch.stack([item["targets"]["pres_mb"] for item in batch], dim=0),
        "imd_level_idx": torch.stack([item["targets"]["imd_level_idx"] for item in batch], dim=0),
        "stage_idx": torch.stack([item["targets"]["stage_idx"] for item in batch], dim=0),
        "detected": torch.stack([item["targets"]["detected"] for item in batch], dim=0),
        "future_deltas": torch.stack([item["targets"]["future_deltas"] for item in batch], dim=0),
        "future_positions": torch.stack([item["targets"]["future_positions"] for item in batch], dim=0),
        "horizon_masks": torch.stack([item["targets"]["horizon_masks"] for item in batch], dim=0),
    }

    return {
        "image": images,
        "image_available": images_available,
        "env_vector": env_vectors,
        "motion_vector": motion_vectors,
        "track_sequence": track_sequences,
        "targets": targets_collated,
        "meta": metas,
    }


__all__ = ["CycloneDataset", "cyclone_collate_fn"]
