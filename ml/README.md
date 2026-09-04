# Project Pukar — Machine Learning & Intelligence Slice

**Owner:** Rishabh Rana  
**Domain:** ML / On-Device Severity & Backend Priority Engine  
**Companion Documents:** [`docs/Beacon_v4_Master_PRD.md`](../docs/Beacon_v4_Master_PRD.md) · [`docs/Beacon_PRD_Rishabh_ML.md`](../docs/Beacon_PRD_Rishabh_ML.md)

---

## 1. System Architecture: Two-Tier Intelligence

In Project Pukar's offline-first emergency mesh network, distress messages hop peer-to-peer over Wi-Fi Aware/Bluetooth Low Energy before reaching a gateway phone that syncs with the cloud.

Because packets are **end-to-end encrypted (E2EE) and signed at origin**, intermediate relay nodes cannot inspect or score the payload. To solve this, Pukar implements a strict **two-tier intelligence design**:

```
┌────────────────────────────────────────────────────────┐
│  TIER 1: ORIGIN PHONE (Offline Edge)                   │
│                                                        │
│  [User SOS Text]                                       │
│         │                                              │
│         ▼                                              │
│  [Regex Engine] ──────► regex_score (0-100)            │
│         │                                              │
│         ▼                                              │
│  [TFLite Classifier] ──► local_model_score (0-100)     │
│   (Distilled Student)    severity: info|warn|critical  │
│                          category: rescue|med|fire...  │
│         │                                              │
│         ▼                                              │
│  [Signed Immutable Header] ───► [Mesh Relay Hopping]   │
└────────────────────────────────────────────────────────┘
                           │ (P2P hops - payload opaque)
                           ▼
┌────────────────────────────────────────────────────────┐
│  TIER 2: CLOUD BACKEND (Online Incident Ingestion)     │
│                                                        │
│  [Decrypted Payload]                                   │
│         │                                              │
│         ├─► [Backend Regex Engine] (Identical Rules)   │
│         ├─► [Groq Llama-3 Teacher] (Structured JSON)   │
│         │                                              │
│         ▼                                              │
│  [Priority Engine Fusion]                              │
│    w1·severity + w2·regex + w3·local + w4·groq         │
│    + corroboration + location_weight + time_decay      │
│         │                                              │
│         ▼                                              │
│  [Auditable AI Transparency Breakdown] ──► Dispatch Map│
└────────────────────────────────────────────────────────┘
```

### Tier 1: Distilled Student (On-Device, Offline)
- **Role:** Generates an immediate severity grading and category on the victim's device before packet signing and encryption.
- **Runtime Constraints:**
  - **Size:** **< 5 MB** hard cap for model and dictionary assets.
  - **Inference Latency:** **< 30 ms** on low-end ARM Cortex-A53 / Snapdragon 400-series hardware.
  - **Deterministic Fallback:** If the neural model fails to initialize or memory pressure is high, the regex rule engine guarantees an instant, deterministic score floor.

### Tier 2: Groq Teacher & Priority Fusion (Backend Cloud)
- **Role:** Deep semantic extraction, entity extraction (trapped victims, medical needs, hazards), and dynamic incident priority fusion.
- **Auditable Priority Engine:** Fuses on-device scores, backend regex, Groq semantic confidence, spatial density (corroboration), and temporal escalation into a normalized priority score (0–100) with a per-factor reasoning breakdown.

---

## 2. Multilingual Target: English, Hindi & Hinglish

Disaster communication in the Indian subcontinent spans multiple languages, scripts, and colloquial mixtures:
1. **Standard English:** *"Severe flooding near bridge, 3 people trapped on roof."*
2. **Standard Hindi (Devanagari):** *"बाढ़ का पानी घर में घुस गया है, तुरंत मदद चाहिए।"*
3. **Hinglish (Code-Mixed Romanized Hindi):** *"Pani bohot badh gaya hai, ghar me 4 log fase hain, jaldi rescue team bhejo."*

The tokenizer, dataset synthesis pipeline (`ml/data_gen/`), and training architectures are explicitly optimized for code-mixed tokenization, transliterated disaster keywords, and multi-dialect crisis phrases.

---

## 3. Directory Layout

```
ml/
├── datasets/            # Raw and processed corpora, labeling rubric (RUBRIC.md), dataset cards
├── data_gen/            # Groq-based synthetic generation & automated teacher labeling
├── tokenizer/           # Lightweight, portable subword/unigram tokenizer + vocabulary
├── model/               # Classifier architectures (BiLSTM / 1D-CNN / Distilled Transformer) & training scripts
├── eval/                # Multi-class metrics, latency benchmarks, edge memory profiling
├── export/              # TFLite quantization (int8/fp16), metadata tagging, and artifact bundle
├── configs/             # Shared YAML configs: regex rules, priority weights, category maps
└── README.md            # Architecture & specifications
```

---

## 4. Performance & Operational Gates

| Metric | Target | Verification Tool |
| :--- | :--- | :--- |
| **Model Size** | `< 5 MB` (TFLite quantized) | `ml/export/validate_bundle.py` |
| **Inference Time** | `< 30 ms` per packet | `ml/eval/benchmark_latency.py` |
| **Multilingual Coverage** | EN + HI (Devanagari) + Hinglish | `ml/eval/eval_multilingual.py` |
| **Fallback Reliability** | 100% deterministic coverage | `pytest tests/test_regex_engine.py` |
| **Explainability** | Full factor breakdown JSON | `tests/test_priority_engine.py` |

---

## 5. Quickstart

```bash
# 1. Setup virtual environment and install dependencies
make setup

# 2. Generate multilingual crisis dataset via Groq Teacher
make gen-data

# 3. Train on-device lightweight classifier
make train

# 4. Evaluate F1-score, latency, and calibration
make eval

# 5. Export quantized TFLite artifact for Android integration
make export

# 6. Run comprehensive unit and contract tests
make test
```
