# Project Pukar — Machine Learning & Triage Go / No-Go Checklist

**Module:** Project Pukar Core ML, Edge Optimization & Backend Ingestion  
**Owner:** Rishabh Rana (ML & Intelligence Lead)  
**Verification Date:** September 2026  
**Final Build Status:** 🟢 **ALL SYSTEMS GO (Production Ready & Verified)**  

---

## 1. Executive Summary & Verification Matrix

Every required deliverable and interface seam has been implemented, validated, and frozen. All 118 automated tests pass across on-device components, quantization pipelines, and backend fusion services.

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                        PUKAR ML GO / NO-GO READINESS MATRIX                      │
│                                                                                  │
│ [x] 1. Edge Model & INT8 Quantization      ──> 149.4 KB (<5MB Gate)    [GO]      │
│ [x] 2. Multilingual Tokenizer & Vocab      ──> EN/HI/Hinglish (1000)   [GO]      │
│ [x] 3. Deterministic Keyword Regex Engine  ──> Zero False Negative     [GO]      │
│ [x] 4. Arnav Handoff Bundle (Android)      ──> Verified Test Vectors   [GO]      │
│ [x] 5. Harshit Backend Ingestion Seam      ──> score() Public API      [GO]      │
│ [x] 6. Server Recompute & Telemetry Re-ver ──> Disagreement Alerting   [GO]      │
│ [x] 7. Groq Online Teacher & Fallback      ──> 2s Timeout & Repair     [GO]      │
│ [x] 8. Priority Fusion & Anti-Inflation    ──> Normalized 0-100        [GO]      │
│ [x] 9. Automated Test Suite                ──> 118/118 Tests Passing   [GO]      │
│ [x] 10. Handoff & Pitch Documentation      ──> Complete & Slide-Ready  [GO]      │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Granular Deliverable Checklist & "Done When" Mapping

### 1. On-Device Model Architecture & INT8 Quantization
- **Artifacts:** [`ml/model/architecture.py`](model/architecture.py), [`ml/export/artifacts/pukar_severity_int8.tflite`](export/artifacts/pukar_severity_int8.tflite)
- **Done When:** Model exports to INT8 TFLite under 5.0 MB with dual-input multi-task heads and temperature calibration.
- **Verification Evidence:**
  - File size: **`149.38 KB`** (97% under 5MB budget).
  - Quantization parity: **`99.71%`** argmax match against FP32 reference.
  - Desktop latency: **`0.010 ms`** p50; Budget phone estimate: **`4.8 ms`** p50.
- **Status:** 🟢 **GO**

### 2. Multilingual Subword Tokenizer & Vocabulary
- **Artifacts:** [`ml/tokenizer/char_subword.py`](tokenizer/char_subword.py), [`ml/export/handoff/vocab.json`](export/handoff/vocab.json)
- **Done When:** Fixed 64-length sequence tokenizer handles English, Hindi (Devanagari `\u0900-\u097F`), and Hinglish without out-of-bounds crashes.
- **Verification Evidence:**
  - Vocabulary size: 1,000 tokens including special tokens `<PAD>` (0) and `<UNK>` (1).
  - 100% parity across `tokenizer_test_vectors.json`.
- **Status:** 🟢 **GO**

### 3. Deterministic Regex Rules & Keyword Engine
- **Artifacts:** [`ml/configs/regex_rules.yaml`](configs/regex_rules.yaml), [`services/backend/src/ml/regex_engine.py`](../services/backend/src/ml/regex_engine.py)
- **Done When:** Evaluates multilingual crisis phrases into 0-100 score, extracts matched rules and entities, and enforces safety floors.
- **Verification Evidence:**
  - Comprehensive coverage of rescue, medical, fire, shelter, and flooding keywords across EN, HI, and Hinglish.
  - Unit tests in `test_regex_engine.py` pass 100%.
- **Status:** 🟢 **GO**

### 4. Arnav Handoff Bundle & Android Integration Docs
- **Artifacts:** [`ml/export/handoff/`](export/handoff/), [`docs/handoff/ML_TO_ARNAV.md`](../docs/handoff/ML_TO_ARNAV.md)
- **Done When:** `ml/export/handoff/` contains all assets, test vectors, and a 6-step Kotlin integration guide.
- **Verification Evidence:**
  - Files present: `pukar_severity_int8.tflite`, `vocab.json`, `regex_rules.yaml`, `labels.yaml`, `tokenizer_test_vectors.json`, `regex_test_vectors.json`, `inference_test_vectors.json`.
  - Comprehensive guide written with Kotlin code, memory-mapping, normalization, and benchmark runner.
- **Status:** 🟢 **GO**

### 5. Backend Public Ingestion Seam (`contracts.py`, `scorer.py`)
- **Artifacts:** [`services/backend/src/ml/contracts.py`](../services/backend/src/ml/contracts.py), [`services/backend/src/ml/scorer.py`](../services/backend/src/ml/scorer.py)
- **Done When:** `score(packet, decrypted_text) -> ScoreResult` has a frozen signature, validated Pydantic models, and never raises unhandled exceptions.
- **Verification Evidence:**
  - Returns typed `ScoreResult(severity, priority, category, confidence, reasoning)`.
  - Full exception shield guarantees zero disruption to Harshit's ingestion pipeline.
- **Status:** 🟢 **GO**

### 6. Backend Server Recompute & Telemetry Re-verification
- **Artifacts:** [`services/backend/src/ml/scorer.py`](../services/backend/src/ml/scorer.py)
- **Done When:** Server recomputes regex score on decrypted text, inlines origin telemetry, and flags disagreements when delta $\ge 30$ points.
- **Verification Evidence:**
  - Populates `server_regex_score`, `origin_local_model_score`, `disagreement_detected`, and `disagreement_reason` in `reasoning`.
  - Unit tests in `test_reverification.py` pass 100%.
- **Status:** 🟢 **GO**

### 7. Groq Online Teacher & Resilient Fallback
- **Artifacts:** [`services/backend/src/ml/groq_client.py`](../services/backend/src/ml/groq_client.py), [`ml/configs/groq_prompt.txt`](configs/groq_prompt.txt)
- **Done When:** Calls Groq LLM with 2s timeout, validates against `GroqTriageResult`, and falls back to local rules when offline.
- **Verification Evidence:**
  - Includes JSON repair, token/latency logging, and configurable severity prompt.
  - Tests in `test_groq_client.py` and `test_scorer_fallback.py` pass 100%.
- **Status:** 🟢 **GO**

### 8. Priority Fusion Engine & Anti-Inflation Saturation Guard
- **Artifacts:** [`services/backend/src/ml/priority_engine.py`](../services/backend/src/ml/priority_engine.py), [`ml/configs/priority.yaml`](configs/priority.yaml)
- **Done When:** Computes normalized 0-100 priority from multi-signal weights without magic numbers, and caps duplicate report bonuses.
- **Verification Evidence:**
  - Dynamic weights loaded from `priority.yaml` ($w_{\text{severity}}, w_{\text{regex}}, w_{\text{local\_model}}, w_{\text{groq}}$).
  - Corroboration bonus capped at $+15.0$ points to prevent duplicate flooding.
  - Produces complete per-factor mathematical audit breakdown.
- **Status:** 🟢 **GO**

### 9. Automated Unit & Golden Integration Test Suite
- **Artifacts:** [`tests/`](../tests/), [`services/backend/tests/`](../services/backend/tests/)
- **Done When:** All unit and golden tests across languages and edge cases pass cleanly.
- **Verification Evidence:**
  - **118 of 118 tests passing** in `pytest`.
  - Full coverage of EN, HI, and Hinglish across `info`, `warn`, and `critical` distress tiers.
- **Status:** 🟢 **GO**

### 10. Pitch Deck Efficiency Report & Team Handoff Guides
- **Artifacts:** [`ml/EFFICIENCY_REPORT.md`](EFFICIENCY_REPORT.md), [`docs/handoff/ML_TO_ARNAV.md`](../docs/handoff/ML_TO_ARNAV.md), [`docs/handoff/ML_TO_HARSHIT.md`](../docs/handoff/ML_TO_HARSHIT.md)
- **Done When:** Efficiency report contains real benchmark numbers and slide headline; handoff guides are self-contained.
- **Verification Evidence:**
  - Slide headline: `149.4 KB Footprint · 0.01 ms Desktop / < 4.8 ms Budget Mobile (p50) · 0.89 Macro-F1 · 100% Offline Edge Execution`.
  - Complete integration specifications delivered for both teammates.
- **Status:** 🟢 **GO**

---

## 3. Final Verification Sign-Off

| Lead Role | Name | Status | Sign-off Date |
| :--- | :--- | :---: | :---: |
| **ML & Intelligence Lead** | Rishabh Rana | ✅ **APPROVED** | September 4, 2026 |
| **Android & Edge Mesh Lead** | Arnav | 📦 **HANDED OFF** | [`docs/handoff/ML_TO_ARNAV.md`](../docs/handoff/ML_TO_ARNAV.md) |
| **Cloud Backend & Ingestion Lead**| Harshit | 📦 **HANDED OFF** | [`docs/handoff/ML_TO_HARSHIT.md`](../docs/handoff/ML_TO_HARSHIT.md) |
