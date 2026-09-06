# Project Pukar — On-Device Preprocessing & Tokenization Specification

**Author:** Rishabh Rana (ML / Intelligence)  
**Target Consumer:** Arnav (Android / Kotlin Runtime)  
**Status:** Frozen Spec (Stub / Active Baseline)  
**Companion Files:** [`ml/tokenizer/tokenizer.py`](tokenizer.py) · [`services/backend/src/ml/contracts.py`](../../services/backend/src/ml/contracts.py)

---

## 1. Overview & Objective

To ensure zero prediction drift between Python offline model training and Kotlin on-device Android inference, text preprocessing and tokenization must follow a strictly deterministic, character-for-character specification.

The on-device pipeline executes **prior to packet signing and encryption** on the victim's device:

```
[Raw User Text Input]
        │
        ▼
1. Unicode Normalization (NFKC)
        │
        ▼
2. Case Normalization & Noise Cleaning
        │
        ▼
3. Multi-Script Tokenization (Regex Word Split)
        │
        ▼
4. Vocabulary Mapping & ID Encoding
        │
        ▼
5. Truncation & Padding (Fixed Shape Tensor)
        │
        ▼
[Input Tensor for TFLite: int32 (1, MAX_SEQ_LEN)]
```

---

## 2. Step-by-Step Normalization Algorithm

### Step 1: Unicode Normalization (NFKC)
- Apply standard Unicode **NFKC** (Compatibility Decomposition followed by Canonical Composition).
- **Rationale:** Vital for Hindi Devanagari characters, matras, Nukta combinations, and ligature stabilization.
- **Kotlin Reference:** `java.text.Normalizer.normalize(input, java.text.Normalizer.Form.NFKC)`

### Step 2: Case Folding & Cleaning
- Convert Latin alphabet characters to lower-case.
- Keep alphanumeric characters, the Devanagari script Unicode block (`\u0900` to `\u097F`), and key punctuation symbols: `[ . , ! ? - ]`.
- Replace all other special characters/emojis with single whitespace.
- Collapse multiple consecutive whitespace characters into a single space and strip leading/trailing spaces.

### Step 3: Token Splitting
- Split normalized string using regular expression matching:
  - Any contiguous alphanumeric or Devanagari word: `[\w\u0900-\u097F]+`
  - Or detached punctuation tokens: `[.,!?-]`

---

## 3. Tensor Encoding & Parameters (Frozen & TODOs)

| Parameter | Identifier / Symbol | Value / Status | Description |
| :--- | :--- | :--- | :--- |
| **Max Sequence Length** | `MAX_SEQ_LEN` | `64` <!-- TODO: Confirm final sequence length after full corpus token length distribution analysis --> | Fixed input tensor dimension `[1, 64]` |
| **Vocabulary Size** | `VOCAB_SIZE` | `5000` <!-- TODO: Finalize exact vocabulary prune cutoff (default: 5000) --> | Size of active token dictionary |
| **Pad Token** | `<PAD>` | `ID: 0` <!-- TODO: Pad ID frozen to 0 --> | Right-padding token for short sequences |
| **Out-of-Vocabulary (OOV)** | `<UNK>` | `ID: 1` <!-- TODO: UNK / OOV ID frozen to 1 --> | Fallback token for unseen words |
| **Tensor Data Type** | `DTYPE` | `Int32` | Native integer input format expected by TFLite interpreter |

---

## 4. Kotlin Reproduction Blueprint (For Arnav)

```kotlin
// Pseudo-code for Android on-device execution in apps/android
class PukarTextPreprocessor(private val vocab: Map<String, Int>) {
    companion object {
        const val MAX_SEQ_LEN = 64
        const val PAD_ID = 0
        const val UNK_ID = 1
    }

    fun normalize(text: String): String {
        val nfkc = java.text.Normalizer.normalize(text.trim(), java.text.Normalizer.Form.NFKC)
        val cleaned = nfkc.lowercase()
            .replace(Regex("[^\\w\\s\\u0900-\\u097F.,!?-]"), " ")
            .replace(Regex("\\s+"), " ")
            .trim()
        return cleaned
    }

    fun encode(text: String): IntArray {
        val normalized = normalize(text)
        val tokens = Regex("[\\w\\u0900-\\u097F]+|[.,!?-]")
            .findAll(normalized)
            .map { it.value }
            .toList()

        val tensor = IntArray(MAX_SEQ_LEN) { PAD_ID }
        for (i in 0 until minOf(tokens.size, MAX_SEQ_LEN)) {
            tensor[i] = vocab[tokens[i]] ?: UNK_ID
        }
        return tensor
    }
}
```

---

## 5. Verification Test Vectors

See [`ml/eval/test_vectors.json`](../eval/test_vectors.json) for sample inputs, token encodings, and expected output score distributions.
