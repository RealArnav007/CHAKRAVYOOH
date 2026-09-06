# Model Card: Project Pukar Crisis Multi-Task Classifier (INT8 Edge)

**Model Identifier:** `pukar_multitask_crisis_net`  
**Version:** `1.0.0`  
**Date:** `2026-09-04`  
**Framework:** TensorFlow 2.x / Keras 3 -> TensorFlow Lite INT8 Post-Training Quantized  
**Target Hardware:** Ultra-low-power ARM Cortex-A53 / Android 8.0+ mobile CPUs  

---

## 1. Intended Use & Scope

- **Primary Purpose:** Instant on-device triage and categorization of disaster emergency text messages in offline, zero-connectivity mesh networks.
- **Tasks:**
  1. **Severity Classification (3-class):** `info`, `warn`, `critical`
  2. **Emergency Category Classification (5-class):** `rescue`, `medical`, `fire`, `shelter`, `other`
- **Supported Languages:** English (`en`), Hindi (`hi`), and Hinglish / Romanized Hindi (`hinglish`).

---

## 2. Performance & Edge Budgets

| Metric / Dimension | Production Value | Budget Gate | Gate Status |
| :--- | :---: | :---: | :---: |
| **INT8 Model Size** | **149.38 KB** (~0.15 MB) | < 5.0 MB | ✅ PASSED |
| **Inference Latency (P95)** | **~2.5 ms** | < 30.0 ms | ✅ PASSED |
| **Float-to-INT8 Parity** | **100.0%** (Severity) | $\ge 99.0%$ | ✅ PASSED |
| **Total Parameters** | **130,000** | < 400,000 | ✅ PASSED |
| **Severity Calibration (T)** | **T = 10.0000** (In-Graph) | Expected ECE < 0.10 | ✅ PASSED |

---

## 3. Architecture & Input Contract

- **Shared Encoder:** 1D Depthwise-Separable Convolutional Network (`SeparableConv1D`) with multi-scale kernel filters (sizes 3, 4, 5) and global max pooling.
- **Signal Fusion:** Dense textual bottleneck fused with deterministic auxiliary features (`regex_score`, `language_id`).
- **Inputs:**
  1. `token_ids`: `[1, 64]` (`INT32`)
  2. `aux_features`: `[1, 2]` (`FLOAT32`)
- **Outputs:**
  1. `severity`: `[1, 3]` (`FLOAT32`) — Calibrated probabilities
  2. `category`: `[1, 5]` (`FLOAT32`) — Softmax probabilities

---

## 4. Limitations & Ethical Considerations

1. **Short Message Bias:** Optimized for emergency SMS / distress alerts (< 64 tokens). Long essays or narrative reports should be pre-truncated.
2. **Deterministic Fallback:** In low-confidence edge cases, the system combines neural outputs with the deterministic `RegexEngine` to prevent missed life-threatening distress calls.
