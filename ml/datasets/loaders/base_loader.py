"""
Project Pukar - Base Dataset Loader
Defines the standard record schema {text, severity, category, language, source}
and shared utilities for loading and parsing raw crisis corpora.
"""

import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from services.backend.src.ml.contracts import Category, Language, Severity


def detect_language(text: str) -> str:
    """
    Lightweight heuristic language identifier for English, Hindi (Devanagari), and Hinglish.
    """
    if not text:
        return Language.EN.value

    # Check for Devanagari script characters (\u0900 - \u097F)
    devanagari_chars = len(re.findall(r"[\u0900-\u097F]", text))
    if devanagari_chars > 2:
        return Language.HI.value

    # Check for characteristic Hinglish / Romanized Hindi keywords
    hinglish_markers = r"(?i)\b(hai|hain|ho|gaya|gayi|pani|paani|chhat|fase|phase|fasa|bachao|madad|bhejo|khana|peene|dawai|khatam|hum|tum|log|deewar|bohot|zyada)\b"
    if len(re.findall(hinglish_markers, text)) >= 2:
        return Language.HINGLISH.value

    return Language.EN.value


class BaseCrisisLoader(ABC):
    def __init__(self, config_path: str = "ml/configs/label_mapping.yaml"):
        self.config_path = Path(config_path)
        self.config: dict[str, Any] = self._load_config()

    def _load_config(self) -> dict[str, Any]:
        if not self.config_path.exists():
            return {}
        with open(self.config_path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    @abstractmethod
    def load(self) -> pd.DataFrame:
        """
        Loads raw files and returns a DataFrame strictly adhering to the schema:
        ['text', 'severity', 'category', 'language', 'source']
        """
        pass

    def validate_schema(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Enforces schema column names, non-empty text, and valid enum values.
        """
        required_cols = ["text", "severity", "category", "language", "source"]
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Loader output missing required column: {col}")

        # Drop empty texts
        df = df.dropna(subset=["text"]).copy()
        df["text"] = df["text"].astype(str).str.strip()
        df = df[df["text"].str.len() > 3].copy()

        # Validate severity
        valid_severities = {s.value for s in Severity}
        df["severity"] = df["severity"].apply(
            lambda s: s if s in valid_severities else Severity.INFO.value
        )

        # Validate category
        valid_categories = {c.value for c in Category}
        df["category"] = df["category"].apply(
            lambda c: c if c in valid_categories else Category.OTHER.value
        )

        # Validate language
        valid_languages = {lang.value for lang in Language}
        df["language"] = df["language"].apply(
            lambda lang_val: lang_val if lang_val in valid_languages else Language.EN.value
        )

        return df[required_cols].reset_index(drop=True)
