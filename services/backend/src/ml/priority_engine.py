"""
Project Pukar - Priority Fusion Engine
Fuses multi-modal signals (on-device TFLite, regex baseline, Groq semantic teacher, and cluster density)
into a calibrated, fully auditable priority score (0-100) and AI transparency breakdown.
"""

import math
from pathlib import Path
from typing import Any

import yaml

from .contracts import (
    AIReasoningBreakdown,
    DecryptedSOSPayload,
    EmergencyCategory,
    SeverityLevel,
    SignedSOSHeader,
)


class PriorityEngine:
    def __init__(self, config_path: str | None = None):
        if config_path is None:
            default_local = Path(__file__).parent / "configs" / "priority_weights.yaml"
            default_ml = Path(__file__).resolve().parents[4] / "ml" / "configs" / "priority_weights.yaml"
            if default_local.exists():
                config_path = str(default_local)
            elif default_ml.exists():
                config_path = str(default_ml)
            else:
                config_path = str(default_local)

        self.config_path = Path(config_path)
        self.config: dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        if not self.config_path.exists():
            self.weights = {
                "w_severity": 0.25,
                "w_regex": 0.20,
                "w_local_model": 0.20,
                "w_groq": 0.35,
            }
            self.thresholds = {
                "critical": 75.0,
                "high": 55.0,
                "medium": 35.0,
                "low": 0.0,
            }
            self.modifiers = {
                "corroboration": {"bonus_per_report": 4.0, "max_corroboration_bonus": 15.0},
                "vulnerability_bonus": {"child_or_elderly": 8.0, "pregnant": 10.0, "medical_equipment": 10.0},
                "temporal_decay": {"half_life_hours": 6.0, "min_decay_factor": 0.5},
            }
        else:
            with open(self.config_path, encoding="utf-8") as f:
                self.config = yaml.safe_load(f) or {}
                self.weights = self.config.get("weights", {})
                self.thresholds = self.config.get("thresholds", {})
                self.modifiers = self.config.get("modifiers", {})

    def _severity_to_numeric(self, sev: SeverityLevel) -> float:
        mapping = {
            SeverityLevel.INFO: 20.0,
            SeverityLevel.WARN: 55.0,
            SeverityLevel.CRITICAL: 90.0,
        }
        return mapping.get(sev, 50.0)

    def calculate_priority(
        self,
        header: SignedSOSHeader,
        payload: DecryptedSOSPayload,
        regex_eval: dict[str, Any],
        groq_eval: dict[str, Any],
        corroborating_reports_count: int = 0,
        hours_elapsed: float = 0.0,
    ) -> dict[str, Any]:
        """
        Executes the multi-factor priority fusion formula and produces the auditable reasoning breakdown.
        """
        # 1. Component scores
        raw_severity_num = self._severity_to_numeric(header.severity)
        regex_score = float(regex_eval.get("score", header.regex_score))
        local_model_score = float(header.local_model_score)
        groq_score = float(groq_eval.get("urgency_score", 50.0))

        # Weights
        w_sev = self.weights.get("w_severity", 0.25)
        w_reg = self.weights.get("w_regex", 0.20)
        w_loc = self.weights.get("w_local_model", 0.20)
        w_grq = self.weights.get("w_groq", 0.35)

        # Base weighted fusion
        contrib_sev = raw_severity_num * w_sev
        contrib_reg = regex_score * w_reg
        contrib_loc = local_model_score * w_loc
        contrib_grq = groq_score * w_grq

        base_priority = contrib_sev + contrib_reg + contrib_loc + contrib_grq

        # 2. Corroboration bonus
        corr_config = self.modifiers.get("corroboration", {})
        bonus_per_report = corr_config.get("bonus_per_report", 4.0)
        max_corr_bonus = corr_config.get("max_corroboration_bonus", 15.0)
        corroboration_bonus = min(max_corr_bonus, corroborating_reports_count * bonus_per_report)

        # 3. Vulnerability & Special flags bonus
        vuln_config = self.modifiers.get("vulnerability_bonus", {})
        vulnerability_bonus = 0.0
        if groq_eval.get("vulnerable_victims", False) or payload.victim_count > 3:
            vulnerability_bonus += vuln_config.get("child_or_elderly", 8.0)
        if payload.is_trapped or groq_eval.get("is_trapped", False):
            vulnerability_bonus += 10.0
        if payload.has_medical_need or groq_eval.get("has_medical_need", False):
            vulnerability_bonus += 5.0

        # 4. Temporal decay factor
        decay_config = self.modifiers.get("temporal_decay", {})
        half_life = decay_config.get("half_life_hours", 6.0)
        min_factor = decay_config.get("min_decay_factor", 0.5)
        
        if hours_elapsed > 0:
            decay_factor = max(min_factor, math.pow(0.5, hours_elapsed / half_life))
        else:
            decay_factor = 1.0

        # Final computed raw priority
        fused_raw = (base_priority + corroboration_bonus + vulnerability_bonus) * decay_factor
        final_priority = max(0.0, min(100.0, round(fused_raw, 2)))

        # 5. Resolve final severity tier
        crit_thresh = self.thresholds.get("critical", 75.0)
        warn_thresh = self.thresholds.get("medium", 35.0)

        if final_priority >= crit_thresh:
            resolved_severity = SeverityLevel.CRITICAL
        elif final_priority >= warn_thresh:
            resolved_severity = SeverityLevel.WARN
        else:
            resolved_severity = SeverityLevel.INFO

        # 6. Resolve final category
        if groq_eval.get("category") and groq_eval.get("category") != EmergencyCategory.OTHER:
            resolved_category = groq_eval["category"]
        elif regex_eval.get("category") and regex_eval.get("category") != EmergencyCategory.OTHER:
            resolved_category = regex_eval["category"]
        else:
            resolved_category = header.category

        # 7. Auditable AI Reasoning Breakdown
        reasoning = AIReasoningBreakdown(
            regex_contribution=round(contrib_reg, 2),
            local_model_contribution=round(contrib_loc, 2),
            groq_contribution=round(contrib_grq, 2),
            corroboration_bonus=round(corroboration_bonus, 2),
            vulnerability_bonus=round(vulnerability_bonus, 2),
            time_decay_factor=round(decay_factor, 3),
            extracted_entities=groq_eval.get("entities", []),
            groq_rationale=groq_eval.get("rationale", ""),
            matched_rules=regex_eval.get("matched_rules", []),
        )

        return {
            "severity": resolved_severity,
            "priority_score": final_priority,
            "category": resolved_category,
            "confidence": round((header.confidence + groq_eval.get("confidence", 0.7)) / 2.0, 3),
            "reasoning": reasoning,
        }
