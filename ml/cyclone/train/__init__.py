from ml.cyclone.train.augment import SatelliteAugmentor, build_satellite_augmentation
from ml.cyclone.train.losses import GaussianNLLLoss, MultiTaskLoss
from ml.cyclone.train.schedule import (
    CosineWarmupScheduler,
    build_optimizer_with_llrd,
    get_cosine_schedule_with_warmup,
    get_layerwise_decay_param_groups,
)
from ml.cyclone.train.sweep import lock_in_best_config, run_hyperparameter_sweep
from ml.cyclone.train.train_detection import train_detection
from ml.cyclone.train.train_fusion import train_fusion
from ml.cyclone.train.train_intensity import train_intensity
from ml.cyclone.train.train_stage import train_stage
from ml.cyclone.train.train_track import haversine_loss, train_track
from ml.cyclone.train.trainer import Trainer

__all__ = [
    "train_detection",
    "train_intensity",
    "train_stage",
    "train_track",
    "train_fusion",
    "haversine_loss",
    "Trainer",
    "MultiTaskLoss",
    "GaussianNLLLoss",
    "SatelliteAugmentor",
    "build_satellite_augmentation",
    "CosineWarmupScheduler",
    "get_cosine_schedule_with_warmup",
    "get_layerwise_decay_param_groups",
    "build_optimizer_with_llrd",
    "run_hyperparameter_sweep",
    "lock_in_best_config",
]
