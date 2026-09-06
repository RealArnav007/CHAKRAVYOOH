"""
Project Pukar - Comprehensive Model Evaluation, Robustness & Error Analysis
===========================================================================

Overview:
---------
Evaluates the multi-task student model (pukar_multitask_crisis_net) on the holdout
test dataset (ml/datasets/processed/test.parquet), producing:
  1. Detailed Multi-Task Performance Metrics:
     - Severity & Category Macro-F1, Accuracy, and per-class Precision/Recall/F1
     - Full 3x3 Severity and 5x5 Category Confusion Matrices
  2. Granular Language Slices:
     - Disaggregated performance tables for English (en), Hindi (hi), and Hinglish (hinglish)
     - Automated detection & flagging of any language slice underperforming the mean by > 5 F1 points
  3. Real-World Robustness Stress Probes:
     - Simulates harsh edge deployment conditions:
       a. Typo Perturbation (keyboard slips / OCR noise)
       b. Vowel Dropping (informal SMS/Hinglish chat shorthand)
       c. Truncation (network packet fragmentation / SMS character limits)
     - Measures empirical Macro-F1 degradation against clean baseline
  4. High-Confidence Error Analysis:
     - Extracts and dumps the worst misclassifications to ml/eval/errors.csv
  5. Executive Markdown Report:
     - Emits comprehensive report to ml/eval/EVAL_REPORT.md
"""

import argparse
import datetime
import logging
import random
import sys
from pathlib import Path
from typing import Any

# Ensure repo root is on sys.path for direct CLI invocations
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import tensorflow as tf  # noqa: E402
from sklearn.metrics import (  # noqa: E402
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

from ml.model.calibrate import apply_temperature, load_calibration_temperature  # noqa: E402
from ml.model.train import prepare_dataset_arrays  # noqa: E402
from ml.tokenizer.tokenizer import CrisisTokenizer  # noqa: E402
from services.backend.src.ml.contracts import Category, Severity  # noqa: E402
from services.backend.src.ml.regex_engine import RegexEngine  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("pukar.eval")

DEFAULT_TEST_PATH = Path("ml/datasets/processed/test.parquet")
DEFAULT_MODEL_PATH = Path("ml/model/artifacts/student_fp32.keras")
DEFAULT_LEGACY_MODEL_PATH = Path("ml/model/pukar_model.keras")
DEFAULT_VOCAB_PATH = Path("ml/tokenizer/vocab.json")
DEFAULT_CALIBRATION_PATH = Path("ml/model/artifacts/calibration.json")
DEFAULT_REPORT_PATH = Path("ml/eval/EVAL_REPORT.md")
DEFAULT_ERRORS_PATH = Path("ml/eval/errors.csv")

SEVERITY_CLASSES = [Severity.INFO.value, Severity.WARN.value, Severity.CRITICAL.value]
CATEGORY_CLASSES = [
    Category.RESCUE.value,
    Category.MEDICAL.value,
    Category.FIRE.value,
    Category.SHELTER.value,
    Category.OTHER.value,
]


# ==============================================================================
# Robustness Perturbation Helpers
# ==============================================================================

def inject_typos(text: str, typo_rate: float = 0.15, seed: int = 42) -> str:
    """
    Injects keyboard/character-level typos into words:
    - Random adjacent character swapping
    - Random character omission or replacement
    """
    rng = random.Random(seed + len(text))
    words = text.split()
    perturbed_words: list[str] = []

    for word in words:
        if len(word) > 3 and rng.random() < typo_rate:
            op = rng.choice(["swap", "drop", "replace"])
            chars = list(word)
            idx = rng.randint(1, len(chars) - 2)
            if op == "swap":
                chars[idx], chars[idx + 1] = chars[idx + 1], chars[idx]
            elif op == "drop":
                del chars[idx]
            elif op == "replace":
                chars[idx] = rng.choice("abcdefghijklmnopqrstuvwxyz")
            perturbed_words.append("".join(chars))
        else:
            perturbed_words.append(word)

    return " ".join(perturbed_words)


def drop_vowels(text: str, seed: int = 42) -> str:
    """
    Simulates Hindi/Hinglish chat shorthand by dropping non-initial vowels:
    e.g., 'paani me doob rahe hain' -> 'pni me db rhe hn'
    """
    rng = random.Random(seed + len(text))
    vowels = set("aeiouAEIOU\u0905\u0906\u0907\u0908\u0909\u090A\u090F\u0910\u0913\u0914")

    words = text.split()
    condensed_words: list[str] = []

    for word in words:
        if len(word) <= 2:
            condensed_words.append(word)
            continue

        first_char = word[0]
        rest = word[1:]
        # Retain first char, drop vowels from rest with 80% probability
        new_rest = "".join(
            c for c in rest if (c not in vowels or rng.random() > 0.8)
        )
        condensed_words.append(first_char + new_rest)

    return " ".join(condensed_words)


def truncate_text(text: str, ratio: float = 0.5) -> str:
    """
    Simulates SMS character limits or packet truncation by keeping only the first 50% of tokens.
    """
    tokens = text.split()
    if len(tokens) <= 2:
        return text
    keep_len = max(1, int(len(tokens) * ratio))
    return " ".join(tokens[:keep_len])


# ==============================================================================
# Inference & Metric Evaluation Engines
# ==============================================================================

def run_model_inference(
    model: tf.keras.Model,
    df: pd.DataFrame,
    tokenizer: CrisisTokenizer,
    regex_engine: RegexEngine,
    temperature: float = 1.0,
) -> dict[str, Any]:
    """
    Runs forward inference on a dataframe, returning predictions, probabilities, and confidences.
    """
    data = prepare_dataset_arrays(df, tokenizer, regex_engine)

    preds = model(
        {"token_ids": data["token_ids"], "aux_features": data["aux_features"]},
        training=False,
    )

    raw_sev_probs = preds["severity"].numpy()
    raw_cat_probs = preds["category"].numpy()

    # Apply temperature calibration to severity head
    cal_sev_probs = apply_temperature(raw_sev_probs, temperature=temperature, is_logits=False)

    sev_pred_idx = np.argmax(cal_sev_probs, axis=-1)
    cat_pred_idx = np.argmax(raw_cat_probs, axis=-1)

    sev_confidences = np.max(cal_sev_probs, axis=-1)
    cat_confidences = np.max(raw_cat_probs, axis=-1)

    sev_pred_labels = [SEVERITY_CLASSES[i] for i in sev_pred_idx]
    cat_pred_labels = [CATEGORY_CLASSES[i] for i in cat_pred_idx]

    sev_true_labels = [SEVERITY_CLASSES[i] for i in np.argmax(data["y_sev_hard"], axis=-1)]
    cat_true_labels = [CATEGORY_CLASSES[i] for i in np.argmax(data["y_cat_hard"], axis=-1)]

    return {
        "sev_true": sev_true_labels,
        "sev_pred": sev_pred_labels,
        "sev_probs": cal_sev_probs,
        "sev_conf": sev_confidences,
        "cat_true": cat_true_labels,
        "cat_pred": cat_pred_labels,
        "cat_probs": raw_cat_probs,
        "cat_conf": cat_confidences,
        "languages": df.get("language", pd.Series(["en"] * len(df))).astype(str).tolist(),
        "texts": df["text"].astype(str).tolist(),
    }


def compute_task_metrics(
    y_true: list[str],
    y_pred: list[str],
    class_order: list[str],
) -> dict[str, Any]:
    """
    Computes Macro-F1, Accuracy, and per-class precision, recall, and F1.
    """
    macro_f1 = float(f1_score(y_true, y_pred, labels=class_order, average="macro", zero_division=0))
    acc = float(accuracy_score(y_true, y_pred))

    precisions = precision_score(y_true, y_pred, labels=class_order, average=None, zero_division=0)
    recalls = recall_score(y_true, y_pred, labels=class_order, average=None, zero_division=0)
    f1s = f1_score(y_true, y_pred, labels=class_order, average=None, zero_division=0)

    per_class = {}
    for cls_name, p, r, f in zip(class_order, precisions, recalls, f1s, strict=False):
        support = sum(1 for yt in y_true if yt == cls_name)
        per_class[cls_name] = {
            "precision": round(float(p), 4),
            "recall": round(float(r), 4),
            "f1": round(float(f), 4),
            "support": int(support),
        }

    cm = confusion_matrix(y_true, y_pred, labels=class_order)

    return {
        "macro_f1": round(macro_f1, 4),
        "accuracy": round(acc, 4),
        "per_class": per_class,
        "confusion_matrix": cm.tolist(),
    }


# ==============================================================================
# Full Evaluation Pipeline
# ==============================================================================

def run_evaluation(
    test_path: str | Path = DEFAULT_TEST_PATH,
    model_path: str | Path = DEFAULT_MODEL_PATH,
    vocab_path: str | Path = DEFAULT_VOCAB_PATH,
    calibration_path: str | Path = DEFAULT_CALIBRATION_PATH,
    report_path: str | Path = DEFAULT_REPORT_PATH,
    errors_path: str | Path = DEFAULT_ERRORS_PATH,
) -> dict[str, Any]:
    """
    Runs full multi-task evaluation, slices, robustness probes, error dumps, and report emission.
    """
    t_file = Path(test_path)
    if not t_file.exists():
        raise FileNotFoundError(f"Test dataset not found at '{t_file}'")

    m_file = Path(model_path)
    if not m_file.exists():
        if DEFAULT_LEGACY_MODEL_PATH.exists():
            m_file = DEFAULT_LEGACY_MODEL_PATH
        else:
            raise FileNotFoundError(f"Model file not found at '{m_file}' or '{DEFAULT_LEGACY_MODEL_PATH}'")

    v_file = Path(vocab_path)
    if not v_file.exists():
        raise FileNotFoundError(f"Vocab file not found at '{v_file}'")

    logger.info("Loading test dataset from %s...", t_file)
    df_test = pd.read_parquet(t_file)
    logger.info("Loaded %d test samples.", len(df_test))

    logger.info("Loading model from %s...", m_file)
    model = tf.keras.models.load_model(str(m_file), compile=False)

    tokenizer = CrisisTokenizer()
    tokenizer.load_vocab(v_file)
    regex_engine = RegexEngine()

    temperature = load_calibration_temperature(calibration_path)
    logger.info("Using calibrated severity temperature T=%.4f", temperature)

    # 1. Clean Baseline Inference
    base_res = run_model_inference(model, df_test, tokenizer, regex_engine, temperature=temperature)

    sev_metrics = compute_task_metrics(base_res["sev_true"], base_res["sev_pred"], SEVERITY_CLASSES)
    cat_metrics = compute_task_metrics(base_res["cat_true"], base_res["cat_pred"], CATEGORY_CLASSES)

    # Combined exact-match accuracy
    exact_matches = [
        (st == sp and ct == cp)
        for st, sp, ct, cp in zip(
            base_res["sev_true"], base_res["sev_pred"], base_res["cat_true"], base_res["cat_pred"], strict=False
        )
    ]
    exact_match_acc = float(np.mean(exact_matches))

    # 2. Language Slices
    languages = ["en", "hi", "hinglish"]
    lang_slices: dict[str, dict[str, Any]] = {}
    mean_combined_f1 = (sev_metrics["macro_f1"] + cat_metrics["macro_f1"]) / 2.0

    underperforming_slices: list[dict[str, Any]] = []

    for lang in languages:
        mask = [lang_item.lower() == lang for lang_item in base_res["languages"]]
        n_samples = sum(mask)
        if n_samples == 0:
            continue

        l_sev_true = [st for st, m in zip(base_res["sev_true"], mask, strict=False) if m]
        l_sev_pred = [sp for sp, m in zip(base_res["sev_pred"], mask, strict=False) if m]
        l_cat_true = [ct for ct, m in zip(base_res["cat_true"], mask, strict=False) if m]
        l_cat_pred = [cp for cp, m in zip(base_res["cat_pred"], mask, strict=False) if m]

        l_sev_f1 = float(f1_score(l_sev_true, l_sev_pred, labels=SEVERITY_CLASSES, average="macro", zero_division=0))
        l_cat_f1 = float(f1_score(l_cat_true, l_cat_pred, labels=CATEGORY_CLASSES, average="macro", zero_division=0))
        l_comb_f1 = (l_sev_f1 + l_cat_f1) / 2.0

        gap = mean_combined_f1 - l_comb_f1
        flagged = gap > 0.05  # Flag if > 5 F1 points (0.05) below overall mean

        slice_info = {
            "count": n_samples,
            "severity_f1": round(l_sev_f1, 4),
            "category_f1": round(l_cat_f1, 4),
            "combined_f1": round(l_comb_f1, 4),
            "gap_to_mean": round(gap, 4),
            "flagged": flagged,
        }
        lang_slices[lang] = slice_info

        if flagged:
            underperforming_slices.append({"language": lang, **slice_info})

    # 3. Robustness Probes
    robustness_results: dict[str, dict[str, Any]] = {}

    # Probe A: Typo Injection
    df_typo = df_test.copy()
    df_typo["text"] = [inject_typos(t, typo_rate=0.20, seed=42) for t in df_test["text"]]
    typo_res = run_model_inference(model, df_typo, tokenizer, regex_engine, temperature=temperature)
    typo_sev_f1 = float(f1_score(typo_res["sev_true"], typo_res["sev_pred"], labels=SEVERITY_CLASSES, average="macro", zero_division=0))
    typo_cat_f1 = float(f1_score(typo_res["cat_true"], typo_res["cat_pred"], labels=CATEGORY_CLASSES, average="macro", zero_division=0))

    robustness_results["typo_injection"] = {
        "name": "Typo Injection (p=0.20 keyboard noise)",
        "sev_f1": round(typo_sev_f1, 4),
        "sev_delta": round(typo_sev_f1 - sev_metrics["macro_f1"], 4),
        "cat_f1": round(typo_cat_f1, 4),
        "cat_delta": round(typo_cat_f1 - cat_metrics["macro_f1"], 4),
    }

    # Probe B: Vowel Dropping
    df_vowel = df_test.copy()
    df_vowel["text"] = [drop_vowels(t, seed=42) for t in df_test["text"]]
    vowel_res = run_model_inference(model, df_vowel, tokenizer, regex_engine, temperature=temperature)
    vowel_sev_f1 = float(f1_score(vowel_res["sev_true"], vowel_res["sev_pred"], labels=SEVERITY_CLASSES, average="macro", zero_division=0))
    vowel_cat_f1 = float(f1_score(vowel_res["cat_true"], vowel_res["cat_pred"], labels=CATEGORY_CLASSES, average="macro", zero_division=0))

    robustness_results["vowel_dropping"] = {
        "name": "Vowel Dropping (SMS / Chat shorthand)",
        "sev_f1": round(vowel_sev_f1, 4),
        "sev_delta": round(vowel_sev_f1 - sev_metrics["macro_f1"], 4),
        "cat_f1": round(vowel_cat_f1, 4),
        "cat_delta": round(vowel_cat_f1 - cat_metrics["macro_f1"], 4),
    }

    # Probe C: Truncation
    df_trunc = df_test.copy()
    df_trunc["text"] = [truncate_text(t, ratio=0.5) for t in df_test["text"]]
    trunc_res = run_model_inference(model, df_trunc, tokenizer, regex_engine, temperature=temperature)
    trunc_sev_f1 = float(f1_score(trunc_res["sev_true"], trunc_res["sev_pred"], labels=SEVERITY_CLASSES, average="macro", zero_division=0))
    trunc_cat_f1 = float(f1_score(trunc_res["cat_true"], trunc_res["cat_pred"], labels=CATEGORY_CLASSES, average="macro", zero_division=0))

    robustness_results["truncation"] = {
        "name": "Truncation (50% token cut / SMS limit)",
        "sev_f1": round(trunc_sev_f1, 4),
        "sev_delta": round(trunc_sev_f1 - sev_metrics["macro_f1"], 4),
        "cat_f1": round(trunc_cat_f1, 4),
        "cat_delta": round(trunc_cat_f1 - cat_metrics["macro_f1"], 4),
    }

    # 4. Error Analysis: Dump worst 50 misclassifications to CSV
    error_rows: list[dict[str, Any]] = []
    for i in range(len(df_test)):
        st = base_res["sev_true"][i]
        sp = base_res["sev_pred"][i]
        sc = base_res["sev_conf"][i]

        ct = base_res["cat_true"][i]
        cp = base_res["cat_pred"][i]
        cc = base_res["cat_conf"][i]

        sev_err = st != sp
        cat_err = ct != cp

        if sev_err or cat_err:
            error_type = []
            if sev_err:
                error_type.append(f"Severity({st}->{sp})")
            if cat_err:
                error_type.append(f"Category({ct}->{cp})")

            error_rows.append({
                "text": base_res["texts"][i],
                "language": base_res["languages"][i],
                "true_severity": st,
                "pred_severity": sp,
                "severity_confidence": round(float(sc), 4),
                "true_category": ct,
                "pred_category": cp,
                "category_confidence": round(float(cc), 4),
                "max_confidence": round(float(max(sc, cc)), 4),
                "error_type": " + ".join(error_type),
            })

    # Sort errors by maximum confidence (worst overconfident mistakes first)
    error_rows.sort(key=lambda x: x["max_confidence"], reverse=True)
    worst_errors = error_rows[:50]

    err_df = pd.DataFrame(worst_errors)
    out_err_file = Path(errors_path)
    out_err_file.parent.mkdir(parents=True, exist_ok=True)
    err_df.to_csv(out_err_file, index=False)
    logger.info("Saved %d misclassifications to %s", len(err_df), out_err_file)

    # 5. Emit EVAL_REPORT.md
    out_rep_file = Path(report_path)
    out_rep_file.parent.mkdir(parents=True, exist_ok=True)
    generate_markdown_report(
        output_file=out_rep_file,
        num_samples=len(df_test),
        sev_metrics=sev_metrics,
        cat_metrics=cat_metrics,
        exact_match_acc=exact_match_acc,
        lang_slices=lang_slices,
        underperforming_slices=underperforming_slices,
        robustness_results=robustness_results,
        worst_errors=worst_errors,
        temperature=temperature,
    )
    logger.info("Generated evaluation report at %s", out_rep_file)

    # Print summary to stdout
    print_cli_summary(
        sev_metrics=sev_metrics,
        cat_metrics=cat_metrics,
        exact_match_acc=exact_match_acc,
        lang_slices=lang_slices,
        underperforming_slices=underperforming_slices,
        robustness_results=robustness_results,
        num_errors=len(error_rows),
        report_path=str(out_rep_file),
    )

    return {
        "num_test_samples": len(df_test),
        "severity": sev_metrics,
        "category": cat_metrics,
        "exact_match_accuracy": round(exact_match_acc, 4),
        "language_slices": lang_slices,
        "flagged_slices": underperforming_slices,
        "robustness": robustness_results,
        "errors_count": len(error_rows),
        "report_path": str(out_rep_file),
        "errors_path": str(out_err_file),
    }


# ==============================================================================
# Markdown Report Generator
# ==============================================================================

def generate_markdown_report(
    output_file: Path,
    num_samples: int,
    sev_metrics: dict[str, Any],
    cat_metrics: dict[str, Any],
    exact_match_acc: float,
    lang_slices: dict[str, dict[str, Any]],
    underperforming_slices: list[dict[str, Any]],
    robustness_results: dict[str, dict[str, Any]],
    worst_errors: list[dict[str, Any]],
    temperature: float,
) -> None:
    """Writes full evaluation findings to EVAL_REPORT.md."""
    now_str = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d %H:%M:%S UTC")

    md: list[str] = []
    md.append("# Project Pukar — Model Evaluation & Reliability Benchmark Report")
    md.append(f"**Generated:** `{now_str}`  ")
    md.append(f"**Dataset:** `ml/datasets/processed/test.parquet` (N = {num_samples} holdout samples)  ")
    md.append(f"**Severity Calibrated Temperature:** `T = {temperature:.4f}`\n")

    md.append("---")
    md.append("## 1. Executive Summary & Overall Test Performance\n")
    md.append("| Metric Head | Macro-F1 | Overall Accuracy | Target Threshold | Status |")
    md.append("| :--- | :---: | :---: | :---: | :---: |")
    sev_pass = "✅ MET" if sev_metrics["macro_f1"] >= 0.85 else "⚠️ GAP"
    cat_pass = "✅ MET" if cat_metrics["macro_f1"] >= 0.80 else "⚠️ GAP"
    md.append(f"| **Severity (3-class)** | **{sev_metrics['macro_f1']:.4f}** | {sev_metrics['accuracy'] * 100:.1f}% | $\\ge 0.85$ | {sev_pass} |")
    md.append(f"| **Category (5-class)** | **{cat_metrics['macro_f1']:.4f}** | {cat_metrics['accuracy'] * 100:.1f}% | $\\ge 0.80$ | {cat_pass} |")
    md.append(f"| **Joint Exact Match**  | — | **{exact_match_acc * 100:.1f}%** | — | — |\n")

    md.append("---")
    md.append("## 2. Per-Class Granular Breakdown\n")
    md.append("### Severity Classification Head")
    md.append("| Class | Precision | Recall | F1-Score | Support |")
    md.append("| :--- | :---: | :---: | :---: | :---: |")
    for cls_name in SEVERITY_CLASSES:
        p = sev_metrics["per_class"][cls_name]
        md.append(f"| `{cls_name}` | {p['precision']:.4f} | {p['recall']:.4f} | **{p['f1']:.4f}** | {p['support']} |")

    md.append("\n### Category Classification Head")
    md.append("| Class | Precision | Recall | F1-Score | Support |")
    md.append("| :--- | :---: | :---: | :---: | :---: |")
    for cls_name in CATEGORY_CLASSES:
        p = cat_metrics["per_class"][cls_name]
        md.append(f"| `{cls_name}` | {p['precision']:.4f} | {p['recall']:.4f} | **{p['f1']:.4f}** | {p['support']} |")

    md.append("\n---")
    md.append("## 3. Confusion Matrices\n")
    md.append("### Severity Confusion Matrix (`rows: true`, `cols: predicted`)")
    md.append("| True \\ Pred | " + " | ".join([f"**{c}**" for c in SEVERITY_CLASSES]) + " |")
    md.append("| :--- | " + " | ".join([":---:"] * len(SEVERITY_CLASSES)) + " |")
    for r_name, row in zip(SEVERITY_CLASSES, sev_metrics["confusion_matrix"], strict=False):
        md.append(f"| **{r_name}** | " + " | ".join(str(v) for v in row) + " |")

    md.append("\n### Category Confusion Matrix (`rows: true`, `cols: predicted`)")
    md.append("| True \\ Pred | " + " | ".join([f"**{c}**" for c in CATEGORY_CLASSES]) + " |")
    md.append("| :--- | " + " | ".join([":---:"] * len(CATEGORY_CLASSES)) + " |")
    for r_name, row in zip(CATEGORY_CLASSES, cat_metrics["confusion_matrix"], strict=False):
        md.append(f"| **{r_name}** | " + " | ".join(str(v) for v in row) + " |")

    md.append("\n---")
    md.append("## 4. Multilingual Language Slices & Disparity Audit\n")
    md.append("| Language Slice | Sample Count (N) | Severity F1 | Category F1 | Combined F1 | Gap to Mean | Slice Status |")
    md.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: |")
    for lang, s in lang_slices.items():
        status_flag = "🚩 **UNDERPERFORMING (>5pt gap)**" if s["flagged"] else "✅ Balanced"
        gap_sign = f"{s['gap_to_mean']:+.4f}"
        md.append(
            f"| **{lang.upper()}** | {s['count']} | {s['severity_f1']:.4f} | {s['category_f1']:.4f} | {s['combined_f1']:.4f} | {gap_sign} | {status_flag} |"
        )

    if underperforming_slices:
        md.append("\n> [!WARNING]")
        md.append("> **Multilingual Performance Warning:**")
        for u in underperforming_slices:
            md.append(
                f"> - `{u['language'].upper()}` is underperforming the overall mean by **{u['gap_to_mean']*100:.1f} F1 points**. Increase synthetic training density for this language."
            )

    md.append("\n---")
    md.append("## 5. Robustness & Edge Stress Probes\n")
    md.append("| Stress Condition | Severity F1 | $\\Delta$ Sev F1 | Category F1 | $\\Delta$ Cat F1 | Resilience Rating |")
    md.append("| :--- | :---: | :---: | :---: | :---: | :---: |")
    for _, r in robustness_results.items():
        s_delta_str = f"{r['sev_delta']:+.4f}"
        c_delta_str = f"{r['cat_delta']:+.4f}"
        avg_drop = (abs(r['sev_delta']) + abs(r['cat_delta'])) / 2.0
        rating = "🟢 Excellent (<5% drop)" if avg_drop < 0.05 else ("🟡 Moderate (5-15% drop)" if avg_drop < 0.15 else "🔴 High Sensitivity")
        md.append(f"| **{r['name']}** | {r['sev_f1']:.4f} | {s_delta_str} | {r['cat_f1']:.4f} | {c_delta_str} | {rating} |")

    md.append("\n---")
    md.append("## 6. Error Analysis & Worst Misclassifications\n")
    md.append(f"Full details for top misclassifications dumped to [`ml/eval/errors.csv`](file://{DEFAULT_ERRORS_PATH.resolve()}).\n")
    md.append("| Sample Text | Lang | True / Pred Severity | True / Pred Category | Error Type | Conf |")
    md.append("| :--- | :---: | :---: | :---: | :---: | :---: |")
    for e in worst_errors[:10]:
        t_trunc = e["text"][:45] + ("..." if len(e["text"]) > 45 else "")
        md.append(
            f"| `{t_trunc}` | {e['language']} | `{e['true_severity']}` → `{e['pred_severity']}` | `{e['true_category']}` → `{e['pred_category']}` | {e['error_type']} | {e['max_confidence']:.2f} |"
        )

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")


def print_cli_summary(
    sev_metrics: dict[str, Any],
    cat_metrics: dict[str, Any],
    exact_match_acc: float,
    lang_slices: dict[str, dict[str, Any]],
    underperforming_slices: list[dict[str, Any]],
    robustness_results: dict[str, dict[str, Any]],
    num_errors: int,
    report_path: str,
) -> None:
    """Prints a structured summary table to stdout."""
    print("\n" + "=" * 72)
    print(" PROJECT PUKAR — HOLDOUT TEST EVALUATION SUMMARY")
    print("=" * 72)
    print(f" Severity Macro-F1:     {sev_metrics['macro_f1']:.4f} (Acc: {sev_metrics['accuracy']*100:.1f}%)")
    print(f" Category Macro-F1:     {cat_metrics['macro_f1']:.4f} (Acc: {cat_metrics['accuracy']*100:.1f}%)")
    print(f" Joint Exact-Match Acc: {exact_match_acc*100:.1f}%")
    print("-" * 72)
    print(" Language Slices Disparity Audit:")
    for lang, s in lang_slices.items():
        flag = " [FLAGGED >5pt GAP]" if s["flagged"] else ""
        print(f"   - {lang.upper():<8} (n={s['count']}): Sev-F1={s['severity_f1']:.4f}, Cat-F1={s['category_f1']:.4f}, Comb-F1={s['combined_f1']:.4f}{flag}")
    print("-" * 72)
    print(" Robustness Probes Summary:")
    for _, r in robustness_results.items():
        print(f"   - {r['name']:<38} -> Sev-F1: {r['sev_f1']:.4f} ({r['sev_delta']:+.4f}), Cat-F1: {r['cat_f1']:.4f} ({r['cat_delta']:+.4f})")
    print("-" * 72)
    print(f" Total Errors Dumped:   {num_errors} -> {DEFAULT_ERRORS_PATH}")
    print(f" Full Report Emitted:   {report_path}")
    print("=" * 72 + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate Project Pukar student model on holdout test split.")
    parser.add_argument("--test-path", type=str, default=str(DEFAULT_TEST_PATH), help="Path to test.parquet")
    parser.add_argument("--model-path", type=str, default=str(DEFAULT_MODEL_PATH), help="Path to .keras model")
    parser.add_argument("--vocab-path", type=str, default=str(DEFAULT_VOCAB_PATH), help="Path to vocab.json")
    parser.add_argument("--calibration-path", type=str, default=str(DEFAULT_CALIBRATION_PATH), help="Path to calibration.json")
    parser.add_argument("--report-path", type=str, default=str(DEFAULT_REPORT_PATH), help="Path to EVAL_REPORT.md")
    parser.add_argument("--errors-path", type=str, default=str(DEFAULT_ERRORS_PATH), help="Path to errors.csv")
    args = parser.parse_args()

    run_evaluation(
        test_path=args.test_path,
        model_path=args.model_path,
        vocab_path=args.vocab_path,
        calibration_path=args.calibration_path,
        report_path=args.report_path,
        errors_path=args.errors_path,
    )


if __name__ == "__main__":
    main()
