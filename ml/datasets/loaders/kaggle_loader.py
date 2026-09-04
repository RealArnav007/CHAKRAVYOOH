"""
Project Pukar - Kaggle Disaster Tweets Dataset Loader
Normalizes Kaggle NLP Disaster Tweets corpus into Pukar's schema.
"""

import logging
import re
from pathlib import Path

import pandas as pd

from .base_loader import BaseCrisisLoader, detect_language

logger = logging.getLogger(__name__)


class KaggleDisasterTweetsLoader(BaseCrisisLoader):
    def __init__(
        self,
        raw_dir: str = "ml/datasets/raw/kaggle",
        config_path: str = "ml/configs/label_mapping.yaml",
    ):
        super().__init__(config_path)
        self.raw_dir = Path(raw_dir)
        self.source_name = "kaggle_disaster_tweets"

    def load(self) -> pd.DataFrame:
        empty_df = pd.DataFrame(columns=["text", "severity", "category", "language", "source"])
        if not self.raw_dir.exists():
            logger.warning(f"[KaggleLoader] Raw directory '{self.raw_dir}' not found. Skipping Kaggle.")
            return empty_df

        raw_files: list[Path] = list(self.raw_dir.glob("*.csv"))
        if not raw_files:
            logger.warning(f"[KaggleLoader] No .csv files in '{self.raw_dir}'. Skipping Kaggle.")
            return empty_df

        mapping_cfg = self.config.get("kaggle", {})
        keyword_mappings = mapping_cfg.get("keyword_mappings", {})

        records = []
        for file_path in raw_files:
            try:
                df = pd.read_csv(file_path, on_bad_lines="skip", low_memory=False)
                if "text" not in df.columns or "target" not in df.columns:
                    logger.warning(f"[KaggleLoader] Columns 'text' and 'target' not found in {file_path.name}")
                    continue

                for _, row in df.iterrows():
                    raw_text = str(row["text"]).strip()
                    if not raw_text or len(raw_text) < 4:
                        continue

                    target = int(row["target"]) if pd.notna(row["target"]) else 0
                    raw_kw = str(row["keyword"]).lower().strip() if "keyword" in df.columns and pd.notna(row["keyword"]) else ""

                    if target == 0:
                        sev = "info"
                        cat = "other"
                    else:
                        # Default disaster category/severity
                        sev = "warn"
                        cat = "other"

                        combined_search = f"{raw_kw} {raw_text.lower()}"
                        # Match against keyword mapping categories
                        for cat_name, conf in keyword_mappings.items():
                            kw_list = conf.get("keywords", [])
                            pattern = r"\b(" + "|".join(re.escape(k) for k in kw_list) + r")\b"
                            if re.search(pattern, combined_search, re.IGNORECASE):
                                sev = conf.get("severity", "critical")
                                cat = conf.get("category", cat_name)
                                break

                    lang = detect_language(raw_text)
                    records.append({
                        "text": raw_text,
                        "severity": sev,
                        "category": cat,
                        "language": lang,
                        "source": self.source_name,
                    })

            except Exception as e:
                logger.warning(f"[KaggleLoader] Error processing {file_path.name}: {e}")

        if not records:
            return empty_df

        result_df = pd.DataFrame(records)
        return self.validate_schema(result_df)
