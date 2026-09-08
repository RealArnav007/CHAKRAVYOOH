"""
Project Pukar - TFLite Export & Quantization Pipeline
Converts trained Keras models to optimized .tflite format, validates < 5 MB size budget,
and bundles the model, vocabulary, preprocessing spec, and metadata for Android [Arnav] integration.
"""

import json
import os
import shutil
from pathlib import Path

import tensorflow as tf

from ml.model.architecture import ScaleLayer


def export_tflite(
    saved_model_dir: str = "ml/model/saved_model",
    keras_model_path: str = "ml/model/pukar_model.keras",
    vocab_path: str = "ml/tokenizer/vocab.json",
    export_dir: str = "ml/export/artifacts",
) -> None:
    s_path = Path(saved_model_dir)
    k_path = Path(keras_model_path)
    out_dir = Path(export_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print("[Export] Initializing TFLite Converter...")
    if s_path.exists():
        converter = tf.lite.TFLiteConverter.from_saved_model(str(s_path))
    elif k_path.exists():
        model = tf.keras.models.load_model(
            str(k_path),
            custom_objects={"ScaleLayer": ScaleLayer},
            safe_mode=False,
        )
        converter = tf.lite.TFLiteConverter.from_keras_model(model)
    else:
        print(f"[Export] No model found at {s_path} or {k_path}. Run 'make train' first.")
        return

    # Apply optimizations & fp16 quantization
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.target_spec.supported_types = [tf.float16]

    tflite_quant_model = converter.convert()

    tflite_path = out_dir / "pukar_severity_classifier.tflite"
    with open(tflite_path, "wb") as f:
        f.write(tflite_quant_model)

    size_bytes = os.path.getsize(tflite_path)
    size_mb = size_bytes / (1024 * 1024)

    # Copy vocabulary into bundle
    if Path(vocab_path).exists():
        shutil.copy(vocab_path, out_dir / "vocab.json")

    # Generate metadata manifest
    manifest = {
        "model_name": "pukar_severity_classifier",
        "format": "TFLite (float16 quantized)",
        "input_tensor": "token_ids [1, 64] (int32)",
        "output_tensors": {
            "severity_probabilities": "[1, 3] float32 (0: info, 1: warn, 2: critical)",
            "category_probabilities": "[1, 5] float32 (0: rescue, 1: medical, 2: fire, 3: shelter, 4: other)",
            "severity_score": "[1, 1] float32 (0.0 to 100.0)",
        },
        "size_mb": round(size_mb, 3),
        "target_size_budget_mb": 5.0,
        "size_gate_passed": bool(size_mb < 5.0),
    }

    manifest_path = out_dir / "model_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print("=" * 60)
    print(" PROJECT PUKAR — TFLITE EXPORT BUNDLE READY")
    print("=" * 60)
    print(f"Artifact Path: {tflite_path}")
    print(f"Model Size: {size_mb:.2f} MB")
    print(f"Target Budget: < 5.0 MB ({'PASSED' if size_mb < 5.0 else 'FAILED'})")
    print(f"Manifest: {manifest_path}")
    print("=" * 60)


if __name__ == "__main__":
    export_tflite()
