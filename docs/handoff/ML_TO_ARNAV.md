# Project Pukar — Android On-Device ML Integration Guide (For Arnav)

**Target Engineer:** Arnav (Android & Edge Mesh Lead)  
**Author:** Rishabh Rana (ML & Intelligence Lead)  
**Source Directory:** [`ml/export/handoff/`](../../ml/export/handoff/)  
**Status:** Frozen Production Spec — Complete & Verified  

---

## 1. Handoff Bundle Inventory (`ml/export/handoff/`)

All necessary assets have been exported, validated, and placed in [`ml/export/handoff/`](../../ml/export/handoff/). Copy these directly into the Android app's `app/src/main/assets/` directory:

| Filename | File Type | Size | Purpose |
| :--- | :---: | :---: | :--- |
| **`pukar_severity_int8.tflite`** | Binary | `149.38 KB` | Quantized multi-task neural network for on-device severity and category classification. |
| **`vocab.json`** | JSON | `4.75 KB` | Multilingual subword/character token vocabulary mapping (1,000 tokens including Devanagari). |
| **`regex_rules.yaml`** | YAML | `6.87 KB` | Deterministic keyword and regex patterns for emergency score computation and safety floor. |
| **`labels.yaml`** | YAML | `1.53 KB` | Class index to string mapping for Severity (`info`, `warn`, `critical`) & Category (`rescue`, `medical`, `fire`, `shelter`, `other`). |
| **`tokenizer_test_vectors.json`**| JSON | `9.77 KB` | Unit test assertions verifying Kotlin tokenization matches Python character-for-character. |
| **`regex_test_vectors.json`** | JSON | `10.33 KB` | Unit test assertions verifying Kotlin RegexEngine score computation. |
| **`inference_test_vectors.json`**| JSON | `13.70 KB` | Golden end-to-end test vectors asserting full TFLite inference outputs, confidence, and scores. |
| **`PREPROCESSING_SPEC.md`** | Markdown | `4.18 KB` | Exact byte-for-byte normalization, regex matching, and tokenization specification. |
| **`MODEL_CARD.md`** | Markdown | `2.23 KB` | Model architecture, input/output tensors, quantization details, and intended use. |
| **`INTEGRATION_README.md`** | Markdown | `4.81 KB` | High-level overview of on-device inference pipeline. |

---

## 2. Model Tensor Specifications

### Input Tensors (2 Inputs)
1. **`token_ids`**:
   - **Tensor Index:** `0`
   - **Shape:** `[1, 64]` (Batch size = 1, Max Sequence Length = 64)
   - **Data Type:** `int32` (Kotlin `IntArray(64)`)
   - **Special Tokens:** `<PAD> = 0`, `<UNK> = 1`
2. **`aux_features`**:
   - **Tensor Index:** `1`
   - **Shape:** `[1, 2]`
   - **Data Type:** `float32` (Kotlin `FloatArray(2)`)
   - **Contents:** `[normalized_regex_score, language_id]`
     - `normalized_regex_score = regex_score / 100.0f` (Range: `0.0` to `1.0`)
     - `language_id`: `0.0` (English `en`), `1.0` (Hindi `hi`), `2.0` (Hinglish `hinglish`)

### Output Tensors (2 Outputs)
1. **`severity_probs`**:
   - **Tensor Index:** `0`
   - **Shape:** `[1, 3]`
   - **Data Type:** `float32`
   - **Classes:** `[0: "info", 1: "warn", 2: "critical"]`
   - **Properties:** Temperature-calibrated softmax probabilities summing to 1.0.
2. **`category_probs`**:
   - **Tensor Index:** `1`
   - **Shape:** `[1, 5]`
   - **Data Type:** `float32`
   - **Classes:** `[0: "rescue", 1: "medical", 2: "fire", 3: "shelter", 4: "other"]`
   - **Properties:** Softmax probabilities summing to 1.0.

---

## 3. The 6-Step On-Device Triage Flow (Kotlin Implementation)

Implement the on-device inference pipeline in Android using these exact 6 steps:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. Asset Loading  ──> Map TFLite model, vocab.json, and regex_rules.yaml    │
│         │                                                                   │
│ 2. Normalization  ──> NFKC Unicode normalization, lowercase, strip noise    │
│         │                                                                   │
│ 3. Tokenization   ──> Word boundary token split, map to IDs, pad to [1, 64] │
│         │                                                                   │
│ 4. Aux Features   ──> Compute Regex score & language ID -> shape [1, 2]     │
│         │                                                                   │
│ 5. TFLite Pass    ──> interpreter.runForMultipleInputsOutputs(...)          │
│         │                                                                   │
│ 6. Post-Process   ──> Argmax, confidence score, and deterministic floor     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Step 1: Asset Loading & Initialization
Memory-map the model file and parse the vocabulary and regex rules during app startup:

```kotlin
import android.content.Context
import org.tensorflow.lite.Interpreter
import java.io.FileInputStream
import java.nio.channels.FileChannel
import org.json.JSONObject

class PukarOnDeviceTriage(private val context: Context) {
    private val interpreter: Interpreter
    private val vocabMap: Map<String, Int>

    init {
        val modelBuffer = context.assets.openFd("pukar_severity_int8.tflite").use { fd ->
            FileInputStream(fd.fileDescriptor).channel.map(
                FileChannel.MapMode.READ_ONLY,
                fd.startOffset,
                fd.declaredLength
            )
        }
        val options = Interpreter.Options().apply {
            setNumThreads(2) // Optimal for ARM big.LITTLE architecture
        }
        interpreter = Interpreter(modelBuffer, options)
        
        // Load vocabulary
        val vocabJson = context.assets.open("vocab.json").bufferedReader().use { it.readText() }
        val jsonObj = JSONObject(vocabJson)
        val map = mutableMapOf<String, Int>()
        jsonObj.keys().forEach { key -> map[key] = jsonObj.getInt(key) }
        vocabMap = map
    }
}
```

### Step 2: Text Normalization
Apply Unicode **NFKC** normalization, convert to lowercase, preserve alphanumeric characters, the Devanagari block (`\u0900-\u097F`), and emergency punctuation (`[.,!?-]`):

```kotlin
import java.text.Normalizer

fun normalizeText(rawText: String): String {
    return Normalizer.normalize(rawText, Normalizer.Form.NFKC)
        .lowercase()
        .replace(Regex("[^a-z0-9\\u0900-\\u097F.,!?-]"), " ")
        .replace(Regex("\\s+"), " ")
        .trim()
}
```

### Step 3: Tokenization & Fixed-Length Padding
Tokenize words and punctuation symbols, looking up indices in `vocab.json` and padding to length 64:

```kotlin
fun tokenize(normalizedText: String, maxLen: Int = 64): Array<IntArray> {
    val tokenRegex = Regex("[\\w\\u0900-\\u097F]+|[.,!?-]")
    val matches = tokenRegex.findAll(normalizedText).map { it.value }.toList()
    
    val tokenIds = IntArray(maxLen) { 0 } // Default to <PAD> = 0
    val count = minOf(matches.size, maxLen)
    for (i in 0 until count) {
        val token = matches[i]
        tokenIds[i] = vocabMap[token] ?: 1 // <UNK> = 1 if not in vocab
    }
    return arrayOf(tokenIds) // Shape: [1, 64]
}
```

### Step 4: Auxiliary Feature Extraction
Compute the deterministic regex score (0-100) using `regex_rules.yaml` and detect the language ID:

```kotlin
fun extractAuxFeatures(rawText: String, regexScore: Float, language: String): Array<FloatArray> {
    val langId = when (language.lowercase()) {
        "hi", "hindi" -> 1.0f
        "hinglish" -> 2.0f
        else -> 0.0f // default to English "en"
    }
    val normalizedRegex = (regexScore / 100.0f).coerceIn(0.0f, 1.0f)
    return arrayOf(floatArrayOf(normalizedRegex, langId)) // Shape: [1, 2]
}
```

### Step 5: TFLite Forward Pass
Execute multi-input, multi-output inference:

```kotlin
fun runInference(
    tokenIdsTensor: Array<IntArray>,
    auxFeaturesTensor: Array<FloatArray>
): Pair<FloatArray, FloatArray> {
    val severityOutput = Array(1) { FloatArray(3) }
    val categoryOutput = Array(1) { FloatArray(5) }

    val inputs = arrayOf(tokenIdsTensor, auxFeaturesTensor)
    val outputs = mutableMapOf<Int, Any>(
        0 to severityOutput,
        1 to categoryOutput
    )

    interpreter.runForMultipleInputsOutputs(inputs, outputs)
    return Pair(severityOutput[0], categoryOutput[0])
}
```

### Step 6: Post-Processing & Safety Floor
Extract classes, calibrated confidence, local model score, and apply the deterministic safety floor:

```kotlin
data class OnDeviceTriageResult(
    val severity: String,
    val category: String,
    val confidence: Float,
    val localModelScore: Int,
    val regexScore: Int
)

fun postProcess(
    severityProbs: FloatArray,
    categoryProbs: FloatArray,
    regexScore: Int
): OnDeviceTriageResult {
    val severityLabels = arrayOf("info", "warn", "critical")
    val categoryLabels = arrayOf("rescue", "medical", "fire", "shelter", "other")

    var sevIdx = severityProbs.indices.maxByOrNull { severityProbs[it] } ?: 0
    val catIdx = categoryProbs.indices.maxByOrNull { categoryProbs[it] } ?: 4

    // Deterministic Safety Floor: If regex score indicates severe distress, enforce floor
    if (regexScore >= 80 && sevIdx < 2) {
        sevIdx = 2 // Floor to "critical"
    } else if (regexScore >= 50 && sevIdx < 1) {
        sevIdx = 1 // Floor to "warn"
    }

    val confidence = severityProbs[sevIdx]
    val localModelScore = (confidence * 100.0f).toInt().coerceIn(0, 100)

    return OnDeviceTriageResult(
        severity = severityLabels[sevIdx],
        category = categoryLabels[catIdx],
        confidence = confidence,
        localModelScore = localModelScore,
        regexScore = regexScore
    )
}
```

---

## 4. Packet Telemetry Packaging for Mesh Dispatch

When Arnav's mesh layer builds the emergency packet header, pack these fields into the signed metadata payload:

```json
{
  "packet_id": "pkt-9812-76fa",
  "device_id": "dev-node-041",
  "timestamp": 1725439821000,
  "hop_count": 0,
  "severity": "critical",
  "regex_score": 90,
  "local_model_score": 88,
  "confidence": 0.88,
  "category": "rescue",
  "language": "hinglish"
}
```

*Note: Harshit's backend ingestion server will reverify these fields and fuse them with cloud intelligence upon gateway arrival.*

---

## 5. Test-Vector Verification Checklist for Android Unit Tests

Run these test suites inside your Android instrumented / JUnit tests to ensure 100% parity with the Python reference implementation:

- [ ] **Tokenizer Parity (`tokenizer_test_vectors.json`):**
  - Iterate through the 25 test samples across English, Hindi, and Hinglish.
  - Assert `tokenize(sample.text) == sample.expected_token_ids`.
- [ ] **Regex Score Parity (`regex_test_vectors.json`):**
  - Run `RegexEngine.score(sample.text)` on the test phrases.
  - Assert `abs(computed_score - sample.expected_regex_score) == 0`.
- [ ] **End-to-End Inference Parity (`inference_test_vectors.json`):**
  - Run the complete 6-step triage pipeline on all golden inference vectors.
  - Assert `predicted_severity == sample.expected_severity`.
  - Assert `predicted_category == sample.expected_category`.
  - Assert `abs(predicted_confidence - sample.expected_confidence) < 0.05`.
- [ ] **Latency Benchmark Gate:**
  - Execute 1,000 runs using `PukarBenchmarkRunner.kt`.
  - Confirm p50 latency is $< 10.0\text{ ms}$ on target test devices (e.g. Redmi 9A / Galaxy M12).

---

## 6. Incident Screen Dispatcher UI Payload (Rendered by Arnav)

When the incident detail screen renders on the Android Dispatcher console, the backend ML pipeline delivers structured intelligence, one-line commander briefing, and recommended resources via the versioned `ScoreResult` (version `2.0.0`):

```json
{
  "schema_version": "2.0.0",
  "severity": "critical",
  "priority": 88,
  "category": "rescue",
  "confidence": 0.89,
  "needs_human_review": false,
  "injection_suspected": false,
  "injection_reasons": [],
  "false_alarm_likelihood": 0.0,
  "false_alarm_reasons": [],
  "escalation_signal": 0.88,
  "correlation_id": "trace-8f92-a1b4",
  "briefing": {
    "headline": "Structural collapse, 3 trapped incl. child — rescue + ambulance, critical priority",
    "recommended_resources": [
      "ambulance",
      "rescue_team",
      "medical_supplies"
    ],
    "confidence": 0.92
  },
  "recommended_resources": [
    "ambulance",
    "rescue_team",
    "medical_supplies"
  ],
  "entities": {
    "people_count": 3,
    "injuries": ["general_trauma", "head_injury"],
    "hazards": ["structural_collapse"],
    "needs": ["rescue", "medical"],
    "landmarks": ["near city hospital"],
    "mobility": "trapped",
    "vulnerable": ["child"]
  },
  "correlation": {
    "match_id": "inc-001",
    "similarity": 0.89,
    "is_duplicate": true,
    "cluster_hint": "North Delhi Flood Collapse"
  }
}
```

### UI Integration Fields for Incident Screen:
* **`schema_version`** $\to$ `"2.0.0"` indicates rich tactical briefing, extraction, and correlation support.
* **`needs_human_review`** $\to$ **Commander Review Badge**: Render an amber/yellow warning badge `"⚠️ Needs Human Review"` / `"Manual Verification Advised"` if `true`. Triggered when model signals diverge or aggregate confidence $< 0.65$.
* **`briefing.headline`** $\to$ **Top Banner**: Crisp, $\le 18$ word imperative dispatcher summary (e.g. *"Structural collapse, 3 trapped — deploy rescue team"*).
* **`recommended_resources` / `briefing.recommended_resources`** $\to$ **Quick-Action Dispatch Buttons**: 1-tap resource allocation chips (`ambulance`, `rescue_team`, `fire_truck`, `evacuation`, `medical_supplies`).
* **`entities`**:
  - **`entities.people_count`** $\to$ Victim headcount chip (e.g. `👥 3 victims`).
  - **`entities.vulnerable`** $\to$ Red highlight badge (e.g. `⚠️ Child`, `⚠️ Elderly`).
  - **`entities.hazards`** $\to$ Warning hazard tags (e.g. `🔥 Fire`, `🌊 Flood`, `🏚️ Structural Collapse`).
  - **`entities.mobility`** $\to$ Entrapment indicator (`trapped` vs `mobile`).
  - **`entities.landmarks`** $\to$ Tactical reference location pin.
  - **`entities.injuries`** $\to$ Medical triage priority list.
* **`correlation.is_duplicate`** $\to$ Link incident to existing cluster `correlation.match_id` without creating duplicate pins on the map.


