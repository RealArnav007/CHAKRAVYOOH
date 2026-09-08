"""Unit tests for temperature scaling, variance recalibration, and reliability diagrams."""

from __future__ import annotations

import json
from pathlib import Path
import pytest
import numpy as np
import torch

from ml.cyclone.eval.metrics import cone_coverage, expected_calibration_error
from ml.cyclone.eval.reliability import (
    compute_reliability_curve,
    plot_calibration_dashboard,
    plot_cone_coverage_curve,
    plot_reliability_diagram,
)
from ml.cyclone.models.calibration import (
    ModelCalibrator,
    TemperatureScaler,
    VarianceRecalibrator,
)


def test_temperature_scaler_multiclass() -> None:
    """Tests that TemperatureScaler optimizes T to reduce ECE on overconfident logits."""
    torch.manual_seed(42)
    np.random.seed(42)

    # Synthetic overconfident logits for 4 classes
    n_samples = 200
    n_classes = 4
    true_labels = np.random.randint(0, n_classes, size=n_samples)

    # Artificially scale logits by 5.0 to create overconfidence
    logits = np.random.randn(n_samples, n_classes) * 5.0
    for i in range(n_samples):
        # 60% accuracy but 99% confidence
        if np.random.rand() < 0.6:
            logits[i, true_labels[i]] += 8.0

    exp_s = np.exp(logits - np.max(logits, axis=1, keepdims=True))
    probs_uncal = exp_s / np.sum(exp_s, axis=1, keepdims=True)
    ece_uncal = expected_calibration_error(true_labels, probs_uncal)

    scaler = TemperatureScaler(initial_temp=1.0)
    fitted_t = scaler.fit(logits, true_labels, is_binary=False)
    assert fitted_t > 1.0  # Overconfident logits should learn T > 1.0

    probs_cal = scaler.predict_proba(logits, is_binary=False)
    assert probs_cal.shape == (n_samples, n_classes)
    assert np.allclose(np.sum(probs_cal, axis=1), 1.0)

    ece_cal = expected_calibration_error(true_labels, probs_cal)
    assert ece_cal < ece_uncal  # Calibrated ECE should improve


def test_temperature_scaler_binary() -> None:
    """Tests TemperatureScaler on binary classification logits."""
    n_samples = 150
    true_labels = np.random.choice([0, 1], size=n_samples)
    logits = np.random.randn(n_samples) * 3.0

    scaler = TemperatureScaler(initial_temp=1.0)
    fitted_t = scaler.fit(logits, true_labels, is_binary=True)
    assert fitted_t > 0.0

    probs = scaler.predict_proba(logits, is_binary=True)
    assert len(probs) == n_samples
    assert np.all(probs >= 0.0) and np.all(probs <= 1.0)


def test_variance_recalibrator_target_coverage() -> None:
    """Tests that VarianceRecalibrator adjusts cone radii to reach target 95% coverage."""
    np.random.seed(42)

    # Simulated tracking errors: Rayleigh / Half-Normal errors
    raw_errors = np.random.exponential(scale=100.0, size=200)
    # Under-estimated raw cone radii (leading to low coverage ~60%)
    raw_radii = np.ones(200) * 80.0
    horizons = np.random.choice([6, 12, 24, 48, 72], size=200)

    recal = VarianceRecalibrator(target_coverage=0.95)
    fit_summary = recal.fit(raw_errors, raw_radii, horizons=horizons, target_coverage=0.95)

    assert fit_summary["global_multiplier"] > 1.0

    # Recalibrate radii
    recal_radii = [recal.recalibrate_radii([0.0, r])[1] for r in raw_radii]
    cov_after = np.mean(raw_errors <= recal_radii)

    # Empirical coverage should be close to nominal 95% target
    assert cov_after >= 0.90


def test_model_calibrator_serialization(tmp_path: Path) -> None:
    """Tests serialization and deserialization of ModelCalibrator."""
    calib = ModelCalibrator()
    calib.detection_scaler.temperature.data.fill_(1.85)
    calib.stage_scaler.temperature.data.fill_(2.10)
    calib.cone_recalibrator.global_multiplier = 1.45

    json_path = tmp_path / "calibration.json"
    calib.save(json_path)
    assert json_path.is_file()

    new_calib = ModelCalibrator()
    new_calib.load(json_path)

    assert float(new_calib.detection_scaler.temperature.item()) == pytest.approx(1.85, abs=1e-3)
    assert float(new_calib.stage_scaler.temperature.item()) == pytest.approx(2.10, abs=1e-3)
    assert new_calib.cone_recalibrator.global_multiplier == pytest.approx(1.45, abs=1e-3)


def test_reliability_diagram_generation(tmp_path: Path) -> None:
    """Tests reliability curve computation and figure plotting."""
    y_true = np.random.choice([0, 1], size=100)
    y_prob_pre = np.random.uniform(0, 1, size=100)
    y_prob_post = np.random.uniform(0, 1, size=100)

    confs, accs, counts = compute_reliability_curve(y_true, y_prob_pre, n_bins=10)
    assert len(confs) == 10
    assert len(accs) == 10
    assert np.sum(counts) == 100

    out_fig = tmp_path / "test_reliability.png"
    ece_pre, ece_post = plot_reliability_diagram(y_true, y_prob_pre, y_prob_post, "Test Task", out_fig)
    assert out_fig.is_file()
    assert ece_pre >= 0.0
    assert ece_post >= 0.0
