# Project Pukar — Model Evaluation & Reliability Benchmark Report
**Generated:** `2026-09-04 07:34:18 UTC`  
**Dataset:** `ml/datasets/processed/test.parquet` (N = 21 holdout samples)  
**Severity Calibrated Temperature:** `T = 10.0000`

---
## 1. Executive Summary & Overall Test Performance

| Metric Head | Macro-F1 | Overall Accuracy | Target Threshold | Status |
| :--- | :---: | :---: | :---: | :---: |
| **Severity (3-class)** | **0.1667** | 33.3% | $\ge 0.85$ | ⚠️ GAP |
| **Category (5-class)** | **0.0889** | 28.6% | $\ge 0.80$ | ⚠️ GAP |
| **Joint Exact Match**  | — | **14.3%** | — | — |

---
## 2. Per-Class Granular Breakdown

### Severity Classification Head
| Class | Precision | Recall | F1-Score | Support |
| :--- | :---: | :---: | :---: | :---: |
| `info` | 0.3333 | 1.0000 | **0.5000** | 7 |
| `warn` | 0.0000 | 0.0000 | **0.0000** | 8 |
| `critical` | 0.0000 | 0.0000 | **0.0000** | 6 |

### Category Classification Head
| Class | Precision | Recall | F1-Score | Support |
| :--- | :---: | :---: | :---: | :---: |
| `rescue` | 0.0000 | 0.0000 | **0.0000** | 4 |
| `medical` | 0.0000 | 0.0000 | **0.0000** | 5 |
| `fire` | 0.0000 | 0.0000 | **0.0000** | 5 |
| `shelter` | 0.0000 | 0.0000 | **0.0000** | 1 |
| `other` | 0.2857 | 1.0000 | **0.4444** | 6 |

---
## 3. Confusion Matrices

### Severity Confusion Matrix (`rows: true`, `cols: predicted`)
| True \ Pred | **info** | **warn** | **critical** |
| :--- | :---: | :---: | :---: |
| **info** | 7 | 0 | 0 |
| **warn** | 8 | 0 | 0 |
| **critical** | 6 | 0 | 0 |

### Category Confusion Matrix (`rows: true`, `cols: predicted`)
| True \ Pred | **rescue** | **medical** | **fire** | **shelter** | **other** |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **rescue** | 0 | 0 | 0 | 0 | 4 |
| **medical** | 0 | 0 | 0 | 0 | 5 |
| **fire** | 0 | 0 | 0 | 0 | 5 |
| **shelter** | 0 | 0 | 0 | 0 | 1 |
| **other** | 0 | 0 | 0 | 0 | 6 |

---
## 4. Multilingual Language Slices & Disparity Audit

| Language Slice | Sample Count (N) | Severity F1 | Category F1 | Combined F1 | Gap to Mean | Slice Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **EN** | 8 | 0.1818 | 0.0444 | 0.1131 | +0.0147 | ✅ Balanced |
| **HI** | 7 | 0.1481 | 0.0500 | 0.0991 | +0.0287 | ✅ Balanced |
| **HINGLISH** | 6 | 0.1667 | 0.1600 | 0.1633 | -0.0355 | ✅ Balanced |

---
## 5. Robustness & Edge Stress Probes

| Stress Condition | Severity F1 | $\Delta$ Sev F1 | Category F1 | $\Delta$ Cat F1 | Resilience Rating |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Typo Injection (p=0.20 keyboard noise)** | 0.1667 | -0.0000 | 0.0889 | -0.0000 | 🟢 Excellent (<5% drop) |
| **Vowel Dropping (SMS / Chat shorthand)** | 0.1667 | -0.0000 | 0.0889 | -0.0000 | 🟢 Excellent (<5% drop) |
| **Truncation (50% token cut / SMS limit)** | 0.1667 | -0.0000 | 0.0889 | -0.0000 | 🟢 Excellent (<5% drop) |

---
## 6. Error Analysis & Worst Misclassifications

Full details for top misclassifications dumped to [`ml/eval/errors.csv`](file:///Users/rana/Documents/Pukar/ml/eval/errors.csv).

| Sample Text | Lang | True / Pred Severity | True / Pred Category | Error Type | Conf |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `other situation update hai, severity is criti...` | hinglish | `critical` → `info` | `other` → `other` | Severity(critical->info) | 0.39 |
| `other situation update hai, severity is criti...` | hinglish | `critical` → `info` | `other` → `other` | Severity(critical->info) | 0.39 |
| `medical situation update hai, severity is inf...` | hinglish | `info` → `info` | `medical` → `other` | Category(medical->other) | 0.39 |
| `other situation update hai, severity is warn,...` | hinglish | `warn` → `info` | `other` → `other` | Severity(warn->info) | 0.39 |
| `fire के संबंध में warn स्थिति है, सूचना दर्ज ...` | hi | `warn` → `info` | `fire` → `other` | Severity(warn->info) + Category(fire->other) | 0.37 |
| `Mummy ko tez bukhar hai aur dawa nahi hai yah...` | hinglish | `warn` → `info` | `medical` → `other` | Severity(warn->info) + Category(medical->other) | 0.37 |
| `fire के संबंध में warn स्थिति है, सूचना दर्ज ...` | hi | `warn` → `info` | `fire` → `other` | Severity(warn->info) + Category(fire->other) | 0.37 |
| `rescue के संबंध में warn स्थिति है, सूचना दर्...` | hi | `warn` → `info` | `rescue` → `other` | Severity(warn->info) + Category(rescue->other) | 0.37 |
| `medical के संबंध में info स्थिति है, सूचना दर...` | hi | `info` → `info` | `medical` → `other` | Category(medical->other) | 0.36 |
| `shelter के संबंध में critical स्थिति है, सूचन...` | hi | `critical` → `info` | `shelter` → `other` | Severity(critical->info) + Category(shelter->other) | 0.36 |
