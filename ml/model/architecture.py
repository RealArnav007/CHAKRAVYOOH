"""
Project Pukar - Multi-Task On-Device Neural Classifier Architecture
===================================================================

Overview:
---------
A lightweight multi-task neural network with a SHARED depthwise-separable TextCNN encoder
and TWO specialized classification heads:
  1. Severity Head: 3-class softmax (info, warn, critical)
  2. Category Head: 5-class softmax (rescue, medical, fire, shelter, other)

Why Multi-Task Single Shared Model?
-----------------------------------
1. Parameter & Size Efficiency:
   - One shared encoder extracts n-gram representations for both severity and category,
     cutting total parameter count by > 45% compared to two independent models.
2. Latency Budget:
   - Single forward pass executes in < 15-20 ms on low-end ARM Cortex-A53 CPUs.
3. Deterministic Auxiliary Fusion:
   - Ingests 2 deterministic scalar features [regex_score, language_id] alongside token IDs,
     allowing high-confidence regex rules to directly anchor the neural predictions.
4. Parameter Target:
   - Hard budget: < 400,000 parameters.
   - At ~130,000 parameters (25d embeddings + SeparableConv1D), INT8 quantized footprint
     is < 300 KB, fitting easily inside the 5 MB offline edge budget.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np
import tensorflow as tf
import yaml
from tensorflow.keras import Model, layers

logger = logging.getLogger("pukar.architecture")
DEFAULT_CONFIG_PATH = Path("ml/configs/model.yaml")


class ScaleLayer(layers.Layer):
    """Legacy scaling layer maintained for backward-compatibility with scalar regression models."""

    def __init__(self, scale_factor: float = 100.0, **kwargs):
        super().__init__(**kwargs)
        self.scale_factor = scale_factor

    def call(self, inputs):
        return inputs * self.scale_factor

    def get_config(self):
        config = super().get_config()
        config.update({"scale_factor": self.scale_factor})
        return config


def load_model_config(config_path: str | Path | dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Loads model architecture configuration from YAML file or returns provided dict.
    """
    if isinstance(config_path, dict):
        return config_path

    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    logger.warning("Config file '%s' not found. Using default architectural parameters.", path)
    return {
        "model": {
            "name": "pukar_multitask_crisis_net",
            "vocab_size": 5000,
            "embedding_dim": 25,
            "max_seq_len": 64,
            "embedding_matrix_path": "ml/model/embedding_matrix.npy",
            "trainable_embeddings": True,
        },
        "encoder": {
            "conv_filters": 32,
            "kernel_sizes": [3, 4, 5],
            "shared_dense_units": 64,
            "dropout_rate": 0.2,
            "activation": "relu",
        },
        "auxiliary": {
            "feature_dim": 2,
        },
        "heads": {
            "severity": {"name": "severity", "num_classes": 3, "loss_weight": 1.0},
            "category": {"name": "category", "num_classes": 5, "loss_weight": 0.8},
        },
        "training": {
            "optimizer": "adam",
            "learning_rate": 0.002,
        },
    }


def estimate_model_size(model: Model) -> dict[str, Any]:
    """
    Calculates parameter count and estimated memory/disk footprint across precisions.
    """
    total_params = int(model.count_params())
    trainable_params = int(sum(np.prod(w.shape) for w in model.trainable_weights))
    non_trainable_params = int(sum(np.prod(w.shape) for w in model.non_trainable_weights))

    fp32_mb = (total_params * 4) / (1024 * 1024)
    fp16_mb = (total_params * 2) / (1024 * 1024)
    int8_mb = (total_params * 1) / (1024 * 1024)

    return {
        "total_params": total_params,
        "trainable_params": trainable_params,
        "non_trainable_params": non_trainable_params,
        "target_max_params": 400_000,
        "within_param_budget": total_params <= 400_000,
        "estimated_size_fp32_mb": round(fp32_mb, 3),
        "estimated_size_fp16_mb": round(fp16_mb, 3),
        "estimated_size_int8_mb": round(int8_mb, 3),
    }


def print_model_budget_summary(model: Model) -> None:
    """
    Prints formatted parameter counts and size budget validation report.
    """
    stats = estimate_model_size(model)
    status_str = "PASSED (< 400k)" if stats["within_param_budget"] else "EXCEEDED (> 400k)"

    print("\n" + "=" * 65)
    print(" PROJECT PUKAR — MULTI-TASK MODEL SIZE & BUDGET REPORT")
    print("=" * 65)
    print(f" Model Name:            {model.name}")
    print(f" Total Parameters:      {stats['total_params']:,} ({status_str})")
    print(f" Trainable Parameters:  {stats['trainable_params']:,}")
    print(f" Non-Trainable:         {stats['non_trainable_params']:,}")
    print("-" * 65)
    print(" Memory / Storage Estimates:")
    print(f"   - FP32 Uncompressed: ~{stats['estimated_size_fp32_mb']:.2f} MB")
    print(f"   - FP16 Quantized:    ~{stats['estimated_size_fp16_mb']:.2f} MB")
    print(f"   - INT8 Quantized:    ~{stats['estimated_size_int8_mb']:.2f} MB (Target: < 2-3 MB)")
    print("=" * 65 + "\n")


def build_model(
    config: dict[str, Any] | str | Path | None = None,
    embedding_matrix: np.ndarray | None = None,
    compile_model: bool = True,
    print_summary: bool = True,
) -> Model:
    """
    Builds and compiles the multi-task crisis classifier with a shared depthwise-separable
    TextCNN encoder and two classification heads (severity & category), accepting token_ids
    and auxiliary features [regex_score, language_id].

    Args:
        config: Configuration dictionary or path to YAML config.
        embedding_matrix: Optional numpy embedding matrix of shape (vocab_size, embedding_dim).
                          If None, attempts loading from config's embedding_matrix_path.
        compile_model: Whether to compile the model with losses and metrics.
        print_summary: Whether to print the parameter budget summary.

    Returns:
        Compiled Keras Model instance.
    """
    cfg = load_model_config(config)
    m_cfg = cfg.get("model", {})
    enc_cfg = cfg.get("encoder", {})
    aux_cfg = cfg.get("auxiliary", {})
    heads_cfg = cfg.get("heads", {})
    train_cfg = cfg.get("training", {})

    model_name = m_cfg.get("name", "pukar_multitask_crisis_net")
    vocab_size = int(m_cfg.get("vocab_size", 5000))
    embedding_dim = int(m_cfg.get("embedding_dim", 25))
    max_seq_len = int(m_cfg.get("max_seq_len", 64))
    trainable_embeddings = bool(m_cfg.get("trainable_embeddings", True))

    conv_filters = int(enc_cfg.get("conv_filters", 32))
    kernel_sizes = enc_cfg.get("kernel_sizes", [3, 4, 5])
    shared_dense_units = int(enc_cfg.get("shared_dense_units", 64))
    dropout_rate = float(enc_cfg.get("dropout_rate", 0.2))
    activation = enc_cfg.get("activation", "relu")

    aux_dim = int(aux_cfg.get("feature_dim", 2))

    sev_cfg = heads_cfg.get("severity", {})
    num_severity_classes = int(sev_cfg.get("num_classes", 3))
    sev_head_name = sev_cfg.get("name", "severity")

    cat_cfg = heads_cfg.get("category", {})
    num_category_classes = int(cat_cfg.get("num_classes", 5))
    cat_head_name = cat_cfg.get("name", "category")

    # 1. Inputs
    # Primary textual token IDs input: (batch_size, max_seq_len)
    token_ids = layers.Input(shape=(max_seq_len,), dtype=tf.int32, name="token_ids")
    # Auxiliary deterministic signals: (batch_size, aux_dim) e.g. [regex_score, language_id]
    aux_features = layers.Input(shape=(aux_dim,), dtype=tf.float32, name="aux_features")

    # 2. Embedding Layer
    # Attempt loading pretrained embedding matrix if not directly provided
    if embedding_matrix is None:
        emb_path_str = m_cfg.get("embedding_matrix_path")
        if emb_path_str:
            emb_path = Path(emb_path_str)
            if emb_path.exists():
                try:
                    loaded_mat = np.load(emb_path)
                    # Check shape compatibility
                    if loaded_mat.ndim == 2:
                        embedding_matrix = loaded_mat
                        # Align vocab_size if needed
                        vocab_size = max(vocab_size, loaded_mat.shape[0])
                        embedding_dim = loaded_mat.shape[1]
                        logger.info(
                            "Loaded embedding matrix from %s with shape %s",
                            emb_path,
                            loaded_mat.shape,
                        )
                except Exception as e:
                    logger.warning("Could not load embedding matrix from %s: %s", emb_path, e)

    embedding_kwargs: dict[str, Any] = {
        "input_dim": vocab_size,
        "output_dim": embedding_dim,
        "mask_zero": False,
        "trainable": trainable_embeddings,
        "name": "embedding",
    }
    if embedding_matrix is not None:
        # Pad or slice embedding matrix if vocab_size exceeds matrix rows
        if embedding_matrix.shape[0] < vocab_size:
            pad_rows = vocab_size - embedding_matrix.shape[0]
            rng = np.random.default_rng(42)
            noise = rng.normal(0.0, 0.05, size=(pad_rows, embedding_dim)).astype(np.float32)
            embedding_matrix = np.vstack([embedding_matrix, noise])
        elif embedding_matrix.shape[0] > vocab_size:
            vocab_size = embedding_matrix.shape[0]
            embedding_kwargs["input_dim"] = vocab_size

        embedding_kwargs["embeddings_initializer"] = tf.keras.initializers.Constant(
            embedding_matrix[:vocab_size, :embedding_dim]
        )

    x = layers.Embedding(**embedding_kwargs)(token_ids)

    # 3. Shared Encoder: 1D Depthwise-Separable Conv TextCNN + Multi-Scale Pooling
    # Depthwise-separable convolutions dramatically reduce parameters vs standard Conv1D
    pooled_branches = []
    for k in kernel_sizes:
        conv_branch = layers.SeparableConv1D(
            filters=conv_filters,
            kernel_size=k,
            padding="same",
            activation=activation,
            name=f"sep_conv_k{k}",
        )(x)
        # Global max-pooling captures position-invariant crisis keywords
        pool_branch = layers.GlobalMaxPooling1D(name=f"global_maxpool_k{k}")(conv_branch)
        pooled_branches.append(pool_branch)

    if len(pooled_branches) > 1:
        merged_cnn = layers.concatenate(pooled_branches, axis=-1, name="concat_conv_pools")
    else:
        merged_cnn = pooled_branches[0]

    # Shared dense bottleneck
    shared_dense = layers.Dense(
        shared_dense_units,
        activation=activation,
        name="shared_dense",
    )(merged_cnn)
    shared_dense = layers.Dropout(dropout_rate, name="shared_dropout")(shared_dense)

    # 4. Auxiliary Feature Concatenation
    # Concatenate shared textual features with auxiliary deterministic inputs [regex_score, language_id]
    fused_representation = layers.concatenate(
        [shared_dense, aux_features],
        axis=-1,
        name="fused_features",
    )

    # 5. Dual Classification Heads
    # Head 1: Severity classification (info, warn, critical)
    severity_out = layers.Dense(
        num_severity_classes,
        activation="softmax",
        name=sev_head_name,
    )(fused_representation)

    # Head 2: Category classification (rescue, medical, fire, shelter, other)
    category_out = layers.Dense(
        num_category_classes,
        activation="softmax",
        name=cat_head_name,
    )(fused_representation)

    model = Model(
        inputs=[token_ids, aux_features],
        outputs={sev_head_name: severity_out, cat_head_name: category_out},
        name=model_name,
    )

    # 6. Compilation
    if compile_model:
        lr = float(train_cfg.get("learning_rate", 0.002))
        optimizer_name = train_cfg.get("optimizer", "adam").lower()
        if optimizer_name == "adam":
            opt = tf.keras.optimizers.Adam(learning_rate=lr)
        else:
            opt = tf.keras.optimizers.get(optimizer_name)

        sev_weight = float(sev_cfg.get("loss_weight", 1.0))
        cat_weight = float(cat_cfg.get("loss_weight", 0.8))

        model.compile(
            optimizer=opt,
            loss={
                sev_head_name: train_cfg.get("severity_loss", "categorical_crossentropy"),
                cat_head_name: train_cfg.get("category_loss", "categorical_crossentropy"),
            },
            loss_weights={
                sev_head_name: sev_weight,
                cat_head_name: cat_weight,
            },
            metrics={
                sev_head_name: [train_cfg.get("severity_metric", "accuracy")],
                cat_head_name: [train_cfg.get("category_metric", "accuracy")],
            },
        )

    if print_summary:
        print_model_budget_summary(model)

    return model


def build_crisis_classifier(
    vocab_size: int = 5000,
    embedding_dim: int = 25,
    max_seq_len: int = 64,
    num_severity_classes: int = 3,
    num_category_classes: int = 5,
    embedding_matrix: np.ndarray | tf.Tensor | None = None,
    trainable_embeddings: bool = True,
    aux_dim: int = 2,
) -> Model:
    """
    Convenience wrapper for backward compatibility.
    """
    cfg = {
        "model": {
            "name": "pukar_ondevice_classifier",
            "vocab_size": vocab_size,
            "embedding_dim": embedding_dim,
            "max_seq_len": max_seq_len,
            "trainable_embeddings": trainable_embeddings,
        },
        "encoder": {
            "conv_filters": 32,
            "kernel_sizes": [3, 4, 5],
            "shared_dense_units": 64,
            "dropout_rate": 0.2,
            "activation": "relu",
        },
        "auxiliary": {
            "feature_dim": aux_dim,
        },
        "heads": {
            "severity": {"name": "severity", "num_classes": num_severity_classes, "loss_weight": 1.0},
            "category": {"name": "category", "num_classes": num_category_classes, "loss_weight": 0.8},
        },
        "training": {
            "optimizer": "adam",
            "learning_rate": 0.002,
        },
    }
    emb_mat = (
        embedding_matrix.numpy()
        if isinstance(embedding_matrix, tf.Tensor)
        else embedding_matrix
    )
    return build_model(
        config=cfg,
        embedding_matrix=emb_mat,
        compile_model=True,
        print_summary=False,
    )


if __name__ == "__main__":
    # Test model build directly from CLI
    m = build_model()
    m.summary(line_length=100)
