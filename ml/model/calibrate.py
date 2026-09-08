"""
Project Pukar - Severity Head Probability Calibration & Reliability Engine
==========================================================================

Overview:
---------
Calibrates the multi-task student classifier's severity output distribution using
Temperature Scaling so that the emitted `confidence` metric is trustworthy on edge devices.

Why Temperature Scaling Calibration?
------------------------------------
1. Overconfidence Problem:
   - Modern neural networks with softmax cross-entropy outputs produce uncalibrated,
     overconfident probabilities (e.g. predicting 98% confidence on an ambiguous disaster message
     when true empirical accuracy is only 75%).
2. Tactical Dispatch Impact:
   - In Project Pukar's emergency mesh triage, confidence directly informs human responder dispatch
     priority. Overconfident false alarms degrade responder trust and waste rescue bandwidth.
3. Zero Computation Overhead on Mobile CPU:
   - Temperature scaling introduces exactly 1 scalar parameter T > 0, scaling logits before softmax
     without changing model accuracy, argmax predictions, or latency (< 0.01 ms).

Evaluation Metrics:
-------------------
- Negative Log-Likelihood (NLL): Cross-entropy loss on validation targets.
- Expected Calibration Error (ECE): Weighted average absolute difference between predicted
  confidence and empirical accuracy across confidence bins.

Artifacts:
----------
Saves calibrated temperature and diagnostic stats to ml/model/artifacts/calibration.json.
"""

import argparse
import datetime
import json
import logging
import sys
from pathlib import Path
from typing import Any

# Ensure repo root is on sys.path for direct CLI invocations
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy.optimize import minimize_scalar  # noqa: E402

from ml.model.train import prepare_dataset_arrays  # noqa: E402
from ml.tokenizer.tokenizer import CrisisTokenizer  # noqa: E402
from services.backend.src.ml.contracts import Severity  # noqa: E402
from services.backend.src.ml.regex_engine import RegexEngine  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("pukar.calibrate")

DEFAULT_MODEL_PATH = Path("ml/model/artifacts/student_fp32.keras")
DEFAULT_LEGACY_MODEL_PATH = Path("ml/model/pukar_model.keras")
DEFAULT_VAL_PATH = Path("ml/datasets/processed/val.parquet")
DEFAULT_VOCAB_PATH = Path("ml/tokenizer/vocab.json")
DEFAULT_CALIBRATION_PATH = Path("ml/model/artifacts/calibration.json")

SEVERITY_ORDER = [Severity.INFO.value, Severity.WARN.value, Severity.CRITICAL.value]


def apply_temperature(
    probs_or_logits: np.ndarray,
    temperature: float = 1.0,
    is_logits: bool = False,
    eps: float = 1e-7,
) -> np.ndarray:
    """
    Applies temperature scaling to probabilities or logits:
      p_cal = softmax(logits / T)

    Args:
        probs_or_logits: 1D or 2D array of class probabilities or unnormalized logits.
        temperature: Scalar temperature T > 0.
        is_logits: True if input is raw logits; False if input is softmax probabilities.
        eps: Small epsilon for log stability.

    Returns:
        Calibrated probability array of same shape, summing to 1.0 along the last axis.
    """
    arr = np.asarray(probs_or_logits, dtype=np.float64)
    single_sample = arr.ndim == 1
    if single_sample:
        arr = np.expand_dims(arr, axis=0)

    if temperature <= 0:
        raise ValueError(f"Temperature must be positive, got {temperature}")

    if np.isclose(temperature, 1.0) and not is_logits:
        # Normalize in case probabilities don't sum to exactly 1
        norm_p = arr / np.sum(arr, axis=-1, keepdims=True)
        return norm_p[0] if single_sample else norm_p

    if is_logits:
        scaled_logits = arr / temperature
    else:
        # Convert probabilities to log-probabilities (pseudo-logits)
        clipped_p = np.clip(arr, eps, 1.0)
        scaled_logits = np.log(clipped_p) / temperature

    # Numerically stable softmax
    exp_logits = np.exp(scaled_logits - np.max(scaled_logits, axis=-1, keepdims=True))
    calibrated_probs = exp_logits / np.sum(exp_logits, axis=-1, keepdims=True)

    return calibrated_probs[0] if single_sample else calibrated_probs


def load_calibration_temperature(
    calibration_path: str | Path = DEFAULT_CALIBRATION_PATH,
) -> float:
    """
    Loads calibrated temperature from JSON artifact with fallback to 1.0 if not found.
    """
    path = Path(calibration_path)
    if path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
                temp = float(data.get("temperature", 1.0))
                logger.info("Loaded calibrated temperature T=%.4f from %s", temp, path)
                return temp
        except Exception as e:
            logger.warning("Could not read calibration file '%s': %s. Using T=1.0.", path, e)
    else:
        logger.info("Calibration file '%s' not found. Using default T=1.0.", path)
    return 1.0


def compute_nll(
    probs: np.ndarray,
    labels: np.ndarray,
    eps: float = 1e-7,
) -> float:
    """
    Computes Negative Log-Likelihood (NLL) / Cross-Entropy loss.

    Args:
        probs: (N, K) array of predicted class probabilities.
        labels: (N,) array of integer true class indices or (N, K) one-hot array.
    """
    probs_clipped = np.clip(probs, eps, 1.0)
    if labels.ndim == 2:
        # One-hot labels
        loss_per_sample = -np.sum(labels * np.log(probs_clipped), axis=-1)
    else:
        # Integer labels
        n = len(labels)
        loss_per_sample = -np.log(probs_clipped[np.arange(n), labels])
    return float(np.mean(loss_per_sample))


def compute_ece(
    probs: np.ndarray,
    labels: np.ndarray,
    num_bins: int = 10,
) -> tuple[float, dict[str, Any]]:
    """
    Computes Expected Calibration Error (ECE) and Maximum Calibration Error (MCE).

    Args:
        probs: (N, K) array of predicted class probabilities.
        labels: (N,) integer class indices or (N, K) one-hot array.
        num_bins: Number of equal-width confidence bins (default: 10).

    Returns:
        Tuple of:
          - ece: float Expected Calibration Error.
          - stats: dictionary with per-bin accuracy, confidence, and sample counts.
    """
    probs = np.asarray(probs, dtype=np.float64)
    if labels.ndim == 2:
        true_indices = np.argmax(labels, axis=-1)
    else:
        true_indices = np.asarray(labels, dtype=np.int64)

    confidences = np.max(probs, axis=-1)
    predictions = np.argmax(probs, axis=-1)
    accuracies = (predictions == true_indices).astype(np.float64)

    num_samples = len(true_indices)
    bin_boundaries = np.linspace(0.0, 1.0, num_bins + 1)

    ece = 0.0
    max_ce = 0.0
    bin_details: list[dict[str, Any]] = []

    for i in range(num_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]

        if i == 0:
            in_bin = (confidences >= bin_lower) & (confidences <= bin_upper)
        else:
            in_bin = (confidences > bin_lower) & (confidences <= bin_upper)

        bin_size = int(np.sum(in_bin))
        if bin_size > 0:
            bin_acc = float(np.mean(accuracies[in_bin]))
            bin_conf = float(np.mean(confidences[in_bin]))
            bin_error = abs(bin_acc - bin_conf)

            ece += (bin_size / num_samples) * bin_error
            max_ce = max(max_ce, bin_error)

            bin_details.append({
                "bin_range": f"({bin_lower:.2f}, {bin_upper:.2f}]",
                "count": bin_size,
                "accuracy": round(bin_acc, 4),
                "confidence": round(bin_conf, 4),
                "error": round(bin_error, 4),
            })

    stats = {
        "ece": round(float(ece), 4),
        "mce": round(float(max_ce), 4),
        "num_samples": num_samples,
        "num_bins": num_bins,
        "bin_details": bin_details,
    }
    return float(ece), stats


def fit_temperature_calibration(
    model_path: str | Path = DEFAULT_MODEL_PATH,
    val_dataset_path: str | Path = DEFAULT_VAL_PATH,
    vocab_path: str | Path = DEFAULT_VOCAB_PATH,
    output_calibration_path: str | Path = DEFAULT_CALIBRATION_PATH,
    target_head: str = "severity",
    num_bins: int = 10,
) -> dict[str, Any]:
    """
    Fits optimal temperature on validation set to minimize NLL on the severity head,
    evaluates ECE before and after calibration, and persists results to JSON.

    Args:
        model_path: Path to trained Keras model.
        val_dataset_path: Path to val.parquet.
        vocab_path: Path to tokenizer vocab.json.
        output_calibration_path: Path to output calibration.json.
        target_head: Target head name ('severity').
        num_bins: Number of confidence bins for ECE evaluation.

    Returns:
        Dictionary containing calibrated temperature, NLL/ECE improvements, and report.
    """
    m_path = Path(model_path)
    if not m_path.exists():
        if DEFAULT_LEGACY_MODEL_PATH.exists():
            m_path = DEFAULT_LEGACY_MODEL_PATH
        else:
            raise FileNotFoundError(
                f"Model file not found at '{m_path}' or '{DEFAULT_LEGACY_MODEL_PATH}'. "
                "Run 'python -m ml.model.train' first."
            )

    val_path = Path(val_dataset_path)
    if not val_path.exists():
        raise FileNotFoundError(f"Validation dataset not found at '{val_path}'")

    import tensorflow as tf

    logger.info("Loading student model from %s...", m_path)
    model = tf.keras.models.load_model(str(m_path), compile=False)

    tokenizer = CrisisTokenizer()
    tokenizer.load_vocab(vocab_path)
    regex_engine = RegexEngine()

    df_val = pd.read_parquet(val_path)
    val_data = prepare_dataset_arrays(df_val, tokenizer, regex_engine)

    # 1. Forward Pass to extract raw uncalibrated probabilities
    preds = model(
        {"token_ids": val_data["token_ids"], "aux_features": val_data["aux_features"]},
        training=False,
    )
    raw_probs = preds[target_head].numpy()
    labels = val_data["y_sev_hard"] if target_head == "severity" else val_data["y_cat_hard"]

    # 2. Baseline Metrics (T = 1.0)
    nll_before = compute_nll(raw_probs, labels)
    ece_before, ece_stats_before = compute_ece(raw_probs, labels, num_bins=num_bins)

    # 3. Optimization: Minimize NLL with respect to scalar Temperature T
    def nll_objective(temp: float) -> float:
        cal_p = apply_temperature(raw_probs, temperature=temp, is_logits=False)
        return compute_nll(cal_p, labels)

    opt_result = minimize_scalar(
        nll_objective,
        bounds=(0.1, 10.0),
        method="bounded",
        options={"xatol": 1e-4, "maxiter": 500},
    )
    optimal_temperature = float(opt_result.x)

    # 4. Calibrated Metrics (T = optimal_temperature)
    calibrated_probs = apply_temperature(raw_probs, temperature=optimal_temperature, is_logits=False)
    nll_after = compute_nll(calibrated_probs, labels)
    ece_after, ece_stats_after = compute_ece(calibrated_probs, labels, num_bins=num_bins)

    ece_reduction_pct = 0.0
    if ece_before > 0:
        ece_reduction_pct = ((ece_before - ece_after) / ece_before) * 100.0

    nll_reduction_pct = 0.0
    if nll_before > 0:
        nll_reduction_pct = ((nll_before - nll_after) / nll_before) * 100.0

    # 5. Build Result & Calibration JSON Payload
    calibration_payload: dict[str, Any] = {
        "temperature": round(optimal_temperature, 4),
        "target_head": target_head,
        "method": "temperature_scaling",
        "optimization_criterion": "negative_log_likelihood",
        "num_val_samples": len(df_val),
        "num_classes": raw_probs.shape[1],
        "nll": {
            "before": round(nll_before, 4),
            "after": round(nll_after, 4),
            "reduction_pct": round(nll_reduction_pct, 2),
        },
        "ece": {
            "before": round(ece_before, 4),
            "after": round(ece_after, 4),
            "reduction_pct": round(ece_reduction_pct, 2),
            "bins": num_bins,
        },
        "mce": {
            "before": ece_stats_before["mce"],
            "after": ece_stats_after["mce"],
        },
        "created_at": datetime.datetime.now(datetime.UTC).isoformat(),
    }

    out_file = Path(output_calibration_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(calibration_payload, f, indent=2)
    logger.info("Saved calibration artifact to %s", out_file)

    # 6. Print Reliability & Diagnostic Report
    print("\n" + "=" * 68)
    print(" PROJECT PUKAR — SEVERITY HEAD PROBABILITY CALIBRATION REPORT")
    print("=" * 68)
    print(f" Target Head:            {target_head.upper()}")
    print(f" Validation Samples:     {len(df_val)}")
    print(f" Optimal Temperature (T): {optimal_temperature:.4f}")
    print("-" * 68)
    print(" Calibration Metrics Comparison:")
    print(f"   - Negative Log-Likelihood (NLL): {nll_before:.4f}  →  {nll_after:.4f} ({nll_reduction_pct:+.2f}%)")
    print(f"   - Expected Calib Error (ECE):   {ece_before:.4f}  →  {ece_after:.4f} ({ece_reduction_pct:+.2f}%)")
    print(f"   - Maximum Calib Error (MCE):    {ece_stats_before['mce']:.4f}  →  {ece_stats_after['mce']:.4f}")
    print("-" * 68)
    print(f" Output Artifact:        {out_file}")
    if optimal_temperature > 1.0:
        print(" Diagnosis: Raw softmax was OVERCONFIDENT. Softened distributions with T > 1.0.")
    elif optimal_temperature < 1.0:
        print(" Diagnosis: Raw softmax was UNDERCONFIDENT. Sharpened distributions with T < 1.0.")
    else:
        print(" Diagnosis: Model is already perfectly calibrated at T = 1.0.")
    print("=" * 68 + "\n")

    return calibration_payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Calibrate Pukar severity head probabilities.")
    parser.add_argument(
        "--model-path",
        type=str,
        default=str(DEFAULT_MODEL_PATH),
        help="Path to trained .keras model",
    )
    parser.add_argument(
        "--val-dataset",
        type=str,
        default=str(DEFAULT_VAL_PATH),
        help="Path to val.parquet dataset",
    )
    parser.add_argument(
        "--vocab-path",
        type=str,
        default=str(DEFAULT_VOCAB_PATH),
        help="Path to vocab.json",
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default=str(DEFAULT_CALIBRATION_PATH),
        help="Output path for calibration.json",
    )
    parser.add_argument(
        "--num-bins",
        type=int,
        default=10,
        help="Number of confidence bins for ECE calculation (default: 10)",
    )
    args = parser.parse_args()

    fit_temperature_calibration(
        model_path=args.model_path,
        val_dataset_path=args.val_dataset,
        vocab_path=args.vocab_path,
        output_calibration_path=args.output_path,
        num_bins=args.num_bins,
    )


if __name__ == "__main__":
    main()
