"""
Project Pukar - Multi-Task Student Model Knowledge Distillation Training Pipeline
================================================================================

Overview:
---------
Trains the compact on-device student model (pukar_multitask_crisis_net) using
Knowledge Distillation (KD) from teacher soft probability distributions.

Loss Formulation:
-----------------
For each task k in {severity, category}:
  - Hard Loss: Weighted Categorical Cross-Entropy against ground truth hard labels.
      L_hard = - sum_c (w_c * y_c * log(p_c + eps))
  - Soft Loss: Kullback-Leibler (KL) Divergence against teacher soft probabilities with temperature T.
      L_soft = T^2 * KL(q_T || p_T)
  - Task Loss:
      L_task = (1 - alpha) * L_hard + alpha * L_soft

Total Loss:
  L_total = w_sev * L_severity + w_cat * L_category

Features & Callbacks:
---------------------
1. Joint Multi-Task Training: Severity (3-class) + Category (5-class).
2. Deterministic Signal Ingestion: [regex_score, language_id] passed as auxiliary features.
3. Class-Imbalance Balancing: Applies inverse-frequency weights from ml/configs/class_weights.yaml.
4. Validation Macro-F1 Tracking: Computes severity, category, and per-language (en, hi, hinglish) F1.
5. Early Stopping & ReduceLROnPlateau: Saves best checkpoint to ml/model/artifacts/student_fp32.keras.
"""

import argparse
import logging
import os
import random
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import tensorflow as tf
import yaml
from dotenv import load_dotenv
from sklearn.metrics import f1_score

from ml.model.architecture import build_model
from ml.tokenizer.tokenizer import CrisisTokenizer
from services.backend.src.ml.contracts import Category, Language, Severity
from services.backend.src.ml.regex_engine import RegexEngine

# Ensure repo root is on sys.path for direct CLI invocations
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("pukar.train")

DEFAULT_CONFIG_PATH = Path("ml/configs/train.yaml")

SEVERITY_ORDER = [Severity.INFO.value, Severity.WARN.value, Severity.CRITICAL.value]
CATEGORY_ORDER = [
    Category.RESCUE.value,
    Category.MEDICAL.value,
    Category.FIRE.value,
    Category.SHELTER.value,
    Category.OTHER.value,
]
LANGUAGE_MAP = {
    Language.EN.value: 0.0,
    Language.HI.value: 1.0,
    Language.HINGLISH.value: 2.0,
}


def set_seed(seed: int = 42) -> None:
    """Sets deterministic random seeds across Python, NumPy, and TensorFlow."""
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)
    tf.random.set_seed(seed)
    logger.info("Deterministic random seed set to %d", seed)


def load_yaml_config(config_path: str | Path) -> dict[str, Any]:
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found at '{path}'")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_class_weights(weights_path: str | Path) -> tuple[np.ndarray, np.ndarray]:
    """
    Loads severity and category class weights from YAML into aligned numpy arrays.
    """
    w_cfg = load_yaml_config(weights_path)
    sev_w_dict = w_cfg.get("severity_weights", {})
    cat_w_dict = w_cfg.get("category_weights", {})

    sev_weights = np.array([float(sev_w_dict.get(c, 1.0)) for c in SEVERITY_ORDER], dtype=np.float32)
    cat_weights = np.array([float(cat_w_dict.get(c, 1.0)) for c in CATEGORY_ORDER], dtype=np.float32)

    logger.info("Loaded Severity Class Weights: %s", dict(zip(SEVERITY_ORDER, sev_weights)))
    logger.info("Loaded Category Class Weights: %s", dict(zip(CATEGORY_ORDER, cat_weights)))
    return sev_weights, cat_weights


def prepare_dataset_arrays(
    df: pd.DataFrame,
    tokenizer: CrisisTokenizer,
    regex_engine: RegexEngine,
    max_seq_len: int = 64,
) -> dict[str, np.ndarray]:
    """
    Prepares token_ids, auxiliary features, hard labels, and soft labels from a dataframe.
    """
    texts = df["text"].astype(str).tolist()
    token_ids = np.array([tokenizer.encode(t) for t in texts], dtype=np.int32)

    # Compute auxiliary features: [regex_score (0.0 to 1.0), language_id (0.0, 1.0, 2.0)]
    aux_list: list[list[float]] = []
    for text, lang in zip(texts, df.get("language", ["en"] * len(df))):
        regex_res = regex_engine.evaluate(text)
        score_norm = float(regex_res.get("score", 0)) / 100.0
        lang_id = LANGUAGE_MAP.get(str(lang).lower(), 0.0)
        aux_list.append([score_norm, lang_id])
    aux_features = np.array(aux_list, dtype=np.float32)

    # Hard labels (one-hot)
    sev_indices = [
        SEVERITY_ORDER.index(s) if s in SEVERITY_ORDER else 1
        for s in df.get("severity", ["warn"] * len(df))
    ]
    cat_indices = [
        CATEGORY_ORDER.index(c) if c in CATEGORY_ORDER else 4
        for c in df.get("category", ["other"] * len(df))
    ]

    y_sev_hard = tf.keras.utils.to_categorical(sev_indices, num_classes=3).astype(np.float32)
    y_cat_hard = tf.keras.utils.to_categorical(cat_indices, num_classes=5).astype(np.float32)

    # Soft labels (if present)
    if "soft_severity" in df.columns and "soft_category" in df.columns:
        y_sev_soft = np.array(df["soft_severity"].tolist(), dtype=np.float32)
        y_cat_soft = np.array(df["soft_category"].tolist(), dtype=np.float32)
    else:
        # Fallback to hard one-hot if soft labels absent
        y_sev_soft = y_sev_hard.copy()
        y_cat_soft = y_cat_hard.copy()

    languages = df.get("language", pd.Series(["en"] * len(df))).astype(str).tolist()

    return {
        "token_ids": token_ids,
        "aux_features": aux_features,
        "y_sev_hard": y_sev_hard,
        "y_cat_hard": y_cat_hard,
        "y_sev_soft": y_sev_soft,
        "y_cat_soft": y_cat_soft,
        "languages": np.array(languages),
    }


def compute_weighted_categorical_crossentropy(
    y_true: tf.Tensor,
    y_pred: tf.Tensor,
    class_weights: tf.Tensor,
    eps: float = 1e-7,
) -> tf.Tensor:
    """Computes sample-wise weighted categorical cross-entropy."""
    y_pred = tf.clip_by_value(y_pred, eps, 1.0 - eps)
    # y_true: (batch, num_classes), class_weights: (num_classes,)
    weighted_log_probs = y_true * tf.math.log(y_pred) * class_weights
    loss_per_sample = -tf.reduce_sum(weighted_log_probs, axis=-1)
    return tf.reduce_mean(loss_per_sample)


def compute_kl_divergence_kd(
    teacher_soft: tf.Tensor,
    student_probs: tf.Tensor,
    temperature: float = 2.0,
    eps: float = 1e-7,
) -> tf.Tensor:
    """
    Computes temperature-scaled Kullback-Leibler divergence for Knowledge Distillation:
      L_kd = T^2 * KL(q_T || p_T)
    """
    # Scale student probabilities to temperature T
    student_log_probs = tf.math.log(tf.clip_by_value(student_probs, eps, 1.0)) / temperature
    student_soft = tf.nn.softmax(student_log_probs, axis=-1)
    student_soft = tf.clip_by_value(student_soft, eps, 1.0)

    # Scale teacher probabilities if not already scaled
    teacher_soft = tf.clip_by_value(teacher_soft, eps, 1.0)

    # KL Divergence: sum( q * (log(q) - log(p)) )
    kl = tf.reduce_sum(
        teacher_soft * (tf.math.log(teacher_soft) - tf.math.log(student_soft)),
        axis=-1,
    )
    return (temperature**2) * tf.reduce_mean(kl)


def evaluate_model_metrics(
    model: tf.keras.Model,
    data: dict[str, np.ndarray],
) -> dict[str, Any]:
    """
    Evaluates Macro-F1 for severity, category, and per-language splits on validation set.
    """
    preds = model({"token_ids": data["token_ids"], "aux_features": data["aux_features"]}, training=False)
    sev_pred_probs = preds["severity"].numpy()
    cat_pred_probs = preds["category"].numpy()

    sev_pred_indices = np.argmax(sev_pred_probs, axis=-1)
    cat_pred_indices = np.argmax(cat_pred_probs, axis=-1)

    sev_true_indices = np.argmax(data["y_sev_hard"], axis=-1)
    cat_true_indices = np.argmax(data["y_cat_hard"], axis=-1)

    sev_macro_f1 = float(f1_score(sev_true_indices, sev_pred_indices, average="macro", zero_division=0))
    cat_macro_f1 = float(f1_score(cat_true_indices, cat_pred_indices, average="macro", zero_division=0))

    # Per-language F1
    per_lang_f1: dict[str, dict[str, float]] = {}
    languages = data["languages"]
    for lang in ["en", "hi", "hinglish"]:
        mask = languages == lang
        if np.sum(mask) > 0:
            lang_sev_f1 = float(f1_score(sev_true_indices[mask], sev_pred_indices[mask], average="macro", zero_division=0))
            lang_cat_f1 = float(f1_score(cat_true_indices[mask], cat_pred_indices[mask], average="macro", zero_division=0))
            per_lang_f1[lang] = {
                "count": int(np.sum(mask)),
                "severity_f1": round(lang_sev_f1, 4),
                "category_f1": round(lang_cat_f1, 4),
            }

    return {
        "severity_macro_f1": round(sev_macro_f1, 4),
        "category_macro_f1": round(cat_macro_f1, 4),
        "combined_macro_f1": round((sev_macro_f1 + cat_macro_f1) / 2.0, 4),
        "per_language": per_lang_f1,
    }


def train_student_model(
    config_path: str | Path = DEFAULT_CONFIG_PATH,
    override_epochs: int | None = None,
    override_batch_size: int | None = None,
    override_lr: float | None = None,
) -> tuple[tf.keras.Model, dict[str, Any]]:
    """
    Main knowledge distillation student model training pipeline.
    """
    cfg = load_yaml_config(config_path)

    # 1. Config parameters
    train_cfg = cfg.get("training", {})
    dist_cfg = cfg.get("distillation", {})
    paths_cfg = cfg.get("paths", {})
    targets_cfg = cfg.get("targets", {})

    seed = int(train_cfg.get("seed", 42))
    set_seed(seed)

    epochs = override_epochs or int(train_cfg.get("epochs", 50))
    batch_size = override_batch_size or int(train_cfg.get("batch_size", 16))
    lr = override_lr or float(train_cfg.get("learning_rate", 0.003))

    alpha = float(dist_cfg.get("alpha", 0.5))
    temperature = float(dist_cfg.get("temperature", 2.0))
    sev_loss_weight = float(dist_cfg.get("severity_weight", 1.0))
    cat_loss_weight = float(dist_cfg.get("category_weight", 0.8))

    early_stopping_patience = int(train_cfg.get("early_stopping_patience", 12))
    reduce_lr_patience = int(train_cfg.get("reduce_lr_patience", 5))
    reduce_lr_factor = float(train_cfg.get("reduce_lr_factor", 0.5))
    min_lr = float(train_cfg.get("min_lr", 0.00005))

    target_sev_f1 = float(targets_cfg.get("val_severity_macro_f1_target", 0.85))
    target_cat_f1 = float(targets_cfg.get("val_category_macro_f1_target", 0.80))

    # 2. Paths
    train_path = Path(paths_cfg.get("train_dataset", "ml/datasets/processed/train_soft.parquet"))
    val_path = Path(paths_cfg.get("val_dataset", "ml/datasets/processed/val.parquet"))
    class_weights_path = Path(paths_cfg.get("class_weights", "ml/configs/class_weights.yaml"))
    vocab_path = Path(paths_cfg.get("vocab", "ml/tokenizer/vocab.json"))
    model_cfg_path = Path(paths_cfg.get("model_config", "ml/configs/model.yaml"))
    save_model_path = Path(paths_cfg.get("save_model_path", "ml/model/artifacts/student_fp32.keras"))
    legacy_model_path = Path(paths_cfg.get("legacy_model_path", "ml/model/pukar_model.keras"))

    # Ensure train_soft.parquet exists
    if not train_path.exists():
        logger.info("Soft-labeled training data not found at %s. Generating...", train_path)
        from ml.model.teacher import generate_soft_labels
        generate_soft_labels(output_path=train_path, temperature=temperature)

    # 3. Load Tokenizer & Regex Engine
    tokenizer = CrisisTokenizer()
    if vocab_path.exists():
        tokenizer.load_vocab(vocab_path)
        logger.info("Loaded vocabulary from %s (size: %d)", vocab_path, len(tokenizer.vocab))
    else:
        raise FileNotFoundError(f"Vocabulary not found at '{vocab_path}'. Run tokenizer fit first.")

    regex_engine = RegexEngine()

    # 4. Load Data & Prepare Arrays
    df_train = pd.read_parquet(train_path)
    df_val = pd.read_parquet(val_path)
    logger.info("Loaded Train samples: %d, Val samples: %d", len(df_train), len(df_val))

    train_data = prepare_dataset_arrays(df_train, tokenizer, regex_engine)
    val_data = prepare_dataset_arrays(df_val, tokenizer, regex_engine)

    # 5. Load Class Weights
    sev_weights, cat_weights = load_class_weights(class_weights_path)
    tf_sev_weights = tf.constant(sev_weights, dtype=tf.float32)
    tf_cat_weights = tf.constant(cat_weights, dtype=tf.float32)

    # 6. Build Student Model
    student_model = build_model(
        config=model_cfg_path,
        compile_model=False,
        print_summary=True,
    )

    optimizer = tf.keras.optimizers.Adam(learning_rate=lr)

    # 7. Knowledge Distillation Training Loop
    num_train_samples = len(df_train)
    steps_per_epoch = int(np.ceil(num_train_samples / batch_size))

    best_sev_f1 = -1.0
    best_combined_f1 = -1.0
    best_epoch = 0
    patience_counter = 0
    lr_patience_counter = 0
    current_lr = lr

    save_model_path.parent.mkdir(parents=True, exist_ok=True)
    legacy_model_path.parent.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 70)
    print(" PROJECT PUKAR — STUDENT KNOWLEDGE DISTILLATION TRAINING")
    print(f" Alpha (Soft vs Hard): {alpha:.2f} | Temperature: {temperature:.1f} | Initial LR: {lr}")
    print(f" Targets -> Severity Macro-F1 >= {target_sev_f1:.2f} | Category Macro-F1 >= {target_cat_f1:.2f}")
    print("=" * 70)

    for epoch in range(1, epochs + 1):
        # Shuffle indices each epoch
        perm = np.random.permutation(num_train_samples)
        epoch_losses: list[float] = []

        for step in range(steps_per_epoch):
            batch_idx = perm[step * batch_size : (step + 1) * batch_size]
            b_tokens = train_data["token_ids"][batch_idx]
            b_aux = train_data["aux_features"][batch_idx]
            b_y_sev_hard = train_data["y_sev_hard"][batch_idx]
            b_y_cat_hard = train_data["y_cat_hard"][batch_idx]
            b_y_sev_soft = train_data["y_sev_soft"][batch_idx]
            b_y_cat_soft = train_data["y_cat_soft"][batch_idx]

            with tf.GradientTape() as tape:
                preds = student_model({"token_ids": b_tokens, "aux_features": b_aux}, training=True)
                p_sev = preds["severity"]
                p_cat = preds["category"]

                # 1. Severity Loss (Hard CE + Soft KD)
                l_sev_hard = compute_weighted_categorical_crossentropy(b_y_sev_hard, p_sev, tf_sev_weights)
                l_sev_soft = compute_kl_divergence_kd(b_y_sev_soft, p_sev, temperature=temperature)
                l_sev = (1.0 - alpha) * l_sev_hard + alpha * l_sev_soft

                # 2. Category Loss (Hard CE + Soft KD)
                l_cat_hard = compute_weighted_categorical_crossentropy(b_y_cat_hard, p_cat, tf_cat_weights)
                l_cat_soft = compute_kl_divergence_kd(b_y_cat_soft, p_cat, temperature=temperature)
                l_cat = (1.0 - alpha) * l_cat_hard + alpha * l_cat_soft

                # 3. Total Loss
                total_loss = (sev_loss_weight * l_sev) + (cat_loss_weight * l_cat)

            grads = tape.gradient(total_loss, student_model.trainable_variables)
            optimizer.apply_gradients(zip(grads, student_model.trainable_variables))
            epoch_losses.append(float(total_loss.numpy()))

        avg_train_loss = np.mean(epoch_losses)

        # Validation Evaluation
        val_metrics = evaluate_model_metrics(student_model, val_data)
        sev_f1 = val_metrics["severity_macro_f1"]
        cat_f1 = val_metrics["category_macro_f1"]
        combined_f1 = val_metrics["combined_macro_f1"]
        per_lang = val_metrics["per_language"]

        # Log epoch summary
        lang_str = " | ".join(
            [f"{k.upper()}: sev={v['severity_f1']:.2f}, cat={v['category_f1']:.2f}" for k, v in per_lang.items()]
        )
        print(
            f"Epoch {epoch:02d}/{epochs:02d} - Loss: {avg_train_loss:.4f} | "
            f"Val Sev-F1: {sev_f1:.4f} | Val Cat-F1: {cat_f1:.4f} | LR: {current_lr:.6f}"
        )
        print(f"   └─ Per-Language -> {lang_str}")

        # Checkpointing on best validation severity macro-F1
        is_best = (sev_f1 > best_sev_f1) or (np.isclose(sev_f1, best_sev_f1) and combined_f1 > best_combined_f1)
        if is_best:
            best_sev_f1 = sev_f1
            best_combined_f1 = combined_f1
            best_epoch = epoch
            patience_counter = 0
            lr_patience_counter = 0

            # Save best model checkpoints
            student_model.save(str(save_model_path))
            student_model.save(str(legacy_model_path))
            logger.info("★ New best model checkpoint saved to %s (Epoch %d, Sev-F1: %.4f, Cat-F1: %.4f)", save_model_path, epoch, sev_f1, cat_f1)
        else:
            patience_counter += 1
            lr_patience_counter += 1

            # ReduceLROnPlateau
            if lr_patience_counter >= reduce_lr_patience and current_lr > min_lr:
                current_lr = max(min_lr, current_lr * reduce_lr_factor)
                optimizer.learning_rate.assign(current_lr)
                lr_patience_counter = 0
                logger.info("▼ Reduced learning rate to %.6f", current_lr)

            # Early Stopping
            if patience_counter >= early_stopping_patience:
                logger.info("Early stopping triggered at epoch %d (no improvement for %d epochs)", epoch, patience_counter)
                break

    # 8. Load best model for final evaluation
    print("\n" + "=" * 70)
    print(" PROJECT PUKAR — FINAL VALIDATION PERFORMANCE REPORT")
    print("=" * 70)
    best_model = tf.keras.models.load_model(str(save_model_path), compile=False)
    final_metrics = evaluate_model_metrics(best_model, val_data)
    final_sev_f1 = final_metrics["severity_macro_f1"]
    final_cat_f1 = final_metrics["category_macro_f1"]

    sev_passed = final_sev_f1 >= target_sev_f1
    cat_passed = final_cat_f1 >= target_cat_f1

    print(f" Best Checkpoint Epoch:     {best_epoch}")
    print(f" Val Severity Macro-F1:     {final_sev_f1:.4f} (Target: >= {target_sev_f1:.2f}) -> {'PASSED' if sev_passed else 'GAP DETECTED'}")
    print(f" Val Category Macro-F1:     {final_cat_f1:.4f} (Target: >= {target_cat_f1:.2f}) -> {'PASSED' if cat_passed else 'GAP DETECTED'}")
    print("-" * 70)
    print(" Per-Language Breakdown:")
    for lang, metrics in final_metrics["per_language"].items():
        print(f"   - {lang.upper():<8} (n={metrics['count']}): Severity F1 = {metrics['severity_f1']:.4f}, Category F1 = {metrics['category_f1']:.4f}")
    print("-" * 70)

    if sev_passed and cat_passed:
        print(" SUCCESS: Both Severity (>= 0.85) and Category (>= 0.80) Macro-F1 targets MET!")
    else:
        print(" ACTIONABLE GAPS & OPTIMIZATION SUGGESTIONS:")
        if not sev_passed:
            gap = target_sev_f1 - final_sev_f1
            print(f"   1. Severity Gap ({gap:+.4f}): Increase Groq teacher temperature (T=2.5-3.0) or add targeted synthetic crisis samples (ml/data_gen/generate.py).")
        if not cat_passed:
            gap = target_cat_f1 - final_cat_f1
            print(f"   2. Category Gap ({gap:+.4f}): Check category confusion matrices (e.g. fire vs shelter) and adjust class weights in ml/configs/class_weights.yaml.")
    print("=" * 70 + "\n")

    return best_model, {
        "best_epoch": best_epoch,
        "final_metrics": final_metrics,
        "save_path": str(save_model_path),
        "sev_passed": sev_passed,
        "cat_passed": cat_passed,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Train Pukar Student Classifier via Knowledge Distillation.")
    parser.add_argument("--config", type=str, default=str(DEFAULT_CONFIG_PATH), help="Path to train.yaml")
    parser.add_argument("--epochs", type=int, default=None, help="Override epochs")
    parser.add_argument("--batch-size", type=int, default=None, help="Override batch size")
    parser.add_argument("--lr", type=float, default=None, help="Override learning rate")
    args = parser.parse_args()

    train_student_model(
        config_path=args.config,
        override_epochs=args.epochs,
        override_batch_size=args.batch_size,
        override_lr=args.lr,
    )


if __name__ == "__main__":
    main()
