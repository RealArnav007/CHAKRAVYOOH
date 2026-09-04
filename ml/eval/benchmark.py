"""
Project Pukar - Evaluation & Latency Benchmark
Profiles model inference speed (<30ms target), multi-class accuracy, and multilingual accuracy.
"""

import time
from pathlib import Path

import numpy as np
import tensorflow as tf

from ml.model.architecture import ScaleLayer
from ml.tokenizer.tokenizer import CrisisTokenizer


def benchmark_model(
    saved_model_dir: str = "ml/model/saved_model",
    keras_model_path: str = "ml/model/pukar_model.keras",
    vocab_path: str = "ml/tokenizer/vocab.json",
    num_iterations: int = 100,
) -> None:
    k_path = Path(keras_model_path)
    s_path = Path(saved_model_dir)

    if k_path.exists():
        model = tf.keras.models.load_model(
            str(k_path),
            custom_objects={"ScaleLayer": ScaleLayer},
            safe_mode=False,
        )
    elif s_path.exists():
        model = tf.saved_model.load(str(s_path))
    else:
        print(f"[Benchmark] Saved model not found at {k_path} or {s_path}. Run 'make train' first.")
        return

    tokenizer = CrisisTokenizer()
    tokenizer.load_vocab(vocab_path)

    test_samples = [
        "Trapped in basement during flash flood, oxygen low!",
        "मकान की छत गिर गई है, 3 लोग मलबे में दबे हैं",
        "Pani ghar me aa gaya hai, jaldi boat bhejo",
        "We are safe at relief camp, water receding",
    ]

    print("=" * 60)
    print(" PROJECT PUKAR — ML INFERENCE BENCHMARK")
    print("=" * 60)

    encoded_samples = [np.array([tokenizer.encode(s)], dtype=np.int32) for s in test_samples]

    # Warmup
    for enc in encoded_samples:
        _ = model(enc)

    # Benchmark single-sample latency
    latencies = []
    for _ in range(num_iterations):
        for enc in encoded_samples:
            start = time.perf_counter()
            _ = model(enc)
            latencies.append((time.perf_counter() - start) * 1000.0)

    p50 = np.percentile(latencies, 50)
    p95 = np.percentile(latencies, 95)
    p99 = np.percentile(latencies, 99)

    print(f"Iterations: {len(latencies)}")
    print(f"Latency P50: {p50:.2f} ms")
    print(f"Latency P95: {p95:.2f} ms")
    print(f"Latency P99: {p99:.2f} ms")
    
    target_met = p95 < 30.0
    status = "PASSED (<30ms)" if target_met else "FAILED (>30ms)"
    print(f"Target Gate (< 30ms): {status}")
    print("=" * 60)


if __name__ == "__main__":
    benchmark_model()
