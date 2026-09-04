"""
Project Pukar - Public Crisis Dataset Normalizer
Concatenates and normalizes all available public corpora (HumAID, CrisisNLP, Kaggle)
into a single unified parquet file: ml/datasets/processed/corpus_public.parquet.
Enforces the frozen schema: {text: str, severity: str, category: str, language: str, source: str}
"""

import logging
from pathlib import Path

import pandas as pd

from ml.data_gen.generate_data import SEED_DATASET
from ml.datasets.loaders import CrisisNLPLoader, HumAIDLoader, KaggleDisasterTweetsLoader
from ml.datasets.loaders.base_loader import BaseCrisisLoader

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("Normalize")


class _SchemaValidator(BaseCrisisLoader):
    def load(self) -> pd.DataFrame:
        return pd.DataFrame()


def normalize_all_datasets(
    output_path: str = "ml/datasets/processed/corpus_public.parquet",
    config_path: str = "ml/configs/label_mapping.yaml",
) -> pd.DataFrame:
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    loaders = [
        ("HumAID", HumAIDLoader(config_path=config_path)),
        ("CrisisNLP", CrisisNLPLoader(config_path=config_path)),
        ("KaggleDisasterTweets", KaggleDisasterTweetsLoader(config_path=config_path)),
    ]

    dfs = []
    for name, loader in loaders:
        logger.info(f"Running loader for {name}...")
        df = loader.load()
        if not df.empty:
            logger.info(f"Loaded {len(df):,} records from {name}.")
            dfs.append(df)
        else:
            logger.info(f"No records loaded from {name} (directory empty or unpopulated).")

    # If no raw public datasets were found, include seed dataset to bootstrap schema
    if not dfs:
        logger.warning("No raw external datasets found in ml/datasets/raw/. Bootstrapping with seed crisis samples.")
        seed_records = []
        for s in SEED_DATASET:
            seed_records.append({
                "text": s["text"],
                "severity": s["severity"],
                "category": s["category"],
                "language": s.get("lang", "en"),
                "source": "pukar_seed_bootstrap",
            })
        combined_df = pd.DataFrame(seed_records)
    else:
        combined_df = pd.concat(dfs, ignore_index=True)

    # Validate against frozen schema and valid enums
    validator = _SchemaValidator(config_path=config_path)
    combined_df = validator.validate_schema(combined_df)

    # Deduplicate by text
    initial_len = len(combined_df)
    combined_df = combined_df.drop_duplicates(subset=["text"]).reset_index(drop=True)
    if initial_len != len(combined_df):
        logger.info(f"Deduplicated dataset: {initial_len:,} -> {len(combined_df):,} records.")

    # Save to Parquet
    combined_df.to_parquet(out_file, index=False, engine="pyarrow")
    logger.info(f"Saved normalized corpus to {out_file} ({len(combined_df):,} total rows).")

    # Print distribution summaries
    print("\n" + "=" * 65)
    print(" PROJECT PUKAR — NORMALIZED CORPUS DISTRIBUTION")
    print("=" * 65)
    print(f"Total Records: {len(combined_df):,}")
    print(f"Output File:   {out_file}\n")

    print("--- Severity Distribution ---")
    sev_counts = combined_df["severity"].value_counts()
    for sev, count in sev_counts.items():
        pct = (count / len(combined_df)) * 100.0
        print(f"  {sev.upper():<10} : {count:>6,} ({pct:>5.1f}%)")

    print("\n--- Category Distribution ---")
    cat_counts = combined_df["category"].value_counts()
    for cat, count in cat_counts.items():
        pct = (count / len(combined_df)) * 100.0
        print(f"  {cat.capitalize():<10} : {count:>6,} ({pct:>5.1f}%)")

    print("\n--- Language Distribution ---")
    lang_counts = combined_df["language"].value_counts()
    for lang, count in lang_counts.items():
        pct = (count / len(combined_df)) * 100.0
        print(f"  {lang.upper():<10} : {count:>6,} ({pct:>5.1f}%)")

    print("\n--- Source Distribution ---")
    src_counts = combined_df["source"].value_counts()
    for src, count in src_counts.items():
        pct = (count / len(combined_df)) * 100.0
        print(f"  {src:<22} : {count:>6,} ({pct:>5.1f}%)")
    print("=" * 65 + "\n")

    return combined_df


if __name__ == "__main__":
    normalize_all_datasets()
