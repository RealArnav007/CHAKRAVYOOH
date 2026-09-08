"""Evaluation metrics for cyclone track forecasting, intensity estimation, classification, and calibration."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np

from ml.cyclone.preprocess.geo import haversine_distance_km

# -----------------------------------------------------------------------------
# 1. Track Forecasting Error Metrics
# -----------------------------------------------------------------------------


def track_error_km(
    pred_path: Sequence[dict[str, Any]] | Sequence[tuple[float, float]] | np.ndarray,
    true_path: Sequence[dict[str, Any]] | Sequence[tuple[float, float]] | np.ndarray,
    horizons: Sequence[int] | None = None,
) -> dict[str, Any]:
    """Computes great-circle track forecasting errors (in km) per horizon and overall mean.

    Args:
        pred_path: Predicted trajectory. Either:
            - List of dicts with 'lat', 'lon', and optional 't_plus_h'
            - List of (lat, lon) or (h, lat, lon) tuples
            - (N, 2) numpy array of [lat, lon]
        true_path: Ground truth trajectory in the same format.
        horizons: Optional list of forecast horizon hours [0, 6, 12, 24, 48, 72].

    Returns:
        Dict containing:
            - "errors_by_horizon": Dict[int, float] mapping horizon hour to error in km
            - "mean_error_km": Mean error across evaluated horizons
            - "max_error_km": Maximum error across evaluated horizons
    """
    pred_pts = _normalize_path_points(pred_path)
    true_pts = _normalize_path_points(true_path)

    n = min(len(pred_pts), len(true_pts))
    if n == 0:
        return {"errors_by_horizon": {}, "mean_error_km": 0.0, "max_error_km": 0.0}

    errors_by_horizon: dict[int, float] = {}
    error_list: list[float] = []

    for i in range(n):
        p_h, p_lat, p_lon = pred_pts[i]
        t_h, t_lat, t_lon = true_pts[i]

        h = (
            horizons[i]
            if (horizons is not None and i < len(horizons))
            else (p_h if p_h is not None else i)
        )
        err = haversine_distance_km(p_lat, p_lon, t_lat, t_lon)
        err = round(float(err), 2)

        errors_by_horizon[int(h)] = err
        error_list.append(err)

    mean_err = round(float(np.mean(error_list)), 2) if error_list else 0.0
    max_err = round(float(np.max(error_list)), 2) if error_list else 0.0

    return {
        "errors_by_horizon": errors_by_horizon,
        "mean_error_km": mean_err,
        "max_error_km": max_err,
    }


def _normalize_path_points(
    path: Sequence[dict[str, Any]] | Sequence[tuple[float, float]] | np.ndarray,
) -> list[tuple[int | None, float, float]]:
    """Helper to convert diverse path representations to standard List[(h, lat, lon)]."""
    normalized: list[tuple[int | None, float, float]] = []

    if isinstance(path, np.ndarray):
        for i in range(len(path)):
            row = path[i]
            if len(row) >= 3:
                normalized.append((int(row[0]), float(row[1]), float(row[2])))
            elif len(row) >= 2:
                normalized.append((None, float(row[0]), float(row[1])))
        return normalized

    for i, pt in enumerate(path):
        if isinstance(pt, dict):
            h = pt.get("t_plus_h", pt.get("horizon", pt.get("h", None)))
            lat = float(pt.get("lat", 0.0))
            lon = float(pt.get("lon", 0.0))
            normalized.append((int(h) if h is not None else None, lat, lon))
        elif isinstance(pt, (tuple, list)):
            if len(pt) >= 3:
                normalized.append((int(pt[0]), float(pt[1]), float(pt[2])))
            elif len(pt) >= 2:
                normalized.append((None, float(pt[0]), float(pt[1])))

    return normalized


# -----------------------------------------------------------------------------
# 2. Intensity Estimation Metrics
# -----------------------------------------------------------------------------


def intensity_metrics(
    pred_wind: Sequence[float] | np.ndarray,
    true_wind: Sequence[float] | np.ndarray,
    pred_pres: Sequence[float] | np.ndarray | None = None,
    true_pres: Sequence[float] | np.ndarray | None = None,
) -> dict[str, float]:
    """Computes MAE, RMSE, and bias for cyclone wind speed (kt) and central pressure (mb).

    Args:
        pred_wind: Predicted wind speeds in knots.
        true_wind: Ground truth wind speeds in knots.
        pred_pres: Optional predicted central pressures in mb.
        true_pres: Optional ground truth central pressures in mb.

    Returns:
        Dict with wind_mae_kt, wind_rmse_kt, wind_bias_kt, and optional pres_* metrics.
    """
    pw = np.asarray(pred_wind, dtype=np.float64)
    tw = np.asarray(true_wind, dtype=np.float64)

    # Filter out NaNs if any
    valid_mask_w = ~np.isnan(pw) & ~np.isnan(tw)
    if not np.any(valid_mask_w):
        return {
            "wind_mae_kt": 0.0,
            "wind_rmse_kt": 0.0,
            "wind_bias_kt": 0.0,
        }

    pw_valid = pw[valid_mask_w]
    tw_valid = tw[valid_mask_w]

    w_diff = pw_valid - tw_valid
    wind_mae = float(np.mean(np.abs(w_diff)))
    wind_rmse = float(np.sqrt(np.mean(w_diff**2)))
    wind_bias = float(np.mean(w_diff))

    results = {
        "wind_mae_kt": round(wind_mae, 2),
        "wind_rmse_kt": round(wind_rmse, 2),
        "wind_bias_kt": round(wind_bias, 2),
    }

    if pred_pres is not None and true_pres is not None:
        pp = np.asarray(pred_pres, dtype=np.float64)
        tp = np.asarray(true_pres, dtype=np.float64)
        valid_mask_p = ~np.isnan(pp) & ~np.isnan(tp)
        if np.any(valid_mask_p):
            pp_valid = pp[valid_mask_p]
            tp_valid = tp[valid_mask_p]
            p_diff = pp_valid - tp_valid
            results["pres_mae_mb"] = round(float(np.mean(np.abs(p_diff))), 2)
            results["pres_rmse_mb"] = round(float(np.sqrt(np.mean(p_diff**2))), 2)
            results["pres_bias_mb"] = round(float(np.mean(p_diff)), 2)

    return results


# -----------------------------------------------------------------------------
# 3. Classification & Identification Metrics
# -----------------------------------------------------------------------------


def classification_metrics(
    y_true: Sequence[Any] | np.ndarray,
    y_pred: Sequence[Any] | np.ndarray,
    y_prob: Sequence[Any] | np.ndarray | None = None,
    classes: Sequence[Any] | None = None,
) -> dict[str, Any]:
    """Computes accuracy, macro-F1, confusion matrix, and PR-AUC for discrete classification.

    Args:
        y_true: Ground truth class labels or integer indices.
        y_pred: Predicted class labels or integer indices.
        y_prob: Optional predicted probabilities. Shape (N,) for binary or (N, C) for multi-class.
        classes: Optional ordered list of unique class names/indices.

    Returns:
        Dict with accuracy, macro_f1, confusion_matrix, pr_auc, and per_class_f1.
    """
    yt = np.asarray(y_true)
    yp = np.asarray(y_pred)
    n = len(yt)

    if n == 0:
        return {
            "accuracy": 0.0,
            "macro_f1": 0.0,
            "pr_auc": 0.0,
            "confusion_matrix": [],
            "per_class_f1": {},
        }

    # Determine unique classes
    if classes is not None:
        unique_classes = list(classes)
    else:
        unique_classes = sorted(list(set(yt).union(set(yp))))

    class_to_idx = {c: i for i, c in enumerate(unique_classes)}
    n_classes = len(unique_classes)

    # Confusion matrix
    cm = np.zeros((n_classes, n_classes), dtype=int)
    for t_val, p_val in zip(yt, yp):
        if t_val in class_to_idx and p_val in class_to_idx:
            cm[class_to_idx[t_val], class_to_idx[p_val]] += 1

    # Accuracy
    accuracy = float(np.trace(cm) / n) if n > 0 else 0.0

    # Per-class precision, recall, F1
    per_class_f1: dict[str, float] = {}
    f1_list: list[float] = []

    for i, c in enumerate(unique_classes):
        tp = cm[i, i]
        fp = np.sum(cm[:, i]) - tp
        fn = np.sum(cm[i, :]) - tp

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2.0 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

        str_c = str(c)
        per_class_f1[str_c] = round(float(f1), 4)
        f1_list.append(f1)

    macro_f1 = float(np.mean(f1_list)) if f1_list else 0.0

    # PR-AUC Calculation
    pr_auc_val: float | None = None
    if y_prob is not None:
        pr_auc_val = _compute_pr_auc(yt, y_prob, unique_classes)

    return {
        "accuracy": round(accuracy, 4),
        "macro_f1": round(macro_f1, 4),
        "pr_auc": round(pr_auc_val, 4) if pr_auc_val is not None else None,
        "confusion_matrix": cm.tolist(),
        "classes": [str(c) for c in unique_classes],
        "per_class_f1": per_class_f1,
    }


def _compute_pr_auc(
    y_true: np.ndarray,
    y_prob: Sequence[Any] | np.ndarray,
    unique_classes: list[Any],
) -> float:
    """Computes Precision-Recall AUC (binary or macro one-vs-rest for multi-class)."""
    probs = np.asarray(y_prob)

    # Binary case (probs 1D or 2D with 2 columns)
    if len(unique_classes) <= 2:
        if probs.ndim == 2 and probs.shape[1] >= 2:
            scores = probs[:, 1]
        else:
            scores = probs.squeeze()

        # Binary labels: 1 if matches second class or 1/True, else 0
        pos_class = unique_classes[-1]
        binary_y = np.array(
            [1 if val == pos_class or val in [1, True, "1"] else 0 for val in y_true]
        )

        return _binary_pr_auc(binary_y, scores)

    # Multi-class one-vs-rest macro PR-AUC
    aucs: list[float] = []
    for idx, c in enumerate(unique_classes):
        binary_y = np.array([1 if val == c else 0 for val in y_true])
        if probs.ndim == 2 and idx < probs.shape[1]:
            scores = probs[:, idx]
        else:
            continue

        if np.sum(binary_y) > 0:
            aucs.append(_binary_pr_auc(binary_y, scores))

    return float(np.mean(aucs)) if aucs else 0.0


def _binary_pr_auc(y_true: np.ndarray, y_scores: np.ndarray) -> float:
    """Computes binary Precision-Recall AUC via trapezoidal integration over thresholds."""
    if len(y_true) == 0 or np.sum(y_true) == 0:
        return 0.0

    n_pos = np.sum(y_true)
    sorted_indices = np.argsort(-y_scores)
    y_sorted = y_true[sorted_indices]

    tps = np.cumsum(y_sorted)
    fps = np.cumsum(1 - y_sorted)

    recalls = tps / n_pos
    precisions = tps / (tps + fps)

    # Prepend recall=0, precision=1 for standard PR curve
    recalls = np.concatenate(([0.0], recalls))
    precisions = np.concatenate(([1.0], precisions))

    # Trapezoidal integration
    auc = np.sum((recalls[1:] - recalls[:-1]) * precisions[1:])
    return float(np.clip(auc, 0.0, 1.0))


# -----------------------------------------------------------------------------
# 4. Calibration & Uncertainty Metrics
# -----------------------------------------------------------------------------


def expected_calibration_error(
    y_true: Sequence[Any] | np.ndarray,
    y_prob: Sequence[Any] | np.ndarray,
    n_bins: int = 10,
) -> float:
    """Computes Expected Calibration Error (ECE) measuring confidence calibration quality.

    Formula:
        ECE = sum_m (|B_m| / N) * |acc(B_m) - conf(B_m)|

    Args:
        y_true: Ground truth binary labels (0/1) or multi-class target indices.
        y_prob: Predicted confidence scores in [0, 1] or probability distribution (N, C).
        n_bins: Number of equal-width calibration bins in [0, 1] (default: 10).

    Returns:
        Float ECE score in [0.0, 1.0] where 0.0 represents perfect calibration.
    """
    yt = np.asarray(y_true)
    yp = np.asarray(y_prob)
    n = len(yt)

    if n == 0:
        return 0.0

    # If multi-class matrix provided, use top confidence and correctness
    if yp.ndim == 2:
        confidences = np.max(yp, axis=1)
        preds = np.argmax(yp, axis=1)
        corrects = (preds == yt).astype(float)
    else:
        confidences = yp.squeeze()
        # Binary target alignment
        if set(np.unique(yt)).issubset({0, 1}):
            corrects = yt.astype(float)
        else:
            corrects = (yt == (confidences >= 0.5)).astype(float)

    bin_boundaries = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0

    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]

        if i == n_bins - 1:
            in_bin = (confidences >= bin_lower) & (confidences <= bin_upper)
        else:
            in_bin = (confidences >= bin_lower) & (confidences < bin_upper)

        bin_count = np.sum(in_bin)
        if bin_count > 0:
            bin_acc = np.mean(corrects[in_bin])
            bin_conf = np.mean(confidences[in_bin])
            ece += (bin_count / n) * abs(bin_acc - bin_conf)

    return round(float(ece), 4)


def cone_coverage(
    pred_cone: Sequence[float] | np.ndarray,
    pred_path: Sequence[dict[str, Any]] | Sequence[tuple[float, float]] | np.ndarray,
    true_path: Sequence[dict[str, Any]] | Sequence[tuple[float, float]] | np.ndarray,
) -> dict[str, Any]:
    """Computes parametric cone coverage percentage (% of horizons where true path lies within radius).

    Args:
        pred_cone: List or array of cone radii in km for each horizon.
        pred_path: Predicted trajectory coordinates.
        true_path: Ground truth trajectory coordinates.

    Returns:
        Dict containing:
            - "coverage_pct": Percentage (0.0 to 100.0) of valid horizons inside cone
            - "inside_count": Number of horizons where error <= cone radius
            - "total_count": Total number of evaluated horizons
            - "inside_by_horizon": Dict[int, bool] indicating inclusion per horizon
    """
    pred_pts = _normalize_path_points(pred_path)
    true_pts = _normalize_path_points(true_path)
    cone_arr = np.asarray(pred_cone, dtype=np.float64)

    n = min(len(pred_pts), len(true_pts), len(cone_arr))
    if n == 0:
        return {
            "coverage_pct": 0.0,
            "inside_count": 0,
            "total_count": 0,
            "inside_by_horizon": {},
        }

    inside_count = 0
    inside_by_horizon: dict[int, bool] = {}

    for i in range(n):
        p_h, p_lat, p_lon = pred_pts[i]
        t_h, t_lat, t_lon = true_pts[i]
        r_km = float(cone_arr[i])

        dist_km = float(haversine_distance_km(p_lat, p_lon, t_lat, t_lon))
        is_inside = dist_km <= r_km

        if is_inside:
            inside_count += 1

        h_key = p_h if p_h is not None else i
        inside_by_horizon[int(h_key)] = is_inside

    coverage_pct = round((inside_count / n) * 100.0, 2)

    return {
        "coverage_pct": coverage_pct,
        "inside_count": inside_count,
        "total_count": n,
        "inside_by_horizon": inside_by_horizon,
    }


__all__ = [
    "track_error_km",
    "intensity_metrics",
    "classification_metrics",
    "expected_calibration_error",
    "cone_coverage",
]
