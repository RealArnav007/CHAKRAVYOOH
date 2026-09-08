# Project Pukar — Crisis SOS Dataset Card

**Domain:** Offline Emergency Mesh SOS Message Classification  
**Target Languages:** English (`en`), Hindi (`hi` - Devanagari), Hinglish (`hinglish` - Romanized Hindi)  
**Schema:** `{text: str, severity: str, category: str, language: str, source: str}`

---

## 1. Dataset Summary & Split Sizes

The final dataset is consolidated from public disaster corpora (HumAID, CrisisNLP, Kaggle Disaster Tweets) and Groq Llama-3 teacher-generated synthetic SOS distress messages. It is partitioned via joint stratification on `(severity x language)`.

| Split | Number of Records | Percentage of Total | Parquet Artifact |
| :--- | :--- | :--- | :--- |
| **Train** | `165` | `79.7%` | [`train.parquet`](processed/train.parquet) |
| **Validation** | `21` | `10.1%` | [`val.parquet`](processed/val.parquet) |
| **Test** | `21` | `10.1%` | [`test.parquet`](processed/test.parquet) |
| **Total** | **`207`** | **100.0%** | Consolidated Master Corpus |

---

## 2. Language Distribution Across Splits

| Language | Total Count (%) | Train Count (%) | Val Count (%) | Test Count (%) |
| :--- | :--- | :--- | :--- | :--- |
| **English (`en`)** | `71` (34.3%) | `56` (33.9%) | `7` (33.3%) | `8` (38.1%) |
| **Hindi (`hi`)** | `68` (32.9%) | `54` (32.7%) | `7` (33.3%) | `7` (33.3%) |
| **Hinglish (`hinglish`)** | `68` (32.9%) | `55` (33.3%) | `7` (33.3%) | `6` (28.6%) |

---

## 3. Class Balance & Computed Loss Weights

### Severity Tiers
| Severity | Total Count | Train Split Count | Computed Loss Weight |
| :--- | :--- | :--- | :--- |
| **`critical`** | `70` | `56` | `0.9821` |
| **`warn`** | `70` | `55` | `1.0` |
| **`info`** | `67` | `54` | `1.0185` |

### Emergency Categories
| Category | Total Count | Train Split Count | Computed Loss Weight |
| :--- | :--- | :--- | :--- |
| **`rescue`** | `44` | `35` | `0.9429` |
| **`medical`** | `41` | `30` | `1.1` |
| **`fire`** | `39` | `31` | `1.0645` |
| **`shelter`** | `39` | `34` | `0.9706` |
| **`other`** | `44` | `35` | `0.9429` |

---

## 4. Provenance & Corpus Sources

```
source
groq_gen                180
pukar_seed_bootstrap     27
```

---

## 5. Quality Controls & Known Limitations

1. **PII Sanitization:** All phone numbers, email addresses, URL links, and 12-digit ID formats have been stripped.
2. **Deterministic Deduplication:** Near-identical texts with equivalent punctuation/whitespace are collapsed.
3. **Synthetic Augmentation:** Low-resource Hinglish and Hindi critical classes were augmented via Groq Llama-3.1-8B teacher prompting.
4. **Boundary Calibration:** 25% of synthetic samples represent ambiguous boundary thresholds (warn-vs-critical) to enhance model calibration on the edge.
