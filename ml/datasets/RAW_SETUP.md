# Project Pukar — Raw Crisis Datasets Setup Guide

This document specifies the expected local file paths, download sources, and formats for raw public crisis-text corpora.

The dataset normalization pipeline (`ml/datasets/normalize.py`) looks for raw data in `ml/datasets/raw/`. Missing datasets are **gracefully skipped with a warning**, so you can download one, two, or all three corpora.

---

## Directory Structure

```
ml/datasets/raw/
├── humaid/
│   └── (TSV or CSV files, e.g. all_events.tsv, *_train.tsv)
├── crisisnlp/
│   └── (CSV or TSV files from CrisisLexT26, CrisisLexT6, or CrisisNLP)
└── kaggle/
    └── (train.csv from Disaster Tweets Kaggle competition)
```

---

## 1. HumAID (Humanitarian AI Dataset)
- **Source:** [QCRI / CrisisNLP HumAID Repository](https://crisisnlp.qcri.org/humaid_dataset)
- **Paper:** *HumAID: Multimodal Human-Annotated Disaster Dataset for NLP Benchmarking*
- **Expected Path:** `ml/datasets/raw/humaid/`
- **Expected Columns:** `tweet_text` (or `text`), `class_label` (or `label`)
- **Setup:**
  ```bash
  mkdir -p ml/datasets/raw/humaid
  # Extract or copy HumAID TSV/CSV splits into ml/datasets/raw/humaid/
  ```

---

## 2. CrisisNLP / CrisisLex
- **Source:** [CrisisLex / CrisisNLP](https://crisisnlp.qcri.org/crisislex)
- **Expected Path:** `ml/datasets/raw/crisisnlp/`
- **Expected Columns:** `tweet` (or `text`), `label` (or `category`, `choose_one_category`)
- **Setup:**
  ```bash
  mkdir -p ml/datasets/raw/crisisnlp
  # Extract CrisisLexT26 or CrisisNLP CSVs into ml/datasets/raw/crisisnlp/
  ```

---

## 3. Kaggle Disaster Tweets
- **Source:** [Kaggle: Natural Language Processing with Disaster Tweets](https://www.kaggle.com/c/nlp-getting-started)
- **Expected Path:** `ml/datasets/raw/kaggle/train.csv` (or `*.csv`)
- **Expected Columns:** `text`, `target` (0 or 1), optional `keyword`, `location`
- **Setup:**
  ```bash
  mkdir -p ml/datasets/raw/kaggle
  # Place Kaggle train.csv in ml/datasets/raw/kaggle/
  ```

---

## Running Normalization

Once any raw files are placed into `ml/datasets/raw/`, run:
```bash
python ml/datasets/normalize.py
```
This will parse all available files, map labels according to [`ml/configs/label_mapping.yaml`](../configs/label_mapping.yaml), and output a single unified parquet file at:
`ml/datasets/processed/corpus_public.parquet` with the frozen schema:
`{text: str, severity: str, category: str, language: str, source: str}`
