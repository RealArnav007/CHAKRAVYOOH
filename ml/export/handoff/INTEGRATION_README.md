# Project Pukar — On-Device Android [Arnav] Integration Guide

**Target Runtime:** Android / Kotlin (API 26+)  
**Model Artifact:** `pukar_severity_int8.tflite` (~150 KB)  
**Status:** Frozen Production Spec  
**Author:** Rishabh Rana (ML / Intelligence)

---

## 1. Overview & Architecture

Project Pukar deploys a compact multi-task crisis classifier (`pukar_multitask_crisis_net`) on the victim's device to perform **instant (< 5 ms), offline triage prior to packet signing, encryption, and mesh dissemination**.

The model processes two inputs and outputs two classification heads simultaneously:

```
[Raw User Emergency Text]
          │
          ├──> 1. Normalize (NFKC, lowercase, clean) -> Tokenize -> Pad [1, 64] (int32)
          │
          └──> 2. Regex Engine -> regex_score (0-100)
               Language Identifier -> language_id (0: en, 1: hi, 2: hinglish)
               Combine to aux_features: [regex_score / 100.0, language_id] [1, 2] (float32)
                                       │
                                       ▼
                       ┌───────────────────────────────┐
                       │  pukar_severity_int8.tflite   │
                       └───────────────────────────────┘
                                       │
                    ┌──────────────────┴──────────────────┐
                    ▼                                     ▼
        severity [1, 3] (float32)             category [1, 5] (float32)
  (Calibrated [info, warn, critical])   ([rescue, medical, fire, shelter, other])
```

---

## 2. Byte-Exact Step-by-Step On-Device Flow

### Step 1: Text Normalization
Apply Unicode **NFKC** normalization, lowercase Latin characters, and preserve alphanumeric + Devanagari Unicode block (`\u0900-\u097F`) and punctuation `[ . , ! ? - ]`:
```kotlin
val normalized = Normalizer.normalize(rawText, Normalizer.Form.NFKC)
    .lowercase()
    .replace(Regex("[^a-z0-9\\u0900-\\u097F.,!?-]"), " ")
    .replace(Regex("\\s+"), " ")
    .trim()
```

### Step 2: Tokenization & ID Encoding
1. Split tokens by word boundary: `[\\w\\u0900-\\u097F]+|[.,!?-]`
2. Look up token IDs in `vocab.json`:
   - Pad token: `0` (`<PAD>`)
   - Unknown token: `1` (`<UNK>`)
3. Truncate / pad to fixed tensor shape `[1, 64]` with `int32` elements.

### Step 3: Auxiliary Feature Construction
1. Run `RegexEngine` with `regex_rules.yaml` against raw text to compute `regex_score` (0.0 to 100.0).
2. Determine message `language_id`:
   - `0.0` -> English (`en`)
   - `1.0` -> Hindi (`hi`)
   - `2.0` -> Hinglish (`hinglish`)
3. Construct `aux_features` buffer: `floatArrayOf((regex_score / 100f), language_id)`.

### Step 4: TFLite Inference Execution
Load `pukar_severity_int8.tflite` into `org.tensorflow.lite.Interpreter`:
```kotlin
val inputMap = mapOf(
    0 to tokenIdsBuffer,    // shape: [1, 64], type: Int
    1 to auxFeaturesBuffer  // shape: [1, 2],  type: Float
)
val outputMap = mapOf(
    0 to severityOutputBuffer, // shape: [1, 3], type: Float
    1 to categoryOutputBuffer  // shape: [1, 5], type: Float
)
interpreter.runForMultipleInputsOutputs(arrayOf(tokenIdsBuffer, auxFeaturesBuffer), outputMap)
```

### Step 5: Post-Processing & Score Mapping
1. **Severity Class**: `argmax(severityOutputBuffer)` mapped via `labels.yaml`:
   - `0` -> `Severity.INFO`
   - `1` -> `Severity.WARN`
   - `2` -> `Severity.CRITICAL`
2. **Category Class**: `argmax(categoryOutputBuffer)` mapped via `labels.yaml`:
   - `0` -> `Category.RESCUE`
   - `1` -> `Category.MEDICAL`
   - `2` -> `Category.FIRE`
   - `3` -> `Category.SHELTER`
   - `4` -> `Category.OTHER`
3. **Calibrated Confidence & Local Model Score**:
   - The severity head is **already temperature-calibrated in-graph**.
   - `confidence = severityOutputBuffer[severity_index]` (range `0.0` to `1.0`)
   - `local_model_score = Math.round(100f * confidence).toInt()` (range `0` to `100`)

---

## 3. Fallback Path: TFLite Task Library

If preferred, the bundle is fully compatible with the official **TensorFlow Lite Task Library** (`org.tensorflow.lite:tensorflow-lite-task-text`). Because standard Float32/Int32 input/output signatures are maintained, either the low-level `Interpreter` API or the `BertNLClassifier` / `NLClassifier` Task API can be initialized directly.

---

## 4. Verification Suite for Kotlin Unit Tests

Arnav should implement automated Kotlin test cases using the accompanying test vector JSONs:
1. `tokenizer_test_vectors.json`: Asserts tokenization matches Python character-for-character.
2. `regex_test_vectors.json`: Asserts regex scores and rule matches.
3. `inference_test_vectors.json`: Asserts full end-to-end model outputs, `confidence`, and `local_model_score`.
