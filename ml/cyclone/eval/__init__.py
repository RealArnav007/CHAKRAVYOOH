"""Evaluation suite: metrics, testing harnesses, EDA, and baseline benchmarks."""

from ml.cyclone.eval.evaluate import evaluate_model, generate_baseline_report, tier0_predict
from ml.cyclone.eval.metrics import (
    classification_metrics,
    cone_coverage,
    expected_calibration_error,
    intensity_metrics,
    track_error_km,
)

__all__ = [
    "track_error_km",
    "intensity_metrics",
    "classification_metrics",
    "expected_calibration_error",
    "cone_coverage",
    "evaluate_model",
    "tier0_predict",
    "generate_baseline_report",
]
