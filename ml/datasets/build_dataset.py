"""
Project Pukar - Master Training Corpus Builder & Stratifier
Merges public, synthetic, and autolabeled corpora with PII sanitization, deduplication,
joint stratification (severity x language), class weight calculation, and DATASET_CARD.md emission.
"""

import hashlib
import logging
import re
import unicodedata
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_class_weight

from services.backend.src.ml.contracts import Category, Severity

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("BuildDataset")


def normalize_text_for_dedup(text: str) -> str:
    """
    Normalizes whitespace, lowercases, and strips non-alphanumeric punctuation
    to produce a canonical string for deduplication.
    """
    if not text:
        return ""
    t = text.lower().strip()
    t = re.sub(r"[^\w\s\u0900-\u097F]", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def compute_text_hash(text: str) -> str:
    norm = normalize_text_for_dedup(text)
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()


def sanitize_text(text: str) -> str:
    """
    Strips PII (phone numbers, emails, Aadhaar/ID numbers, URLs),
    normalizes Unicode (NFKC), and collapses whitespace.
    """
    if not text or not isinstance(text, str):
        return ""

    # 1. Unicode normalization (NFKC)
    t = unicodedata.normalize("NFKC", text.strip())

    # 2. Strip URLs
    t = re.sub(r"https?://\S+|www\.\S+", " ", t)

    # 3. Strip Email addresses
    t = re.sub(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", " ", t)

    # 4. Strip Indian 10-digit phone numbers & +91 prefixes
    t = re.sub(r"\b(?:\+?91[\-\s]?)?[6-9]\d{9}\b", " ", t)
    # Generic international / 7-12 digit phone patterns
    t = re.sub(r"\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b", " ", t)

    # 5. Strip 12-digit Aadhaar / ID formats (e.g. 1234 5678 9012)
    t = re.sub(r"\b\d{4}\s\d{4}\s\d{4}\b", " ", t)

    # 6. Normalize whitespace
    t = re.sub(r"\s+", " ", t).strip()
    return t


def compute_and_save_class_weights(
    train_df: pd.DataFrame,
    output_path: str = "ml/configs/class_weights.yaml",
) -> dict[str, Any]:
    """
    Computes balanced inverse-frequency class weights for Severity (3 classes) and Category (5 classes).
    Saves the weights to YAML.
    """
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    # 1. Severity class weights
    sev_classes = [s.value for s in Severity]
    sev_weights_arr = compute_class_weight(
        class_weight="balanced",
        classes=np.array(sev_classes),
        y=train_df["severity"].values,
    )
    severity_weights = {str(cls): round(float(w), 4) for cls, w in zip(sev_classes, sev_weights_arr, strict=False)}

    # 2. Category class weights
    cat_classes = [c.value for c in Category]
    cat_weights_arr = compute_class_weight(
        class_weight="balanced",
        classes=np.array(cat_classes),
        y=train_df["category"].values,
    )
    category_weights = {str(cls): round(float(w), 4) for cls, w in zip(cat_classes, cat_weights_arr, strict=False)}

    data = {
        "version": "1.0.0",
        "description": "Balanced inverse-frequency class weights computed from training split",
        "severity_weights": severity_weights,
        "category_weights": category_weights,
    }

    with open(out_file, "w", encoding="utf-8") as f:
        yaml.dump(data, f, indent=2, sort_keys=True)

    logger.info(f"Saved computed class weights to {out_file}")
    return data


def stratified_split(
    df: pd.DataFrame,
    train_ratio: float = 0.80,
    val_ratio: float = 0.10,
    test_ratio: float = 0.10,
    random_state: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Performs joint stratified split on (severity x language) so all languages and severities
    are proportionally represented across train, val, and test splits.
    """
    # Create composite stratum key
    df = df.copy()
    df["stratum"] = df["severity"] + "_" + df["language"]

    # Filter out single-instance strata or merge them to ensure stratification works
    stratum_counts = df["stratum"].value_counts()
    rare_strata = stratum_counts[stratum_counts < 2].index
    if len(rare_strata) > 0:
        # Fallback stratum to severity only for rare items
        df.loc[df["stratum"].isin(rare_strata), "stratum"] = df["severity"]

    # First split: train vs (val + test)
    val_test_ratio = val_ratio + test_ratio
    train_df, val_test_df = train_test_split(
        df,
        test_size=val_test_ratio,
        stratify=df["stratum"],
        random_state=random_state,
    )

    # Second split: val vs test (50/50 split of the remaining ratio)
    rel_test_ratio = test_ratio / val_test_ratio
    # Check if stratum has at least 2 instances in val_test_df
    vt_counts = val_test_df["stratum"].value_counts()
    vt_rare = vt_counts[vt_counts < 2].index
    if len(vt_rare) > 0:
        val_test_df.loc[val_test_df["stratum"].isin(vt_rare), "stratum"] = val_test_df["severity"]

    val_df, test_df = train_test_split(
        val_test_df,
        test_size=rel_test_ratio,
        stratify=val_test_df["stratum"],
        random_state=random_state,
    )

    # Clean temporary stratum column
    train_df = train_df.drop(columns=["stratum"]).reset_index(drop=True)
    val_df = val_df.drop(columns=["stratum"]).reset_index(drop=True)
    test_df = test_df.drop(columns=["stratum"]).reset_index(drop=True)

    return train_df, val_df, test_df


def generate_dataset_card(
    full_df: pd.DataFrame,
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    class_weights: dict[str, Any],
    output_path: str = "ml/datasets/DATASET_CARD.md",
) -> None:
    """
    Generates a comprehensive DATASET_CARD.md documenting split sizes, distributions,
    class weights, language mix, and ethical considerations.
    """
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    card_content = f"""# Project Pukar — Crisis SOS Dataset Card

**Domain:** Offline Emergency Mesh SOS Message Classification  
**Target Languages:** English (`en`), Hindi (`hi` - Devanagari), Hinglish (`hinglish` - Romanized Hindi)  
**Schema:** `{{text: str, severity: str, category: str, language: str, source: str}}`

---

## 1. Dataset Summary & Split Sizes

The final dataset is consolidated from public disaster corpora (HumAID, CrisisNLP, Kaggle Disaster Tweets) and Groq Llama-3 teacher-generated synthetic SOS distress messages. It is partitioned via joint stratification on `(severity x language)`.

| Split | Number of Records | Percentage of Total | Parquet Artifact |
| :--- | :--- | :--- | :--- |
| **Train** | `{len(train_df):,}` | `{(len(train_df)/len(full_df)*100.0):.1f}%` | [`train.parquet`](processed/train.parquet) |
| **Validation** | `{len(val_df):,}` | `{(len(val_df)/len(full_df)*100.0):.1f}%` | [`val.parquet`](processed/val.parquet) |
| **Test** | `{len(test_df):,}` | `{(len(test_df)/len(full_df)*100.0):.1f}%` | [`test.parquet`](processed/test.parquet) |
| **Total** | **`{len(full_df):,}`** | **100.0%** | Consolidated Master Corpus |

---

## 2. Language Distribution Across Splits

| Language | Total Count (%) | Train Count (%) | Val Count (%) | Test Count (%) |
| :--- | :--- | :--- | :--- | :--- |
| **English (`en`)** | `{len(full_df[full_df['language']=='en']):,}` ({(len(full_df[full_df['language']=='en'])/len(full_df)*100.0):.1f}%) | `{len(train_df[train_df['language']=='en']):,}` ({(len(train_df[train_df['language']=='en'])/len(train_df)*100.0):.1f}%) | `{len(val_df[val_df['language']=='en']):,}` ({(len(val_df[val_df['language']=='en'])/len(val_df)*100.0):.1f}%) | `{len(test_df[test_df['language']=='en']):,}` ({(len(test_df[test_df['language']=='en'])/len(test_df)*100.0):.1f}%) |
| **Hindi (`hi`)** | `{len(full_df[full_df['language']=='hi']):,}` ({(len(full_df[full_df['language']=='hi'])/len(full_df)*100.0):.1f}%) | `{len(train_df[train_df['language']=='hi']):,}` ({(len(train_df[train_df['language']=='hi'])/len(train_df)*100.0):.1f}%) | `{len(val_df[val_df['language']=='hi']):,}` ({(len(val_df[val_df['language']=='hi'])/len(val_df)*100.0):.1f}%) | `{len(test_df[test_df['language']=='hi']):,}` ({(len(test_df[test_df['language']=='hi'])/len(test_df)*100.0):.1f}%) |
| **Hinglish (`hinglish`)** | `{len(full_df[full_df['language']=='hinglish']):,}` ({(len(full_df[full_df['language']=='hinglish'])/len(full_df)*100.0):.1f}%) | `{len(train_df[train_df['language']=='hinglish']):,}` ({(len(train_df[train_df['language']=='hinglish'])/len(train_df)*100.0):.1f}%) | `{len(val_df[val_df['language']=='hinglish']):,}` ({(len(val_df[val_df['language']=='hinglish'])/len(val_df)*100.0):.1f}%) | `{len(test_df[test_df['language']=='hinglish']):,}` ({(len(test_df[test_df['language']=='hinglish'])/len(test_df)*100.0):.1f}%) |

---

## 3. Class Balance & Computed Loss Weights

### Severity Tiers
| Severity | Total Count | Train Split Count | Computed Loss Weight |
| :--- | :--- | :--- | :--- |
| **`critical`** | `{len(full_df[full_df['severity']=='critical']):,}` | `{len(train_df[train_df['severity']=='critical']):,}` | `{class_weights['severity_weights'].get('critical', 1.0)}` |
| **`warn`** | `{len(full_df[full_df['severity']=='warn']):,}` | `{len(train_df[train_df['severity']=='warn']):,}` | `{class_weights['severity_weights'].get('warn', 1.0)}` |
| **`info`** | `{len(full_df[full_df['severity']=='info']):,}` | `{len(train_df[train_df['severity']=='info']):,}` | `{class_weights['severity_weights'].get('info', 1.0)}` |

### Emergency Categories
| Category | Total Count | Train Split Count | Computed Loss Weight |
| :--- | :--- | :--- | :--- |
| **`rescue`** | `{len(full_df[full_df['category']=='rescue']):,}` | `{len(train_df[train_df['category']=='rescue']):,}` | `{class_weights['category_weights'].get('rescue', 1.0)}` |
| **`medical`** | `{len(full_df[full_df['category']=='medical']):,}` | `{len(train_df[train_df['category']=='medical']):,}` | `{class_weights['category_weights'].get('medical', 1.0)}` |
| **`fire`** | `{len(full_df[full_df['category']=='fire']):,}` | `{len(train_df[train_df['category']=='fire']):,}` | `{class_weights['category_weights'].get('fire', 1.0)}` |
| **`shelter`** | `{len(full_df[full_df['category']=='shelter']):,}` | `{len(train_df[train_df['category']=='shelter']):,}` | `{class_weights['category_weights'].get('shelter', 1.0)}` |
| **`other`** | `{len(full_df[full_df['category']=='other']):,}` | `{len(train_df[train_df['category']=='other']):,}` | `{class_weights['category_weights'].get('other', 1.0)}` |

---

## 4. Provenance & Corpus Sources

```
{full_df['source'].value_counts().to_string()}
```

---

## 5. Quality Controls & Known Limitations

1. **PII Sanitization:** All phone numbers, email addresses, URL links, and 12-digit ID formats have been stripped.
2. **Deterministic Deduplication:** Near-identical texts with equivalent punctuation/whitespace are collapsed.
3. **Synthetic Augmentation:** Low-resource Hinglish and Hindi critical classes were augmented via Groq Llama-3.1-8B teacher prompting.
4. **Boundary Calibration:** 25% of synthetic samples represent ambiguous boundary thresholds (warn-vs-critical) to enhance model calibration on the edge.
"""

    with open(out_file, "w", encoding="utf-8") as f:
        f.write(card_content)

    logger.info(f"Generated DATASET_CARD.md at {out_file}")


def build_final_dataset(
    processed_dir: str = "ml/datasets/processed",
    output_dir: str = "ml/datasets/processed",
    config_weights_path: str = "ml/configs/class_weights.yaml",
    dataset_card_path: str = "ml/datasets/DATASET_CARD.md",
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    proc_path = Path(processed_dir)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # 1. Collect all available processed corpora
    candidate_files = [
        proc_path / "corpus_public.parquet",
        proc_path / "corpus_synth.parquet",
        proc_path / "corpus_autolabeled.parquet",
    ]

    dfs = []
    for f in candidate_files:
        if f.exists():
            try:
                df = pd.read_parquet(f)
                logger.info(f"Loaded {len(df):,} records from {f.name}")
                dfs.append(df[["text", "severity", "category", "language", "source"]])
            except Exception as e:
                logger.warning(f"Failed to read {f.name}: {e}")

    if not dfs:
        raise FileNotFoundError(f"No processed parquet files found in {proc_path}. Run 'make normalize-data' or 'make gen-data' first.")

    combined = pd.concat(dfs, ignore_index=True)
    initial_len = len(combined)

    # 2. Sanitize and clean
    combined["text"] = combined["text"].apply(sanitize_text)
    combined = combined[combined["text"].str.len() > 5].copy()

    # 3. Deduplicate by normalized text hash
    combined["hash"] = combined["text"].apply(compute_text_hash)
    combined = combined.drop_duplicates(subset=["hash"]).drop(columns=["hash"]).reset_index(drop=True)
    logger.info(f"Sanitization & Deduplication: {initial_len:,} -> {len(combined):,} records (removed {initial_len - len(combined):,} dirty/duplicate rows).")

    # 4. Joint Stratified Split (80 / 10 / 10)
    train_df, val_df, test_df = stratified_split(combined, train_ratio=0.80, val_ratio=0.10, test_ratio=0.10)

    # 5. Compute and save class weights on training split
    weights_data = compute_and_save_class_weights(train_df, output_path=config_weights_path)

    # 6. Save splits
    train_df.to_parquet(out_path / "train.parquet", index=False, engine="pyarrow")
    val_df.to_parquet(out_path / "val.parquet", index=False, engine="pyarrow")
    test_df.to_parquet(out_path / "test.parquet", index=False, engine="pyarrow")
    logger.info(f"Saved splits: Train={len(train_df):,}, Val={len(val_df):,}, Test={len(test_df):,} to {out_path}")

    # 7. Generate Dataset Card
    generate_dataset_card(
        full_df=combined,
        train_df=train_df,
        val_df=val_df,
        test_df=test_df,
        class_weights=weights_data,
        output_path=dataset_card_path,
    )

    # 8. Print distribution summary
    print("\n" + "=" * 70)
    print(" PROJECT PUKAR — FINAL DATASET BUILD & STRATIFICATION REPORT")
    print("=" * 70)
    print(f"Total Consolidated Records : {len(combined):,}")
    print(f"Train Split Records (80%)  : {len(train_df):,}")
    print(f"Val Split Records (10%)    : {len(val_df):,}")
    print(f"Test Split Records (10%)   : {len(test_df):,}")
    print("=" * 70)

    print("\n--- Train Split: Joint Stratification (Severity x Language) ---")
    print(pd.pivot_table(train_df, index="severity", columns="language", values="text", aggfunc="count", fill_value=0).to_string())

    print("\n--- Val Split: Joint Stratification (Severity x Language) ---")
    print(pd.pivot_table(val_df, index="severity", columns="language", values="text", aggfunc="count", fill_value=0).to_string())

    print("\n--- Test Split: Joint Stratification (Severity x Language) ---")
    print(pd.pivot_table(test_df, index="severity", columns="language", values="text", aggfunc="count", fill_value=0).to_string())

    print("\n--- Computed Training Class Weights ---")
    print("Severity Weights :", weights_data["severity_weights"])
    print("Category Weights :", weights_data["category_weights"])
    print("=" * 70 + "\n")

    return train_df, val_df, test_df


if __name__ == "__main__":
    build_final_dataset()
