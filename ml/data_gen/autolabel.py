"""
Project Pukar - AI Teacher Autolabeling & Weak-Supervision Quality Oracle
Labels and verifies unlabeled/low-confidence crisis text using Groq Llama-3 as a teacher oracle.
Extracts soft probability distributions (for distillation) and routes teacher-regex disagreements
to ml/datasets/processed/review_queue.parquet for human audit.
"""

import hashlib
import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Any

import pandas as pd
from dotenv import load_dotenv

from ml.datasets.loaders.base_loader import detect_language
from services.backend.src.ml.contracts import Category, Language, Severity
from services.backend.src.ml.regex_engine import RegexEngine

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("AutoLabel")


def normalize_text_for_dedup(text: str) -> str:
    """
    Normalizes whitespace, lowercases, and strips non-alphanumeric punctuation
    to produce a canonical hash string for deduplication.
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


class AutoLabelOracle:
    def __init__(
        self,
        model: str | None = None,
        max_retries: int = 3,
        backoff_factor: float = 1.8,
        delay_sec: float = 0.5,
    ):
        self.model = model or os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.delay_sec = delay_sec

        self.api_key = os.getenv("GROQ_API_KEY")
        self.client = None
        if self.api_key:
            try:
                from groq import Groq
                self.client = Groq(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Groq SDK initialization deferred/failed: {e}")

        self.regex_engine = RegexEngine()
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0

    def query_teacher(self, text: str) -> dict[str, Any]:
        """
        Queries Groq Llama-3 teacher oracle for hard label, soft probabilities, and rationale.
        """
        if not self.client:
            return self._heuristic_teacher_fallback(text)

        system_prompt = (
            "You are the Master Triage Oracle for Project Pukar (Emergency Mesh SOS Platform). "
            "Analyze the given disaster text message (English, Hindi in Devanagari, or Hinglish). "
            "You must return ONLY a JSON object with this exact schema:\n"
            "{\n"
            '  "severity": "info" | "warn" | "critical",\n'
            '  "category": "rescue" | "medical" | "fire" | "shelter" | "other",\n'
            '  "language": "en" | "hi" | "hinglish",\n'
            '  "confidence": <float 0.0 to 1.0>,\n'
            '  "rationale": "<1-sentence clinical reasoning for this severity and category>",\n'
            '  "severity_probs": {"info": <float>, "warn": <float>, "critical": <float>},\n'
            '  "category_probs": {"rescue": <float>, "medical": <float>, "fire": <float>, "shelter": <float>, "other": <float>}\n'
            "}\n"
            "Ensure probabilities in severity_probs sum to 1.0, and category_probs sum to 1.0."
        )

        user_prompt = f"DISASTER TEXT MESSAGE:\n'''{text}'''"

        delay = self.delay_sec
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.1,
                    response_format={"type": "json_object"},
                    max_tokens=400,
                )

                if hasattr(response, "usage") and response.usage:
                    self.total_prompt_tokens += response.usage.prompt_tokens or 0
                    self.total_completion_tokens += response.usage.completion_tokens or 0

                content = response.choices[0].message.content
                data = json.loads(content)
                return self._validate_teacher_output(data, text)

            except Exception as e:
                logger.warning(f"Teacher query attempt {attempt}/{self.max_retries} failed: {e}")
                if attempt < self.max_retries:
                    time.sleep(delay)
                    delay *= self.backoff_factor

        return self._heuristic_teacher_fallback(text)

    def _validate_teacher_output(self, data: dict[str, Any], text: str) -> dict[str, Any]:
        # Validate severity
        sev_str = str(data.get("severity", "warn")).lower()
        if sev_str not in [s.value for s in Severity]:
            sev_str = Severity.WARN.value

        # Validate category
        cat_str = str(data.get("category", "other")).lower()
        if cat_str not in [c.value for c in Category]:
            cat_str = Category.OTHER.value

        # Validate language
        lang_str = str(data.get("language", "")).lower()
        if lang_str not in [lang_enum.value for lang_enum in Language]:
            lang_str = detect_language(text)

        conf = float(data.get("confidence", 0.8))
        conf = max(0.0, min(1.0, conf))

        # Validate & normalize severity_probs
        raw_sev_probs = data.get("severity_probs", {})
        sev_probs = {
            "info": float(raw_sev_probs.get("info", 0.1)),
            "warn": float(raw_sev_probs.get("warn", 0.2)),
            "critical": float(raw_sev_probs.get("critical", 0.7)),
        }
        sev_sum = sum(sev_probs.values()) or 1.0
        sev_probs = {k: round(v / sev_sum, 4) for k, v in sev_probs.items()}

        # Validate & normalize category_probs
        raw_cat_probs = data.get("category_probs", {})
        cat_probs = {
            "rescue": float(raw_cat_probs.get("rescue", 0.2)),
            "medical": float(raw_cat_probs.get("medical", 0.2)),
            "fire": float(raw_cat_probs.get("fire", 0.2)),
            "shelter": float(raw_cat_probs.get("shelter", 0.2)),
            "other": float(raw_cat_probs.get("other", 0.2)),
        }
        cat_sum = sum(cat_probs.values()) or 1.0
        cat_probs = {k: round(v / cat_sum, 4) for k, v in cat_probs.items()}

        return {
            "severity": sev_str,
            "category": cat_str,
            "language": lang_str,
            "confidence": conf,
            "rationale": str(data.get("rationale", "Teacher classification complete")),
            "severity_probs": sev_probs,
            "category_probs": cat_probs,
        }

    def _heuristic_teacher_fallback(self, text: str) -> dict[str, Any]:
        """
        Deterministic fallback when Groq is unavailable.
        Uses regex evaluation + heuristic soft probability calculation.
        """
        regex_res = self.regex_engine.evaluate(text)
        sev = regex_res["severity"].value
        cat = regex_res["category"].value
        lang = detect_language(text)
        score = regex_res["score"]

        # Soft probabilities for distillation
        if sev == "critical":
            sev_probs = {"info": 0.05, "warn": 0.15, "critical": 0.80}
        elif sev == "warn":
            sev_probs = {"info": 0.15, "warn": 0.70, "critical": 0.15}
        else:
            sev_probs = {"info": 0.80, "warn": 0.15, "critical": 0.05}

        cat_probs = {c.value: (0.70 if c.value == cat else 0.075) for c in Category}
        cat_sum = sum(cat_probs.values())
        cat_probs = {k: round(v / cat_sum, 4) for k, v in cat_probs.items()}

        return {
            "severity": sev,
            "category": cat,
            "language": lang,
            "confidence": 0.85 if regex_res["matched_rules"] else 0.55,
            "rationale": f"Rule-derived classification (Score: {score}, Rules: {regex_res['matched_rules']})",
            "severity_probs": sev_probs,
            "category_probs": cat_probs,
        }

    def check_weak_supervision_agreement(
        self,
        text: str,
        teacher_eval: dict[str, Any],
    ) -> tuple[bool, str | None, dict[str, Any]]:
        """
        Compares Groq teacher label vs Regex engine prediction.
        Returns: (agreed: bool, disagreement_reason: Optional[str], regex_eval: dict)
        """
        regex_eval = self.regex_engine.evaluate(text)
        t_sev = teacher_eval["severity"]
        r_sev = regex_eval["severity"].value

        t_cat = teacher_eval["category"]
        r_cat = regex_eval["category"].value

        # Condition 1: Severe polar disagreement on severity (critical vs info)
        if (t_sev == "critical" and r_sev == "info") or (t_sev == "info" and r_sev == "critical"):
            reason = f"POLAR_SEVERITY_DISAGREEMENT: Teacher={t_sev} vs Regex={r_sev} (Score={regex_eval['score']})"
            return False, reason, regex_eval

        # Condition 2: High-confidence teacher category disagrees with strong explicit regex match
        if regex_eval["matched_rules"] and (r_cat != "other") and (t_cat != r_cat) and (teacher_eval["confidence"] >= 0.80):
            reason = f"CATEGORY_CONFLICT: Teacher={t_cat} vs Regex={r_cat} (Rules={regex_eval['matched_rules']})"
            return False, reason, regex_eval

        # Condition 3: Very low teacher confidence (< 0.40)
        if teacher_eval["confidence"] < 0.40:
            reason = f"LOW_CONFIDENCE: Teacher confidence={teacher_eval['confidence']:.2f}"
            return False, reason, regex_eval

        return True, None, regex_eval


def auto_label_corpus(
    input_data: str | list[str] | pd.DataFrame,
    output_path: str = "ml/datasets/processed/corpus_autolabeled.parquet",
    review_queue_path: str = "ml/datasets/processed/review_queue.parquet",
    model: str | None = None,
    delay_sec: float = 0.2,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Main autolabeling entry point.
    Deduplicates texts, labels via Teacher Oracle, checks weak-supervision agreement,
    and splits output into confirmed labeled corpus and review_queue.
    """
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    review_file = Path(review_queue_path)
    review_file.parent.mkdir(parents=True, exist_ok=True)

    # 1. Extract raw texts
    raw_texts: list[str] = []
    if isinstance(input_data, str):
        path = Path(input_data)
        if path.suffix == ".parquet":
            df_in = pd.read_parquet(path)
            raw_texts = df_in["text"].dropna().tolist()
        elif path.suffix in [".csv", ".tsv"]:
            sep = "\t" if path.suffix == ".tsv" else ","
            df_in = pd.read_csv(path, sep=sep)
            text_col = "text" if "text" in df_in.columns else df_in.columns[0]
            raw_texts = df_in[text_col].dropna().tolist()
        elif path.suffix == ".jsonl":
            import json
            with open(path, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        raw_texts.append(json.loads(line).get("text", ""))
    elif isinstance(input_data, pd.DataFrame):
        raw_texts = input_data["text"].dropna().tolist()
    elif isinstance(input_data, list):
        raw_texts = list(input_data)

    logger.info(f"Loaded {len(raw_texts):,} input texts for autolabeling.")

    # 2. Near-identical text deduplication using normalized hash
    seen_hashes: set[str] = set()
    deduped_texts: list[str] = []
    for t in raw_texts:
        t_clean = str(t).strip()
        if len(t_clean) < 4:
            continue
        h = compute_text_hash(t_clean)
        if h not in seen_hashes:
            seen_hashes.add(h)
            deduped_texts.append(t_clean)

    logger.info(f"Deduplication: {len(raw_texts):,} -> {len(deduped_texts):,} unique texts (saved {len(raw_texts) - len(deduped_texts):,} calls).")

    # 3. Initialize Oracle and iterate
    oracle = AutoLabelOracle(model=model, delay_sec=delay_sec)
    labeled_rows: list[dict[str, Any]] = []
    review_rows: list[dict[str, Any]] = []

    for i, text in enumerate(deduped_texts, 1):
        if i % 25 == 0 or i == len(deduped_texts):
            logger.info(f"Autolabeling progress: {i}/{len(deduped_texts)} ({len(labeled_rows)} approved, {len(review_rows)} flagged)...")

        t_eval = oracle.query_teacher(text)
        agreed, disagreement_reason, r_eval = oracle.check_weak_supervision_agreement(text, t_eval)

        record = {
            "text": text,
            "severity": t_eval["severity"],
            "category": t_eval["category"],
            "language": t_eval["language"],
            "confidence": t_eval["confidence"],
            "rationale": t_eval["rationale"],
            "prob_info": t_eval["severity_probs"]["info"],
            "prob_warn": t_eval["severity_probs"]["warn"],
            "prob_critical": t_eval["severity_probs"]["critical"],
            "prob_rescue": t_eval["category_probs"]["rescue"],
            "prob_medical": t_eval["category_probs"]["medical"],
            "prob_fire": t_eval["category_probs"]["fire"],
            "prob_shelter": t_eval["category_probs"]["shelter"],
            "prob_other": t_eval["category_probs"]["other"],
            "source": "autolabel_teacher",
        }

        if agreed:
            labeled_rows.append(record)
        else:
            review_record = dict(record)
            review_record["flag_reason"] = disagreement_reason
            review_record["regex_severity"] = r_eval["severity"].value
            review_record["regex_category"] = r_eval["category"].value
            review_record["regex_score"] = r_eval["score"]
            review_record["matched_rules"] = json.dumps(r_eval["matched_rules"])
            review_rows.append(review_record)

        if oracle.client:
            time.sleep(delay_sec)

    # 4. Create DataFrames and save
    labeled_df = pd.DataFrame(labeled_rows) if labeled_rows else pd.DataFrame(columns=[
        "text", "severity", "category", "language", "confidence", "rationale",
        "prob_info", "prob_warn", "prob_critical", "prob_rescue", "prob_medical", "prob_fire", "prob_shelter", "prob_other", "source"
    ])
    review_df = pd.DataFrame(review_rows) if review_rows else pd.DataFrame(columns=[
        "text", "severity", "category", "language", "confidence", "rationale", "flag_reason", "regex_severity", "regex_category", "regex_score", "matched_rules"
    ])

    labeled_df.to_parquet(out_file, index=False, engine="pyarrow")
    review_df.to_parquet(review_file, index=False, engine="pyarrow")

    print("\n" + "=" * 70)
    print(" PROJECT PUKAR — AUTOLABELING & WEAK-SUPERVISION AUDIT REPORT")
    print("=" * 70)
    print(f"Total Unique Texts Evaluated : {len(deduped_texts):,}")
    print(f"Approved High-Confidence Rows: {len(labeled_df):,} -> {out_file}")
    print(f"Flagged for Human Review     : {len(review_df):,} -> {review_file}")
    print(f"Agreement Rate               : {(len(labeled_df)/len(deduped_texts)*100.0 if deduped_texts else 0.0):.1f}%")
    print("=" * 70)

    if not labeled_df.empty:
        print("\n--- Approved Label Distribution (Severity x Category) ---")
        print(pd.pivot_table(labeled_df, index="severity", columns="category", values="text", aggfunc="count", fill_value=0).to_string())

    if not review_df.empty:
        print("\n--- Flagged Disagreement Reasons in Review Queue ---")
        print(review_df["flag_reason"].value_counts().to_string())
    print("=" * 70 + "\n")

    return labeled_df, review_df


if __name__ == "__main__":
    sample_corpus = "ml/datasets/processed/corpus_synth.parquet"
    if Path(sample_corpus).exists():
        auto_label_corpus(sample_corpus)
    else:
        sample_texts = [
            "4 people trapped under concrete rubble in flash flood!",
            "मकान की छत गिर गई है 3 लोग मलबे में फंसे हैं तुरंत मदद भेजो",
            "Pani bohot badh gaya hai hum safe school me hain",
            "Is there any road open towards sector 4?",
        ]
        auto_label_corpus(sample_texts)
