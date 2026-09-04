"""
Project Pukar - HumAID Dataset Loader
Normalizes Humanitarian AI Dataset (HumAID) into Pukar's {text, severity, category, language, source} schema.
"""

import logging
from pathlib import Path

import pandas as pd

from .base_loader import BaseCrisisLoader, detect_language

logger = logging.getLogger(__name__)


class HumAIDLoader(BaseCrisisLoader):
    def __init__(
        self,
        raw_dir: str = "ml/datasets/raw/humaid",
        config_path: str = "ml/configs/label_mapping.yaml",
    ):
        super().__init__(config_path)
        self.raw_dir = Path(raw_dir)
        self.source_name = "humaid"

    def load(self) -> pd.DataFrame:
        empty_df = pd.DataFrame(columns=["text", "severity", "category", "language", "source"])
        if not self.raw_dir.exists():
            logger.warning(f"[HumAIDLoader] Raw directory '{self.raw_dir}' not found. Skipping HumAID.")
            return empty_df

        raw_files: list[Path] = list(self.raw_dir.glob("*.tsv")) + list(self.raw_dir.glob("*.csv"))
        if not raw_files:
            logger.warning(f"[HumAIDLoader] No .tsv or .csv files found in '{self.raw_dir}'. Skipping HumAID.")
            return empty_df

        mapping_cfg = self.config.get("humaid", {})
        label_map = mapping_cfg.get("mappings", {})
        default_sev = mapping_cfg.get("default", {}).get("severity", "info")
        default_cat = mapping_cfg.get("default", {}).get("category", "other")

        records = []
        for file_path in raw_files:
            try:
                sep = "\t" if file_path.suffix == ".tsv" else ","
                df = pd.read_csv(file_path, sep=sep, on_bad_lines="skip", low_memory=False)
                
                # Identify text and label column names
                text_col = None
                for candidate in ["tweet_text", "text", "message"]:
                    if candidate in df.columns:
                        text_col = candidate
                        break

                label_col = None
                for candidate in ["class_label", "label", "category"]:
                    if candidate in df.columns:
                        label_col = candidate
                        break

                if not text_col:
                    logger.warning(f"[HumAIDLoader] Text column not recognized in {file_path.name}")
                    continue

                for _, row in df.iterrows():
                    raw_text = str(row[text_col]).strip()
                    if not raw_text or len(raw_text) < 4:
                        continue

                    raw_label = str(row[label_col]).strip() if label_col and pd.notna(row[label_col]) else ""
                    mapped = label_map.get(raw_label, {})
                    sev = mapped.get("severity", default_sev)
                    cat = mapped.get("category", default_cat)
                    lang = detect_language(raw_text)

                    records.append({
                        "text": raw_text,
                        "severity": sev,
                        "category": cat,
                        "language": lang,
                        "source": self.source_name,
                    })

            except Exception as e:
                logger.warning(f"[HumAIDLoader] Error processing file {file_path.name}: {e}")

        if not records:
            return empty_df

        result_df = pd.DataFrame(records)
        return self.validate_schema(result_df)
