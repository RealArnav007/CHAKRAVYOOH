"""Typed configuration loader and schemas for Chakravyuh Cyclone Engine."""

from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
try:
    import yaml
except ImportError:
    yaml = None


# -----------------------------------------------------------------------------
# Data Configurations
# -----------------------------------------------------------------------------


@dataclass
class NormalizationConfig:
    temp_min_k: float = 180.0
    temp_max_k: float = 310.0


@dataclass
class SatelliteConfig:
    image_size: int = 224
    channels: int = 1
    crop_size_km: float = 1000.0
    ir_band: str = "TIR1"
    normalization: NormalizationConfig = field(default_factory=NormalizationConfig)


@dataclass
class EnvironmentalConfig:
    variables: List[str] = field(
        default_factory=lambda: ["sst", "vertical_wind_shear", "rh_500", "vorticity_850", "ohc"]
    )
    spatial_radius_deg: float = 5.0
    time_resolution_hours: int = 1


@dataclass
class TrackConfig:
    history_steps: int = 8
    step_interval_hours: int = 3
    features: List[str] = field(
        default_factory=lambda: [
            "lat",
            "lon",
            "max_wind_kt",
            "min_pressure_mb",
            "speed_kt",
            "heading_deg",
        ]
    )


@dataclass
class DataPathsConfig:
    data_root: str = "ml/cyclone/data"
    ibtracs_csv: str = "ml/cyclone/data/ibtracs.NI.list.v04r00.csv"
    satellite_dir: str = "ml/cyclone/data/satellite"
    era5_dir: str = "ml/cyclone/data/era5"
    processed_dir: str = "ml/cyclone/data/processed"


@dataclass
class DataConfig:
    basin: str = "North Indian Ocean"
    satellite: SatelliteConfig = field(default_factory=SatelliteConfig)
    environmental: EnvironmentalConfig = field(default_factory=EnvironmentalConfig)
    track: TrackConfig = field(default_factory=TrackConfig)
    paths: DataPathsConfig = field(default_factory=DataPathsConfig)


# -----------------------------------------------------------------------------
# Model Configurations
# -----------------------------------------------------------------------------


@dataclass
class Tier0StageRulesConfig:
    depression_wind_max: float = 27.0
    deep_depression_wind_max: float = 33.0
    cyclonic_storm_wind_max: float = 47.0
    severe_cyclonic_storm_wind_max: float = 63.0
    very_severe_cyclonic_storm_wind_max: float = 89.0
    extremely_severe_cyclonic_storm_wind_max: float = 119.0


@dataclass
class Tier0TrackConfig:
    decay_rate: float = 0.05


@dataclass
class Tier0ParametricConeConfig:
    base_radius_km: float = 0.0
    growth_rate_km_per_hour: float = 4.0


@dataclass
class Tier0Config:
    detection_threshold_wind_kt: float = 17.0
    stage_rules: Tier0StageRulesConfig = field(default_factory=Tier0StageRulesConfig)
    track_persistence: Tier0TrackConfig = field(default_factory=Tier0TrackConfig)
    parametric_cone: Tier0ParametricConeConfig = field(default_factory=Tier0ParametricConeConfig)


@dataclass
class ImageBranchConfig:
    backbone: str = "efficientnet_b0"
    pretrained: bool = True
    in_channels: int = 1
    embedding_dim: int = 512
    dropout: float = 0.2


@dataclass
class EnvBranchConfig:
    input_dim: int = 5
    hidden_dims: List[int] = field(default_factory=lambda: [64, 128])
    embedding_dim: int = 64
    dropout: float = 0.1


@dataclass
class TrackBranchConfig:
    input_dim: int = 6
    hidden_dim: int = 128
    num_layers: int = 2
    embedding_dim: int = 128
    bidirectional: bool = False
    dropout: float = 0.1


@dataclass
class FusionTrunkConfig:
    hidden_dims: List[int] = field(default_factory=lambda: [512, 256])
    dropout: float = 0.3


@dataclass
class HeadsConfig:
    forecast_horizons_hours: List[int] = field(default_factory=lambda: [0, 6, 12, 24, 48, 72])
    num_stage_classes: int = 6
    num_intensity_classes: int = 7
    uncertainty_method: str = "heteroscedastic"


@dataclass
class Tier1Config:
    image_branch: ImageBranchConfig = field(default_factory=ImageBranchConfig)
    env_branch: EnvBranchConfig = field(default_factory=EnvBranchConfig)
    track_branch: TrackBranchConfig = field(default_factory=TrackBranchConfig)
    fusion_trunk: FusionTrunkConfig = field(default_factory=FusionTrunkConfig)
    heads: HeadsConfig = field(default_factory=HeadsConfig)


@dataclass
class ConfidenceGatesConfig:
    min_detection_confidence: float = 0.50
    min_stage_confidence: float = 0.60
    min_intensity_confidence: float = 0.60
    max_track_variance_ceiling: float = 5.0


@dataclass
class ModelConfig:
    model_name: str = "chakravyuh-fusion-net"
    model_version: str = "0.1.0"
    device: str = "auto"
    tier0: Tier0Config = field(default_factory=Tier0Config)
    tier1: Tier1Config = field(default_factory=Tier1Config)
    confidence_gates: ConfidenceGatesConfig = field(default_factory=ConfidenceGatesConfig)


# -----------------------------------------------------------------------------
# Training Configurations
# -----------------------------------------------------------------------------


@dataclass
class OptimizationConfig:
    batch_size: int = 32
    epochs: int = 50
    learning_rate: float = 0.0003
    weight_decay: float = 0.0001
    grad_clip_norm: float = 1.0
    mixed_precision: bool = True


@dataclass
class SchedulerConfig:
    type: str = "cosine_with_warmup"
    warmup_epochs: int = 5
    min_lr: float = 0.000001


@dataclass
class LossWeightsConfig:
    strategy: str = "homoscedastic_learnable"
    initial_weights: Dict[str, float] = field(
        default_factory=lambda: {
            "detection_bce": 1.0,
            "stage_ce": 1.0,
            "intensity_huber": 1.0,
            "intensity_ce": 0.5,
            "track_haversine": 2.0,
            "uncertainty_nll": 0.5,
        }
    )


@dataclass
class AugmentationConfig:
    random_rotation: bool = True
    random_horizontal_flip: bool = False
    random_vertical_flip: bool = False
    random_brightness_jitter: float = 0.05


@dataclass
class ValidationConfig:
    eval_every_n_epochs: int = 1
    patience: int = 10
    primary_metric: str = "val_track_error_km"


@dataclass
class TrainConfig:
    experiment_name: str = "cyclone_brain_v1"
    output_dir: str = "ml/cyclone/checkpoints"
    seed: int = 42
    num_workers: int = 4
    optimization: OptimizationConfig = field(default_factory=OptimizationConfig)
    scheduler: SchedulerConfig = field(default_factory=SchedulerConfig)
    loss_weights: LossWeightsConfig = field(default_factory=LossWeightsConfig)
    augmentation: AugmentationConfig = field(default_factory=AugmentationConfig)
    validation: ValidationConfig = field(default_factory=ValidationConfig)


# -----------------------------------------------------------------------------
# Replay Configurations
# -----------------------------------------------------------------------------


@dataclass
class StormPresetConfig:
    cyclone_id: str
    name: str
    season: int
    start_time: str
    landfall_time: str
    end_time: str
    step_hours: int = 3
    landfall_coords: Dict[str, float] = field(default_factory=dict)
    presets: Dict[str, str] = field(default_factory=dict)


@dataclass
class PlaybackConfig:
    playback_speed: float = 1.0
    output_format: str = "jsonl"
    producer_endpoint: str = "http://localhost:8000/api/v1/cyclone/intelligence"
    drop_directory: str = "ml/cyclone/data/replay_feed"


@dataclass
class ReplayConfig:
    default_storm_id: str = "CYC-2020-BAY-001"
    default_storm_name: str = "Amphan"
    basin: str = "North Indian Ocean"
    storms: Dict[str, Any] = field(default_factory=dict)
    playback: PlaybackConfig = field(default_factory=PlaybackConfig)


# -----------------------------------------------------------------------------
# Unified Master Configuration
# -----------------------------------------------------------------------------


@dataclass
class CycloneConfig:
    data: DataConfig = field(default_factory=DataConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    train: TrainConfig = field(default_factory=TrainConfig)
    replay: ReplayConfig = field(default_factory=ReplayConfig)


# -----------------------------------------------------------------------------
# Loader Helpers
# -----------------------------------------------------------------------------


def _load_yaml(file_path: Path) -> Dict[str, Any]:
    if yaml is None or not file_path.is_file():
        return {}
    with open(file_path, "r", encoding="utf-8") as f:
        content = yaml.safe_load(f)
        return content if isinstance(content, dict) else {}


def _populate_dataclass(dc_cls: type, data: Dict[str, Any]) -> Any:
    """Recursively populates a dataclass from a dict with type-safe nested resolution."""
    if not isinstance(data, dict):
        return dc_cls()
    fields_dict = getattr(dc_cls, "__dataclass_fields__", {})
    init_kwargs = {}
    for key, val in data.items():
        if key in fields_dict:
            field_type = fields_dict[key].type
            if hasattr(field_type, "__dataclass_fields__") and isinstance(val, dict):
                init_kwargs[key] = _populate_dataclass(field_type, val)
            else:
                init_kwargs[key] = val
    return dc_cls(**init_kwargs)


def get_default_config_dir() -> Path:
    """Returns the default configuration directory path."""
    return Path(__file__).resolve().parent


def load_config(config_dir: Optional[str | Path] = None) -> CycloneConfig:
    """Loads and returns the unified typed CycloneConfig from YAML files."""
    base_dir = Path(config_dir) if config_dir else get_default_config_dir()

    data_dict = _load_yaml(base_dir / "data.yaml")
    model_dict = _load_yaml(base_dir / "model.yaml")
    train_dict = _load_yaml(base_dir / "train.yaml")
    replay_dict = _load_yaml(base_dir / "replay.yaml")

    # Construct nested dataclasses with overrides
    data_cfg = _populate_data_config(data_dict)
    model_cfg = _populate_model_config(model_dict)
    train_cfg = _populate_train_config(train_dict)
    replay_cfg = _populate_replay_config(replay_dict)

    return CycloneConfig(
        data=data_cfg,
        model=model_cfg,
        train=train_cfg,
        replay=replay_cfg,
    )


def _populate_data_config(d: Dict[str, Any]) -> DataConfig:
    sat_d = d.get("satellite", {})
    norm_d = sat_d.get("normalization", {})
    norm = NormalizationConfig(**{k: v for k, v in norm_d.items() if hasattr(NormalizationConfig, k)})
    sat_kwargs = {k: v for k, v in sat_d.items() if k != "normalization" and hasattr(SatelliteConfig, k)}
    sat = SatelliteConfig(normalization=norm, **sat_kwargs)

    env_d = d.get("environmental", {})
    env = EnvironmentalConfig(**{k: v for k, v in env_d.items() if hasattr(EnvironmentalConfig, k)})

    trk_d = d.get("track", {})
    trk = TrackConfig(**{k: v for k, v in trk_d.items() if hasattr(TrackConfig, k)})

    pth_d = d.get("paths", {})
    pth = DataPathsConfig(**{k: v for k, v in pth_d.items() if hasattr(DataPathsConfig, k)})

    return DataConfig(
        basin=d.get("basin", "North Indian Ocean"),
        satellite=sat,
        environmental=env,
        track=trk,
        paths=pth,
    )


def _populate_model_config(d: Dict[str, Any]) -> ModelConfig:
    t0_d = d.get("tier0", {})
    t0_rules_d = t0_d.get("stage_rules", {})
    t0_rules = Tier0StageRulesConfig(**{k: v for k, v in t0_rules_d.items() if hasattr(Tier0StageRulesConfig, k)})
    t0_trk_d = t0_d.get("track_persistence", {})
    t0_trk = Tier0TrackConfig(**{k: v for k, v in t0_trk_d.items() if hasattr(Tier0TrackConfig, k)})
    t0_cone_d = t0_d.get("parametric_cone", {})
    t0_cone = Tier0ParametricConeConfig(**{k: v for k, v in t0_cone_d.items() if hasattr(Tier0ParametricConeConfig, k)})
    t0 = Tier0Config(
        detection_threshold_wind_kt=t0_d.get("detection_threshold_wind_kt", 17.0),
        stage_rules=t0_rules,
        track_persistence=t0_trk,
        parametric_cone=t0_cone,
    )

    t1_d = d.get("tier1", {})
    img_d = t1_d.get("image_branch", {})
    img = ImageBranchConfig(**{k: v for k, v in img_d.items() if hasattr(ImageBranchConfig, k)})
    env_d = t1_d.get("env_branch", {})
    env = EnvBranchConfig(**{k: v for k, v in env_d.items() if hasattr(EnvBranchConfig, k)})
    trk_d = t1_d.get("track_branch", {})
    trk = TrackBranchConfig(**{k: v for k, v in trk_d.items() if hasattr(TrackBranchConfig, k)})
    trunk_d = t1_d.get("fusion_trunk", {})
    trunk = FusionTrunkConfig(**{k: v for k, v in trunk_d.items() if hasattr(FusionTrunkConfig, k)})
    heads_d = t1_d.get("heads", {})
    heads = HeadsConfig(**{k: v for k, v in heads_d.items() if hasattr(HeadsConfig, k)})
    t1 = Tier1Config(
        image_branch=img,
        env_branch=env,
        track_branch=trk,
        fusion_trunk=trunk,
        heads=heads,
    )

    cg_d = d.get("confidence_gates", {})
    cg = ConfidenceGatesConfig(**{k: v for k, v in cg_d.items() if hasattr(ConfidenceGatesConfig, k)})

    return ModelConfig(
        model_name=d.get("model_name", "chakravyuh-fusion-net"),
        model_version=d.get("model_version", "0.1.0"),
        device=d.get("device", "auto"),
        tier0=t0,
        tier1=t1,
        confidence_gates=cg,
    )


def _populate_train_config(d: Dict[str, Any]) -> TrainConfig:
    opt_d = d.get("optimization", {})
    opt = OptimizationConfig(**{k: v for k, v in opt_d.items() if hasattr(OptimizationConfig, k)})

    sched_d = d.get("scheduler", {})
    sched = SchedulerConfig(**{k: v for k, v in sched_d.items() if hasattr(SchedulerConfig, k)})

    loss_d = d.get("loss_weights", {})
    loss = LossWeightsConfig(**{k: v for k, v in loss_d.items() if hasattr(LossWeightsConfig, k)})

    aug_d = d.get("augmentation", {})
    aug = AugmentationConfig(**{k: v for k, v in aug_d.items() if hasattr(AugmentationConfig, k)})

    val_d = d.get("validation", {})
    val = ValidationConfig(**{k: v for k, v in val_d.items() if hasattr(ValidationConfig, k)})

    return TrainConfig(
        experiment_name=d.get("experiment_name", "cyclone_brain_v1"),
        output_dir=d.get("output_dir", "ml/cyclone/checkpoints"),
        seed=d.get("seed", 42),
        num_workers=d.get("num_workers", 4),
        optimization=opt,
        scheduler=sched,
        loss_weights=loss,
        augmentation=aug,
        validation=val,
    )


def _populate_replay_config(d: Dict[str, Any]) -> ReplayConfig:
    pb_d = d.get("playback", {})
    pb = PlaybackConfig(**{k: v for k, v in pb_d.items() if hasattr(PlaybackConfig, k)})

    return ReplayConfig(
        default_storm_id=d.get("default_storm_id", "CYC-2020-BAY-001"),
        default_storm_name=d.get("default_storm_name", "Amphan"),
        basin=d.get("basin", "North Indian Ocean"),
        storms=d.get("storms", {}),
        playback=pb,
    )


__all__ = [
    "CycloneConfig",
    "DataConfig",
    "ModelConfig",
    "TrainConfig",
    "ReplayConfig",
    "load_config",
    "get_default_config_dir",
]
