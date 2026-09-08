"""
Project Pukar - Content-Based False Alarm & Mock Drill Scorer
============================================================
Detects test/drill language, explicit ignore disclaimers, empty/garbage payloads,
and trigger-type mismatches.

POLICY: NEVER AUTO-SUPPRESS.
Real emergencies can look unusual or contain odd phrasing. This module emits
an auditable likelihood score (0.0 to 1.0) and descriptive reasons to inform
the command center dispatcher without dropping or altering SOS packet delivery.
"""

from __future__ import annotations

import logging
from pathlib import Path
import re
from typing import Any
import yaml

from .contracts import Entities, FalseAlarmResult

logger = logging.getLogger("pukar.ml.false_alarm")

DEFAULT_CONFIG: dict[str, Any] = {
    "thresholds": {
        "drill_threshold": 0.65,
        "groq_ambiguity_band": {"min": 0.30, "max": 0.70},
    },
    "rule_weights": {
        "explicit_test_phrase": 0.90,
        "mock_drill_phrase": 0.85,
        "ignore_disclaimer": 0.80,
        "gibberish_or_empty": 0.75,
        "trigger_type_test": 0.70,
        "casual_check_phrase": 0.60,
        "contradictory_disclaimer": 0.50,
    },
    "patterns": {
        "test_phrases": [
            r"\b(this\s+is\s+a\s+)?test\b",
            r"\btesting(\s+1\s*2\s*3)?\b",
            r"\btest\s*(message|msg|call|sos|alert|broadcast|packet)\b",
            r"\bjust\s+testing\b",
            r"\bcheck(ing)?\s+(the\s+)?(app|system|network|radio|mesh|connection|beacon)\b",
            r"\bmic\s+check\b",
            r"\btrial\s+run\b",
            r"\bsample\s+alert\b",
            r"\b(sirf|bas)\s+(test|testing|jaanch)\s+(hai|kar\s+rahe\s+hain|h)\b",
            r"\bparikshan\b",
            r"\bjaanch\s+sandesh\b",
            r"\byeh\s+ek\s+parikshan\s+hai\b",
            r"\btest\s+ho\s+raha\s+hai\b",
        ],
        "drill_phrases": [
            r"\bmock\s*drill\b",
            r"\bdisaster\s+drill\b",
            r"\b(evacuation|fire|safety|emergency)\s+drill\b",
            r"\bexercise\s+only\b",
            r"\bsimulation\s+(exercise|only|test)\b",
            r"\bdry\s+run\b",
            r"\babhyaas\b",
            r"\bmock\s+parikshan\b",
            r"\btraining\s+exercise\b",
        ],
        "ignore_phrases": [
            r"\b(please\s+)?ignore(\s+this)?(\s+message|\s+alert|\s+sos)?\b",
            r"\bdo\s+not\s+(respond|dispatch|send|panic)\b",
            r"\bfalse\s+alarm\b",
            r"\baccidental\s+(press|trigger|alert|tap|click)\b",
            r"\bgalti\s+se\s+(dab\s+gaya|bhej\s+diya|trigger\s+ho\s+gaya)\b",
            r"\bkripya\s+dhyan\s+na\s+de(n)?\b",
            r"\bignore\s+karo\b",
            r"\bkoi\s+madad\s+ki\s+jarurat\s+nahi\s+hai\b",
            r"\bno\s+emergency\b",
            r"\bno\s+help\s+needed\b",
            r"\bjust\s+kidding\b",
            r"\bmazaak\b",
        ],
        "garbage_patterns": [
            r"^(.)\1{4,}$",
            r"^(asdf|qwer|zxcv|1234|test)+$",
            r"^[0-9\W_]+$",
        ],
    },
    "test_trigger_types": [
        "test",
        "manual_test",
        "mock_drill",
        "periodic_ping",
        "sensor_health_check",
        "diagnostic",
    ],
}

_CONFIG_CACHE: dict[str, Any] | None = None


def load_false_alarm_config(config_path: str | Path | None = None) -> dict[str, Any]:
    """Loads false alarm detection config from YAML with cached fallback."""
    global _CONFIG_CACHE
    if config_path is None and _CONFIG_CACHE is not None:
        return _CONFIG_CACHE

    search_paths = []
    if config_path:
        search_paths.append(Path(config_path))
    else:
        search_paths.extend([
            Path(__file__).parent / "configs" / "false_alarm.yaml",
            Path(__file__).parents[4] / "ml" / "configs" / "false_alarm.yaml",
            Path("services/backend/src/ml/configs/false_alarm.yaml"),
            Path("ml/configs/false_alarm.yaml"),
        ])

    for p in search_paths:
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    cfg = yaml.safe_load(f)
                    if isinstance(cfg, dict):
                        if config_path is None:
                            _CONFIG_CACHE = cfg
                        return cfg
            except Exception as e:
                logger.warning("Failed to load false_alarm config from %s: %s", p, e)

    return DEFAULT_CONFIG


def false_alarm(
    canonical_en: str | None,
    entities: Entities | dict[str, Any] | None = None,
    trigger_type: str | None = None,
    groq_eval: dict[str, Any] | None = None,
    groq_client: Any | None = None,
    config_path: str | Path | None = None,
) -> FalseAlarmResult:
    """
    Evaluates distress text for false alarm, mock drill, or test alert characteristics.

    Parameters:
        canonical_en: Canonical English or original distress message text.
        entities: Extracted Entities object or dict of extracted fields.
        trigger_type: Optional packet trigger context (e.g. 'manual_sos', 'sensor_fall', 'manual_test').
        groq_eval: Optional pre-computed Groq cloud triage evaluation dictionary.
        groq_client: Optional GroqClient instance for ambiguous cases.
        config_path: Optional custom config path.

    Returns:
        FalseAlarmResult containing false_alarm_likelihood (0.0-1.0), reasons, and is_likely_drill flag.
    """
    cfg = load_false_alarm_config(config_path)
    thresholds = cfg.get("thresholds", DEFAULT_CONFIG["thresholds"])
    weights = cfg.get("rule_weights", DEFAULT_CONFIG["rule_weights"])
    patterns = cfg.get("patterns", DEFAULT_CONFIG["patterns"])
    test_triggers = [t.lower() for t in cfg.get("test_trigger_types", DEFAULT_CONFIG["test_trigger_types"])]

    drill_threshold = float(thresholds.get("drill_threshold", 0.65))

    text = str(canonical_en or "").strip().lower()
    reasons: list[str] = []
    matched_weights: list[float] = []

    # 1. Empty / Whitespace check
    if not text or len(text) <= 2:
        reasons.append("Empty or trivial message body with no emergency context")
        matched_weights.append(float(weights.get("gibberish_or_empty", 0.75)))
        return FalseAlarmResult(
            false_alarm_likelihood=round(float(weights.get("gibberish_or_empty", 0.75)), 3),
            reasons=reasons,
            is_likely_drill=True,
        )

    # 2. Garbage / Repetitive Character smash
    garbage_patterns = patterns.get("garbage_patterns", [])
    for pat in garbage_patterns:
        try:
            if re.search(pat, text, re.IGNORECASE):
                reasons.append(f"Repetitive or nonsensical text pattern detected ('{text[:20]}')")
                matched_weights.append(float(weights.get("gibberish_or_empty", 0.75)))
                break
        except re.error:
            continue

    # 3. Test Phrases (Multilingual)
    test_patterns = patterns.get("test_phrases", [])
    matched_test = False
    for pat in test_patterns:
        try:
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                matched_test = True
                matched_phrase = match.group(0)
                reasons.append(f"Explicit test/diagnostic keyword detected: '{matched_phrase}'")
                matched_weights.append(float(weights.get("explicit_test_phrase", 0.90)))
                break
        except re.error:
            continue

    # 4. Mock Drill / Disaster Exercise Phrases
    drill_patterns = patterns.get("drill_phrases", [])
    matched_drill = False
    for pat in drill_patterns:
        try:
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                matched_drill = True
                matched_phrase = match.group(0)
                reasons.append(f"Mock drill or simulation exercise phrase detected: '{matched_phrase}'")
                matched_weights.append(float(weights.get("mock_drill_phrase", 0.85)))
                break
        except re.error:
            continue

    # 5. Ignore / False Alarm Disclaimers
    ignore_patterns = patterns.get("ignore_phrases", [])
    matched_ignore = False
    for pat in ignore_patterns:
        try:
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                matched_ignore = True
                matched_phrase = match.group(0)
                reasons.append(f"Explicit ignore/accidental trigger disclaimer: '{matched_phrase}'")
                matched_weights.append(float(weights.get("ignore_disclaimer", 0.80)))
                break
        except re.error:
            continue

    # 6. Trigger Type Mismatch
    if trigger_type and str(trigger_type).strip().lower() in test_triggers:
        reasons.append(f"Origin trigger type '{trigger_type}' explicitly declares test/diagnostic mode")
        matched_weights.append(float(weights.get("trigger_type_test", 0.70)))

    # 7. Check Entity Context & Contradictions
    # Check if real emergency entities were extracted
    has_real_distress_entities = False
    if entities:
        if isinstance(entities, dict):
            has_real_distress_entities = bool(
                entities.get("people_count")
                or entities.get("injuries")
                or entities.get("hazards")
                or (entities.get("needs") and len(entities.get("needs", [])) > 0)
                or entities.get("mobility") in ["trapped", "Trapped"]
            )
        elif hasattr(entities, "needs"):
            has_real_distress_entities = bool(
                entities.people_count
                or entities.injuries
                or entities.hazards
                or entities.needs
                or str(entities.mobility).lower() == "trapped"
            )

    if (matched_test or matched_drill or matched_ignore) and has_real_distress_entities:
        reasons.append("Disaster terminology present alongside explicit test/drill disclaimers")
        matched_weights.append(float(weights.get("contradictory_disclaimer", 0.50)))

    # 8. Compute Probabilistic Aggregate Likelihood (Noisy-OR over independent matches)
    if not matched_weights:
        # Check if pre-computed groq_eval signaled low urgency / drill
        if groq_eval:
            rationale = str(groq_eval.get("rationale", "")).lower()
            if any(k in rationale for k in ["drill", "test message", "testing", "simulation", "false alarm"]):
                reasons.append(f"Cloud Groq triage identified potential drill/test: '{groq_eval.get('rationale')}'")
                matched_weights.append(0.70)

    if not matched_weights:
        # Genuine clean SOS message with no false-alarm indicators
        return FalseAlarmResult(
            false_alarm_likelihood=0.0,
            reasons=[],
            is_likely_drill=False,
        )

    # Noisy-OR combination: 1 - prod(1 - w_i)
    prob_clean = 1.0
    for w in matched_weights:
        prob_clean *= (1.0 - min(0.99, max(0.0, w)))
    aggregate_likelihood = round(min(1.0, max(0.0, 1.0 - prob_clean)), 3)

    # If genuine distress entities are present without explicit drill keywords, damp likelihood
    if has_real_distress_entities and not (matched_test or matched_drill or matched_ignore):
        aggregate_likelihood = round(min(0.20, aggregate_likelihood * 0.3), 3)

    is_likely = aggregate_likelihood >= drill_threshold

    return FalseAlarmResult(
        false_alarm_likelihood=aggregate_likelihood,
        reasons=reasons,
        is_likely_drill=is_likely,
    )
