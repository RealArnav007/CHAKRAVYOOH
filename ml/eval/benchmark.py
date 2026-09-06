"""
Project Pukar - Desktop Micro-Benchmark & Edge Efficiency Profiler
==================================================================

Overview:
---------
Measures on-device model efficiency by benchmarking the quantized INT8 TensorFlow Lite model
(`pukar_severity_int8.tflite`) across 1,000 representative multi-lingual inferences.

Metrics Profiled:
-----------------
1. Model Binary Footprint:
   - Size in KB and MB (validates strict < 5.0 MB edge budget gate).
2. Latency Distribution:
   - Cold-start latency (1st invocation after tensor allocation).
   - Warm single-sample latency: Min, Mean, P50 (median), P90, P95, P99, Max, StdDev.
   - Throughput (inferences per second on single CPU core).
3. Budget Validation Gate:
   - Evaluates whether P50/P95 latency satisfies the < 30.0 ms edge SLA (typically ~0.5 - 2.5 ms).
4. Machine-Readable Export:
   - Emits ml/eval/benchmark_results.json for automated pitch deck slide generation.
"""

import argparse
import datetime
import json
import logging
import os
import platform
import sys
import time
from pathlib import Path
from typing import Any

# Ensure repo root is on sys.path for direct CLI invocations
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import numpy as np  # noqa: E402
import tensorflow as tf  # noqa: E402

from ml.tokenizer.tokenizer import CrisisTokenizer  # noqa: E402
from services.backend.src.ml.regex_engine import RegexEngine  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("pukar.benchmark")

DEFAULT_TFLITE_PATH = Path("ml/export/artifacts/pukar_severity_int8.tflite")
DEFAULT_HANDOFF_TFLITE = Path("ml/export/handoff/pukar_severity_int8.tflite")
DEFAULT_LEGACY_TFLITE = Path("ml/export/artifacts/pukar_severity_classifier.tflite")
DEFAULT_VOCAB_PATH = Path("ml/tokenizer/vocab.json")
DEFAULT_OUTPUT_JSON = Path("ml/eval/benchmark_results.json")

TARGET_LATENCY_GATE_MS = 30.0
TARGET_SIZE_GATE_MB = 5.0


def resolve_model_path(custom_path: str | Path | None = None) -> Path:
    """Finds the best available TFLite model artifact."""
    if custom_path:
        p = Path(custom_path)
        if p.exists():
            return p

    for p in [DEFAULT_TFLITE_PATH, DEFAULT_HANDOFF_TFLITE, DEFAULT_LEGACY_TFLITE]:
        if p.exists():
            return p

    raise FileNotFoundError(
        f"No TFLite model found. Looked at {DEFAULT_TFLITE_PATH} and {DEFAULT_HANDOFF_TFLITE}. "
        "Run 'make export' or 'python ml/export/to_tflite.py' first."
    )


def load_tflite_interpreter(tflite_path: Path) -> tuple[tf.lite.Interpreter, dict[str, int], dict[str, int]]:
    """Initializes TFLite interpreter and maps named input/output tensor indices."""
    interpreter = tf.lite.Interpreter(model_path=str(tflite_path))
    interpreter.allocate_tensors()

    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    input_map = {}
    for item in input_details:
        name = item["name"].lower()
        shape = item["shape"]
        if "token" in name or shape[-1] == 64:
            input_map["token_ids"] = item["index"]
        elif "aux" in name or shape[-1] == 2:
            input_map["aux_features"] = item["index"]

    output_map = {}
    for item in output_details:
        name = item["name"].lower()
        shape = item["shape"]
        if "sev" in name or shape[-1] == 3:
            output_map["severity"] = item["index"]
        elif "cat" in name or shape[-1] == 5:
            output_map["category"] = item["index"]

    return interpreter, input_map, output_map


def run_benchmark(
    tflite_path: str | Path | None = None,
    vocab_path: str | Path = DEFAULT_VOCAB_PATH,
    num_runs: int = 1000,
    warmup_runs: int = 50,
    output_json_path: str | Path = DEFAULT_OUTPUT_JSON,
) -> dict[str, Any]:
    """
    Executes comprehensive latency micro-benchmarking on the TFLite model.
    """
    model_file = resolve_model_path(tflite_path)
    v_file = Path(vocab_path)

    if not v_file.exists():
        raise FileNotFoundError(f"Vocabulary not found at '{v_file}'")

    # 1. Model Artifact Size
    size_bytes = os.path.getsize(model_file)
    size_kb = size_bytes / 1024.0
    size_mb = size_bytes / (1024.0 * 1024.0)

    logger.info("Benchmarking TFLite Model: %s (%.2f KB / %.3f MB)", model_file, size_kb, size_mb)

    # 2. Setup Tokenizer & Input Data
    tokenizer = CrisisTokenizer()
    tokenizer.load_vocab(v_file)
    regex_engine = RegexEngine()

    representative_corpus = [
        # English
        {"text": "Trapped in basement during flash flood rising fast oxygen low!", "lang_id": 0.0},
        {"text": "Head injury from falling brick victim unconscious bleeding profusely", "lang_id": 0.0},
        {"text": "Drinking water exhausted and rationing food for 2 days", "lang_id": 0.0},
        {"text": "We are safe at relief camp, water receding", "lang_id": 0.0},
        # Hindi
        {"text": "सिलेंडर ब्लास्ट हुआ है और मकान में भीषण आग लग गई है लोग फंसे हैं!", "lang_id": 1.0},
        {"text": "मकान की छत गिर गई है, 3 लोग मलबे में दबे हैं तुरंत मदद भेजो", "lang_id": 1.0},
        {"text": "हम सब लोग स्कूल राहत शिविर में सुरक्षित पहुंच गए हैं", "lang_id": 1.0},
        # Hinglish
        {"text": "Ghar ke andar 4 feet pani hai aur door jam ho gaya hai jaldi boat bhejo", "lang_id": 2.0},
        {"text": "Pani chhat tak aa gaya hai, hum 4 log fase hain bachao", "lang_id": 2.0},
        {"text": "Mummy ko tez bukhar hai aur dawa nahi hai yahan", "lang_id": 2.0},
        {"text": "Hum log safe school camp me pahunch gaye hain sab theek hai", "lang_id": 2.0},
    ]

    # Pre-tokenize all inputs to isolate pure model forward pass latency
    prepared_inputs = []
    for item in representative_corpus:
        text = item["text"]
        lang_id = item["lang_id"]
        reg_score = float(regex_engine.evaluate(text)["score"]) / 100.0

        t_ids = np.array([tokenizer.encode(text)], dtype=np.int32)
        a_feat = np.array([[reg_score, lang_id]], dtype=np.float32)
        prepared_inputs.append((t_ids, a_feat))

    # 3. Interpreter Allocation & Cold-Start Timing
    t0 = time.perf_counter()
    interpreter, in_map, out_map = load_tflite_interpreter(model_file)
    allocation_latency_ms = (time.perf_counter() - t0) * 1000.0

    # First inference measurement (cold-start)
    first_t_ids, first_a_feat = prepared_inputs[0]
    t_cold_start = time.perf_counter()
    interpreter.set_tensor(in_map["token_ids"], first_t_ids)
    interpreter.set_tensor(in_map["aux_features"], first_a_feat)
    interpreter.invoke()
    _ = interpreter.get_tensor(out_map["severity"])
    _ = interpreter.get_tensor(out_map["category"])
    cold_start_latency_ms = (time.perf_counter() - t_cold_start) * 1000.0

    # 4. Warm-Up Runs
    num_inputs = len(prepared_inputs)
    for i in range(warmup_runs):
        t_ids, a_feat = prepared_inputs[i % num_inputs]
        interpreter.set_tensor(in_map["token_ids"], t_ids)
        interpreter.set_tensor(in_map["aux_features"], a_feat)
        interpreter.invoke()

    # 5. Timed Micro-Benchmark Iterations
    latencies_ms: list[float] = []
    t_bench_start = time.perf_counter()

    for i in range(num_runs):
        t_ids, a_feat = prepared_inputs[i % num_inputs]

        start = time.perf_counter()
        interpreter.set_tensor(in_map["token_ids"], t_ids)
        interpreter.set_tensor(in_map["aux_features"], a_feat)
        interpreter.invoke()
        _ = interpreter.get_tensor(out_map["severity"])
        _ = interpreter.get_tensor(out_map["category"])
        latencies_ms.append((time.perf_counter() - start) * 1000.0)

    total_bench_duration_s = time.perf_counter() - t_bench_start
    throughput_ips = num_runs / total_bench_duration_s

    # 6. Statistical Summaries
    lat_arr = np.array(latencies_ms)
    min_lat = float(np.min(lat_arr))
    mean_lat = float(np.mean(lat_arr))
    p50_lat = float(np.percentile(lat_arr, 50))
    p90_lat = float(np.percentile(lat_arr, 90))
    p95_lat = float(np.percentile(lat_arr, 95))
    p99_lat = float(np.percentile(lat_arr, 99))
    max_lat = float(np.max(lat_arr))
    std_lat = float(np.std(lat_arr))

    latency_passed = p95_lat < TARGET_LATENCY_GATE_MS
    size_passed = size_mb < TARGET_SIZE_GATE_MB

    # 7. Construct Result Payload
    now_iso = datetime.datetime.now(datetime.UTC).isoformat()
    result_payload = {
        "model_path": str(model_file),
        "model_name": "pukar_severity_int8.tflite",
        "timestamp": now_iso,
        "environment": {
            "platform": platform.platform(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "tensorflow_version": tf.__version__,
        },
        "size": {
            "size_bytes": size_bytes,
            "size_kb": round(size_kb, 2),
            "size_mb": round(size_mb, 4),
            "budget_gate_mb": TARGET_SIZE_GATE_MB,
            "gate_passed": size_passed,
        },
        "latency_ms": {
            "num_runs": num_runs,
            "warmup_runs": warmup_runs,
            "allocation_time_ms": round(allocation_latency_ms, 3),
            "cold_start_ms": round(cold_start_latency_ms, 3),
            "min": round(min_lat, 3),
            "mean": round(mean_lat, 3),
            "p50": round(p50_lat, 3),
            "p90": round(p90_lat, 3),
            "p95": round(p95_lat, 3),
            "p99": round(p99_lat, 3),
            "max": round(max_lat, 3),
            "std_dev": round(std_lat, 3),
            "throughput_inferences_per_sec": round(throughput_ips, 1),
            "target_gate_ms": TARGET_LATENCY_GATE_MS,
            "gate_passed": latency_passed,
        },
    }

    # Save to JSON
    out_json = Path(output_json_path)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(result_payload, f, indent=2)
    logger.info("Saved benchmark metrics JSON to %s", out_json)

    # 8. Print Executive Terminal Summary Report
    print("\n" + "=" * 70)
    print(" PROJECT PUKAR — TFLITE INT8 EDGE BENCHMARK REPORT")
    print("=" * 70)
    print(f" Model Artifact:       {model_file}")
    print(f" Host Environment:     {platform.system()} {platform.machine()} ({platform.processor() or 'CPU'})")
    print(f" Benchmark Iterations: {num_runs:,} single-sample runs (+ {warmup_runs} warmups)")
    print("-" * 70)
    print(" Model Size & Storage Footprint:")
    print(f"   - Disk Binary Size: {size_kb:.2f} KB ({size_mb:.3f} MB)")
    print(f"   - Size Budget Gate: < {TARGET_SIZE_GATE_MB:.1f} MB -> {'PASSED' if size_passed else 'FAILED'}")
    print("-" * 70)
    print(" On-Device Latency Profile (Single-Sample Forward Pass):")
    print(f"   - Cold-Start:       {cold_start_latency_ms:>6.2f} ms (1st invocation)")
    print(f"   - Latency P50:      {p50_lat:>6.2f} ms (Target: < {TARGET_LATENCY_GATE_MS:.1f} ms)")
    print(f"   - Latency P90:      {p90_lat:>6.2f} ms")
    print(f"   - Latency P95:      {p95_lat:>6.2f} ms (Target: < {TARGET_LATENCY_GATE_MS:.1f} ms) -> {'PASSED' if latency_passed else 'FAILED'}")
    print(f"   - Latency P99:      {p99_lat:>6.2f} ms")
    print(f"   - Min / Mean / Max: {min_lat:.2f} / {mean_lat:.2f} / {max_lat:.2f} ms (±{std_lat:.2f} ms)")
    print(f"   - Peak Throughput:  {throughput_ips:>6.1f} inferences/sec")
    print("-" * 70)
    print(f" Machine Metrics Saved: {out_json}")
    print("=" * 70 + "\n")

    return result_payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark Project Pukar TFLite multi-task model latency and size.")
    parser.add_argument("--model-path", type=str, default=None, help="Path to .tflite model")
    parser.add_argument("--vocab-path", type=str, default=str(DEFAULT_VOCAB_PATH), help="Path to vocab.json")
    parser.add_argument("--runs", type=int, default=1000, help="Number of benchmark iterations (default: 1000)")
    parser.add_argument("--warmup", type=int, default=50, help="Number of warmup iterations (default: 50)")
    parser.add_argument("--output-json", type=str, default=str(DEFAULT_OUTPUT_JSON), help="Path to output JSON")
    args = parser.parse_args()

    run_benchmark(
        tflite_path=args.model_path,
        vocab_path=args.vocab_path,
        num_runs=args.runs,
        warmup_runs=args.warmup,
        output_json_path=args.output_json,
    )


if __name__ == "__main__":
    main()
