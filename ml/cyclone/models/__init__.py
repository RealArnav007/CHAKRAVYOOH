"""Model implementations: Tier-0 baselines and Tier-1 multi-modal neural network."""

from ml.cyclone.models.baseline_classify import classify
from ml.cyclone.models.baseline_identify import identify
from ml.cyclone.models.baseline_intensity import intensity
from ml.cyclone.models.baseline_track import (
    cliper_forecast,
    parametric_cone,
    persistence_forecast,
    predict_track,
)
from ml.cyclone.models.calibration import ModelCalibrator, TemperatureScaler, VarianceRecalibrator
from ml.cyclone.models.env_branch import EnvBranch
from ml.cyclone.models.fusion_net import FusionNet
from ml.cyclone.models.heads import (
    DEFAULT_TRACK_HORIZONS,
    DetectionHead,
    DetectionModel,
    IntensityHead,
    IntensityModel,
    StageClassificationHead,
    StageHead,
    StageModel,
    TrackHead,
    TrackModel,
)
from ml.cyclone.models.image_branch import ImageBranch
from ml.cyclone.models.track_branch import TrackBranch
from ml.cyclone.models.uncertainty import (
    KM_PER_DEG_LAT,
    monte_carlo_dropout_predict,
    predict_cone_radii,
)

__all__ = [
    "identify",
    "classify",
    "intensity",
    "predict_track",
    "persistence_forecast",
    "cliper_forecast",
    "parametric_cone",
    "ImageBranch",
    "EnvBranch",
    "TrackBranch",
    "FusionNet",
    "DetectionHead",
    "DetectionModel",
    "IntensityHead",
    "IntensityModel",
    "StageClassificationHead",
    "StageHead",
    "StageModel",
    "TrackHead",
    "TrackModel",
    "DEFAULT_TRACK_HORIZONS",
    "TemperatureScaler",
    "VarianceRecalibrator",
    "ModelCalibrator",
    "predict_cone_radii",
    "monte_carlo_dropout_predict",
    "KM_PER_DEG_LAT",
]
