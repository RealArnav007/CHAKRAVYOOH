"""Unit tests with hand-checkable tiny examples for evaluation metrics suite."""

import numpy as np
import pytest

from ml.cyclone.eval.metrics import (
    classification_metrics,
    cone_coverage,
    expected_calibration_error,
    intensity_metrics,
    track_error_km,
)


# -----------------------------------------------------------------------------
# 1. Track Forecasting Error Tests
# -----------------------------------------------------------------------------


def test_track_error_km_exact_and_shifted():
    """Asserts track_error_km gives 0 for identical paths and correct haversine for known delta."""
    # Exact match at Equator
    pred_path = [{"t_plus_h": 0, "lat": 0.0, "lon": 80.0}, {"t_plus_h": 12, "lat": 2.0, "lon": 82.0}]
    true_path = [{"t_plus_h": 0, "lat": 0.0, "lon": 80.0}, {"t_plus_h": 12, "lat": 2.0, "lon": 82.0}]

    res_zero = track_error_km(pred_path, true_path)
    assert res_zero["mean_error_km"] == 0.0
    assert res_zero["errors_by_horizon"][0] == 0.0
    assert res_zero["errors_by_horizon"][12] == 0.0

    # 1 degree latitude shift ~ 111.19 km
    shifted_pred = [{"t_plus_h": 6, "lat": 1.0, "lon": 0.0}]
    shifted_true = [{"t_plus_h": 6, "lat": 0.0, "lon": 0.0}]

    res_shift = track_error_km(shifted_pred, shifted_true)
    assert 111.0 <= res_shift["errors_by_horizon"][6] <= 112.0
    assert 111.0 <= res_shift["mean_error_km"] <= 112.0


# -----------------------------------------------------------------------------
# 2. Intensity Metrics Tests
# -----------------------------------------------------------------------------


def test_intensity_metrics_hand_checkable():
    """Asserts intensity_metrics computes correct MAE and RMSE for simple hand-checkable numbers."""
    pred_w = [30.0, 50.0, 80.0]
    true_w = [30.0, 40.0, 70.0]
    # diffs = [0, 10, 10] -> MAE = 20/3 = 6.67, RMSE = sqrt(200/3) = sqrt(66.666) = 8.16

    pred_p = [1000.0, 980.0, 950.0]
    true_p = [996.0, 980.0, 956.0]
    # diffs = [4, 0, -6] -> MAE = 10/3 = 3.33, RMSE = sqrt(52/3) = sqrt(17.33) = 4.16

    res = intensity_metrics(pred_wind=pred_w, true_wind=true_w, pred_pres=pred_p, true_pres=true_p)

    assert pytest.approx(res["wind_mae_kt"], abs=0.05) == 6.67
    assert pytest.approx(res["wind_rmse_kt"], abs=0.05) == 8.16
    assert pytest.approx(res["wind_bias_kt"], abs=0.05) == 6.67

    assert pytest.approx(res["pres_mae_mb"], abs=0.05) == 3.33
    assert pytest.approx(res["pres_rmse_mb"], abs=0.05) == 4.16
    assert pytest.approx(res["pres_bias_mb"], abs=0.05) == -0.67


# -----------------------------------------------------------------------------
# 3. Classification Metrics Tests
# -----------------------------------------------------------------------------


def test_classification_metrics_binary_and_multiclass():
    """Asserts classification_metrics computes accuracy, F1, and PR-AUC properly."""
    # Binary case
    y_true = [1, 1, 0, 0]
    y_pred = [1, 0, 0, 0]
    # 3 correct out of 4 -> Acc = 0.75
    # Class 1: TP=1, FP=0, FN=1 -> Prec=1.0, Rec=0.5 -> F1 = 2/3 = 0.667
    # Class 0: TP=2, FP=1, FN=0 -> Prec=2/3, Rec=1.0 -> F1 = 0.800
    # Macro F1 = (0.667 + 0.800) / 2 = 0.7333

    y_prob = [0.9, 0.4, 0.1, 0.2]
    res = classification_metrics(y_true, y_pred, y_prob=y_prob)

    assert res["accuracy"] == 0.75
    assert pytest.approx(res["macro_f1"], abs=0.01) == 0.7333
    assert 0.0 <= res["pr_auc"] <= 1.0
    assert res["confusion_matrix"] == [[2, 0], [1, 1]]


# -----------------------------------------------------------------------------
# 4. Calibration & ECE Tests
# -----------------------------------------------------------------------------


def test_expected_calibration_error_perfect_and_miscalibrated():
    """Asserts ECE is ~0 for perfectly calibrated confidence and higher for overconfident models."""
    # Perfectly calibrated case: 10 samples with conf 0.8 of which 8 are positive (80% acc)
    # and 10 samples with conf 0.2 of which 2 are positive (20% acc)
    y_true_perf = [1] * 8 + [0] * 2 + [1] * 2 + [0] * 8
    y_prob_perf = [0.8] * 10 + [0.2] * 10

    ece_perf = expected_calibration_error(y_true_perf, y_prob_perf, n_bins=10)
    assert ece_perf <= 0.05

    # Completely overconfident case: confidence 0.99 for all, but all are 0 (0% acc)
    y_true_bad = [0] * 10
    y_prob_bad = [0.99] * 10

    ece_bad = expected_calibration_error(y_true_bad, y_prob_bad, n_bins=10)
    assert ece_bad >= 0.90


# -----------------------------------------------------------------------------
# 5. Cone Coverage Tests
# -----------------------------------------------------------------------------


def test_cone_coverage_inside_and_outside():
    """Asserts cone_coverage correctly identifies points inside and outside cone radius."""
    # Point 1: 0 km error, cone radius 0 km -> Inside
    # Point 2: 50 km error, cone radius 78 km -> Inside
    # Point 3: 150 km error, cone radius 100 km -> Outside
    pred_path = [
        {"t_plus_h": 0, "lat": 10.0, "lon": 85.0},
        {"t_plus_h": 24, "lat": 12.0, "lon": 85.0},
        {"t_plus_h": 48, "lat": 15.0, "lon": 85.0},
    ]
    true_path = [
        {"t_plus_h": 0, "lat": 10.0, "lon": 85.0},      # dist = 0 km
        {"t_plus_h": 24, "lat": 12.4, "lon": 85.0},     # 0.4 deg lat ~ 44.4 km <= 78 km
        {"t_plus_h": 48, "lat": 17.0, "lon": 85.0},     # 2.0 deg lat ~ 222.4 km > 100 km
    ]
    pred_cone = [0.0, 78.0, 100.0]

    cov = cone_coverage(pred_cone, pred_path, true_path)
    assert cov["inside_count"] == 2
    assert cov["total_count"] == 3
    assert pytest.approx(cov["coverage_pct"], abs=0.1) == 66.67
    assert cov["inside_by_horizon"][0] is True
    assert cov["inside_by_horizon"][24] is True
    assert cov["inside_by_horizon"][48] is False
