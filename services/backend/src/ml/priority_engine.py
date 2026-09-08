"""
Project Pukar - Master Priority Fusion Engine (Confidence-Aware)
================================================================

Fuses multi-modal signals into ONE operational dispatch priority score (0-100)
with dynamic confidence weighting, explicit life-safety disagreement resolution,
and human review abstention.

Architectural Contract & Separation of Concerns:
------------------------------------------------
1. Confidence-Aware Dynamic Modulation:
   - Multi-modal input signals: on-device neural model (with origin confidence),
     backend deterministic regex rules (with match pattern confidence), and cloud Groq LLM
     (with semantic calibration confidence).
   - Each source is weighted dynamically by its real-time confidence rather than a static constant.
2. Life-Safety Disagreement Resolution Policy:
   - In search-and-rescue life-safety operations, conflicting signals across edge neural,
     server regex, and cloud LLM are resolved by biasing toward the SAFER (higher) severity tier.
   - Explicitly logged in reasoning to ensure full algorithmic transparency and accountability.
3. Quality Assurance & Abstention (Human Review Trigger):
   - If aggregate confidence falls below `human_review_confidence_threshold` (or unresolved
     low-confidence conflicts occur), `needs_human_review` is set to `True`.
   - Rendered as a prominent triage badge on Arnav's incident command screen.
4. Sub-Linear Corroboration Guard:
   - Duplicate nearby SOS packets apply sub-linear saturation capped at `max_corroboration_bonus`.
5. Configuration-Driven:
   - All weights, confidence anchors, thresholds, and modifier gains are dynamically loaded
     from `priority.yaml` so changing the configuration visibly changes runtime behavior.
"""

from __future__ import annotations

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
    """
    Multi-signal confidence-aware priority fusion engine combining edge telemetry,
    deterministic regex, cloud LLM triage, and incident layer spatial/temporal modifiers.
    """

    def __init__(self, config_path: str | Path | None = None):
        if config_path is None:
            candidate_paths = [
                Path(__file__).parent / "configs" / "priority.yaml",
                Path(__file__).resolve().parents[4] / "ml" / "configs" / "priority.yaml",
                Path("ml/configs/priority.yaml"),
                Path(__file__).parent / "configs" / "priority_weights.yaml",
                Path(__file__).resolve().parents[4] / "ml" / "configs" / "priority_weights.yaml",
            ]
            for cp in candidate_paths:
                if cp.exists():
                    config_path = cp
                    break
            if config_path is None:
                config_path = candidate_paths[0]

        self.config_path = Path(config_path)
        self.config: dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """
        Dynamically loads fusion weights, severity anchors, and modifier parameters from YAML.
        """
        if not self.config_path.exists():
            self.weights = {
                "w_severity": 0.20,
                "w_regex": 0.30,
                "w_local_model": 0.25,
                "w_groq": 0.45,
            }
            self.thresholds = {
                "critical": 75.0,
                "warn": 35.0,
                "info": 0.0,
            }
            self.severity_numeric_anchors = {
                "info": 20.0,
                "warn": 55.0,
                "critical": 90.0,
            }
            self.confidence_fusion_cfg = {
                "enabled": True,
                "default_regex_confidence_match": 0.95,
                "default_regex_confidence_nomatch": 0.70,
                "min_source_confidence": 0.10,
            }
            self.disagreement_cfg = {
                "score_delta_threshold": 30.0,
                "safe_side_bias_enabled": True,
                "critical_elevation_anchor": 78.0,
                "flag_degraded_local": True,
            }
            self.abstention_cfg = {
                "human_review_confidence_threshold": 0.65,
                "flag_on_severe_disagreement": True,
            }
            self.modifiers = {
                "corroboration": {"bonus_per_report": 4.0, "max_corroboration_bonus": 15.0},
                "vulnerability_bonus": {
                    "child_or_elderly": 8.0,
                    "pregnant": 10.0,
                    "medical_equipment": 10.0,
                    "trapped_bonus": 10.0,
                    "medical_need_bonus": 5.0,
                    "victim_count_threshold": 3,
                },
                "temporal_decay": {"half_life_hours": 6.0, "min_decay_factor": 0.5},
                "spatial_location": {"weight": 1.0, "max_location_bonus": 10.0},
                "escalation_trend": {"weight": 1.0, "max_trend_bonus": 10.0},
            }
            self.groq_cfg = {
                "groq_enabled": True,
                "groq_timeout_ms": 2000,
            }
        else:
            with open(self.config_path, encoding="utf-8") as f:
                self.config = yaml.safe_load(f) or {}
                self.weights = self.config.get(
                    "weights",
                    {"w_severity": 0.20, "w_regex": 0.30, "w_local_model": 0.25, "w_groq": 0.45},
                )
                self.thresholds = self.config.get(
                    "thresholds",
                    {"critical": 75.0, "warn": 35.0, "info": 0.0},
                )
                self.severity_numeric_anchors = self.config.get(
                    "severity_numeric_anchors",
                    {"info": 20.0, "warn": 55.0, "critical": 90.0},
                )
                self.confidence_fusion_cfg = self.config.get(
                    "confidence_fusion",
                    {
                        "enabled": True,
                        "default_regex_confidence_match": 0.95,
                        "default_regex_confidence_nomatch": 0.70,
                        "min_source_confidence": 0.10,
                    },
                )
                self.disagreement_cfg = self.config.get(
                    "disagreement",
                    {
                        "score_delta_threshold": 30.0,
                        "safe_side_bias_enabled": True,
                        "critical_elevation_anchor": 78.0,
                        "flag_degraded_local": True,
                    },
                )
                self.abstention_cfg = self.config.get(
                    "abstention",
                    {
                        "human_review_confidence_threshold": 0.65,
                        "flag_on_severe_disagreement": True,
                    },
                )
                self.modifiers = self.config.get("modifiers", {})
                self.groq_cfg = self.config.get(
                    "groq",
                    {
                        "groq_enabled": self.config.get("groq_enabled", True),
                        "groq_timeout_ms": self.config.get("groq_timeout_ms", 2000),
                    },
                )

    def _severity_to_numeric(self, sev: SeverityLevel | str) -> float:
        sev_key = sev.value if hasattr(sev, "value") else str(sev).lower()
        anchors = getattr(self, "severity_numeric_anchors", {}) or {}
        return float(anchors.get(sev_key, 50.0))

    def calculate_priority(
        self,
        header: SignedSOSHeader,
        payload: DecryptedSOSPayload,
        regex_eval: dict[str, Any],
        groq_eval: dict[str, Any] | None = None,
        corroborating_reports_count: int = 0,
        hours_elapsed: float = 0.0,
        location_risk_modifier: float = 0.0,
        escalation_trend: float = 0.0,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Calculates normalized operational priority (0-100) using confidence-aware fusion,
        resolves signal disagreements via life-safety escalation policy, and sets
        `needs_human_review` when aggregate confidence is low.
        """
        groq_dict = groq_eval or {}

        # 1. Base Signal Scores
        raw_severity_num = self._severity_to_numeric(header.severity)
        server_regex_score = float(regex_eval.get("score", header.regex_score))
        local_model_score = float(header.local_model_score)
        groq_score = float(groq_dict.get("urgency_score", 50.0))

        # Check Groq availability
        groq_status = groq_dict.get("groq", groq_dict.get("groq_status"))
        is_groq_active = (
            bool(groq_dict)
            and groq_dict.get("available", True)
            and groq_status != "unavailable — rules-only"
            and not groq_dict.get("fallback", False)
            and "Groq API unavailable" not in groq_dict.get("rationale", "")
            and "Groq invocation failed" not in groq_dict.get("rationale", "")
        )
        if not is_groq_active:
            groq_status = "unavailable — rules-only"

        # 2. Extract Per-Source Confidences
        min_conf = float(self.confidence_fusion_cfg.get("min_source_confidence", 0.10))
        conf_local = max(min_conf, min(1.0, float(header.confidence)))

        matched_rules = regex_eval.get("matched_rules", [])
        if matched_rules:
            conf_regex = float(self.confidence_fusion_cfg.get("default_regex_confidence_match", 0.95))
        else:
            conf_regex = float(self.confidence_fusion_cfg.get("default_regex_confidence_nomatch", 0.70))

        if is_groq_active:
            conf_groq = max(min_conf, min(1.0, float(groq_dict.get("confidence", 0.85))))
        else:
            conf_groq = 0.0

        conf_sev = max(min_conf, min(1.0, float(header.confidence)))

        # 3. Dynamic Confidence-Modulated Weights
        w_sev_base = float(self.weights.get("w_severity", 0.20))
        w_reg_base = float(self.weights.get("w_regex", 0.30))
        w_loc_base = float(self.weights.get("w_local_model", 0.25))
        w_grq_base = float(self.weights.get("w_groq", 0.45)) if is_groq_active else 0.0

        is_conf_fusion = bool(self.confidence_fusion_cfg.get("enabled", True))
        if is_conf_fusion:
            raw_w_sev = w_sev_base * conf_sev
            raw_w_reg = w_reg_base * conf_regex
            raw_w_loc = w_loc_base * conf_local
            raw_w_grq = w_grq_base * conf_groq
        else:
            raw_w_sev, raw_w_reg, raw_w_loc, raw_w_grq = w_sev_base, w_reg_base, w_loc_base, w_grq_base

        total_w = raw_w_sev + raw_w_reg + raw_w_loc + raw_w_grq
        if total_w > 0:
            norm_w_sev = raw_w_sev / total_w
            norm_w_reg = raw_w_reg / total_w
            norm_w_loc = raw_w_loc / total_w
            norm_w_grq = raw_w_grq / total_w
        else:
            norm_w_sev, norm_w_reg, norm_w_loc, norm_w_grq = 0.25, 0.25, 0.25, 0.25

        contrib_sev = raw_severity_num * norm_w_sev
        contrib_reg = server_regex_score * norm_w_reg
        contrib_loc = local_model_score * norm_w_loc
        contrib_grq = groq_score * norm_w_grq

        base_priority = contrib_sev + contrib_reg + contrib_loc + contrib_grq

        # Compute Aggregate Fused Confidence
        if is_groq_active:
            aggregate_confidence = (
                norm_w_sev * conf_sev + norm_w_reg * conf_regex + norm_w_loc * conf_local + norm_w_grq * conf_groq
            )
        else:
            active_sub_w = norm_w_sev + norm_w_reg + norm_w_loc
            if active_sub_w > 0:
                aggregate_confidence = (
                    (norm_w_sev * conf_sev + norm_w_reg * conf_regex + norm_w_loc * conf_local) / active_sub_w
                )
            else:
                aggregate_confidence = 0.50

        aggregate_confidence = round(min(1.0, max(0.0, aggregate_confidence)), 4)

        # 4. Multi-Source Disagreement Detection & Safer-Side Life-Safety Policy
        active_scores = [server_regex_score, local_model_score]
        if is_groq_active:
            active_scores.append(groq_score)

        score_spread = max(active_scores) - min(active_scores)
        score_delta_thresh = float(self.disagreement_cfg.get("score_delta_threshold", 30.0))
        disagreement_detected = score_spread >= score_delta_thresh

        disagreement_reason: str | None = None
        disagreement_policy_applied: str | None = None

        if disagreement_detected:
            sources_summary = f"local_model={int(local_model_score)}, server_regex={int(server_regex_score)}"
            if is_groq_active:
                sources_summary += f", groq={int(groq_score)}"
            disagreement_reason = (
                f"Score divergence: active sources differ by {int(score_spread)} points (threshold={int(score_delta_thresh)}). "
                f"({sources_summary})."
            )
            flag_degraded = bool(self.disagreement_cfg.get("flag_degraded_local", True))
            if flag_degraded and (local_model_score < server_regex_score - score_delta_thresh or (is_groq_active and local_model_score < groq_score - score_delta_thresh)):
                disagreement_reason += " (Possible degraded on-device evaluation)."

            # Apply Life-Safety Safer-Side Escalation Policy
            safe_side_enabled = bool(self.disagreement_cfg.get("safe_side_bias_enabled", True))
            crit_anchor = float(self.disagreement_cfg.get("critical_elevation_anchor", 78.0))
            crit_thresh = float(self.thresholds.get("critical", 75.0))

            if safe_side_enabled:
                # If any high-confidence source assessed critical distress, elevate priority
                highest_signal = max(active_scores)
                has_high_distress_source = (
                    server_regex_score >= crit_thresh
                    or local_model_score >= 70
                    or (is_groq_active and groq_score >= 80)
                    or header.severity == SeverityLevel.CRITICAL
                )
                if has_high_distress_source and base_priority < crit_anchor:
                    base_priority = max(base_priority, crit_anchor)
                    disagreement_policy_applied = "SAFER_SIDE_ESCALATION (Elevated to critical tier based on life-safety policy)"
                elif highest_signal >= 35.0 and base_priority < 45.0:
                    base_priority = max(base_priority, 45.0)
                    disagreement_policy_applied = "SAFER_SIDE_ESCALATION (Elevated to warn tier based on life-safety policy)"

        # 5. Abstention & Human Review Trigger
        human_review_threshold = float(self.abstention_cfg.get("human_review_confidence_threshold", 0.65))
        flag_on_severe = bool(self.abstention_cfg.get("flag_on_severe_disagreement", True))

        needs_human_review = False
        abstention_reason: str | None = None

        if aggregate_confidence < human_review_threshold:
            needs_human_review = True
            abstention_reason = (
                f"Aggregate confidence ({aggregate_confidence:.2f}) is below safety review threshold "
                f"({human_review_threshold:.2f}). Flagged for commander verification."
            )
        elif flag_on_severe and disagreement_detected and aggregate_confidence < 0.78:
            needs_human_review = True
            abstention_reason = (
                f"Severe signal divergence ({int(score_spread)} pts) with aggregate confidence ({aggregate_confidence:.2f}). "
                "Flagged for human commander review."
            )

        # 6. Environmental Modifiers (Corroboration, Vulnerability, GIS, Trend, Decay)
        corr_config = self.modifiers.get("corroboration", {})
        bonus_per_report = float(corr_config.get("bonus_per_report", 4.0))
        max_corr_bonus = float(corr_config.get("max_corroboration_bonus", 15.0))
        corroboration_bonus = min(max_corr_bonus, max(0, corroborating_reports_count) * bonus_per_report)

        vuln_config = self.modifiers.get("vulnerability_bonus", {})
        vulnerability_bonus = 0.0
        victim_threshold = int(vuln_config.get("victim_count_threshold", 3))
        
        if groq_dict.get("vulnerable_victims", False) or (payload.victim_count and payload.victim_count > victim_threshold):
            vulnerability_bonus += float(vuln_config.get("child_or_elderly", 8.0))
        if payload.is_trapped or groq_dict.get("is_trapped", False):
            vulnerability_bonus += float(vuln_config.get("trapped_bonus", 10.0))
        if payload.has_medical_need or groq_dict.get("has_medical_need", False):
            vulnerability_bonus += float(vuln_config.get("medical_need_bonus", 5.0))

        spatial_cfg = self.modifiers.get("spatial_location", {})
        loc_weight = float(spatial_cfg.get("weight", 1.0))
        max_loc_bonus = float(spatial_cfg.get("max_location_bonus", 10.0))
        location_bonus = max(-max_loc_bonus, min(max_loc_bonus, location_risk_modifier * loc_weight))

        trend_cfg = self.modifiers.get("escalation_trend", {})
        trend_weight = float(trend_cfg.get("weight", 1.0))
        max_trend_bonus = float(trend_cfg.get("max_trend_bonus", 10.0))
        trend_bonus = max(-max_trend_bonus, min(max_trend_bonus, escalation_trend * trend_weight))

        decay_config = self.modifiers.get("temporal_decay", {})
        half_life = float(decay_config.get("half_life_hours", 6.0))
        min_factor = float(decay_config.get("min_decay_factor", 0.5))
        if hours_elapsed > 0:
            decay_factor = max(min_factor, math.pow(0.5, hours_elapsed / half_life))
        else:
            decay_factor = 1.0

        # 7. Compute Final Calibrated Operational Priority (0 to 100)
        unclamped_fused = (
            base_priority
            + corroboration_bonus
            + vulnerability_bonus
            + location_bonus
            + trend_bonus
        ) * decay_factor
        final_priority = max(0.0, min(100.0, round(unclamped_fused, 2)))
        int_priority = max(0, min(100, int(round(final_priority))))

        # 8. Resolve Final Severity Tier
        crit_thresh = float(self.thresholds.get("critical", 75.0))
        warn_thresh = float(self.thresholds.get("medium", self.thresholds.get("warn", 35.0)))

        if final_priority >= crit_thresh:
            resolved_severity = SeverityLevel.CRITICAL
        elif final_priority >= warn_thresh:
            resolved_severity = SeverityLevel.WARN
        else:
            resolved_severity = SeverityLevel.INFO

        # 9. Resolve Final Category
        if groq_dict.get("category") and groq_dict.get("category") != EmergencyCategory.OTHER:
            resolved_category = groq_dict["category"]
        elif regex_eval.get("category") and regex_eval.get("category") != EmergencyCategory.OTHER:
            resolved_category = regex_eval["category"]
        else:
            resolved_category = header.category

        origin_sev_val = header.severity.value if hasattr(header.severity, "value") else str(header.severity)
        origin_cat_val = header.category.value if hasattr(header.category, "value") else str(header.category)

        # 10. Human-Readable "Why is this critical?" Bullet List for Incident Screen
        bullets: list[str] = []
        if resolved_severity == SeverityLevel.CRITICAL:
            if regex_eval.get("matched_rules"):
                bullets.append(f"High-urgency emergency language matched ({', '.join(regex_eval['matched_rules'])})")
            if local_model_score >= 70 or header.severity == SeverityLevel.CRITICAL:
                bullets.append(f"On-device neural model assessed critical severity (score: {int(local_model_score)})")
            if is_groq_active and groq_dict.get("urgency"):
                bullets.append(f"Groq cloud teacher verified urgency {groq_dict.get('urgency')}/5")
            if vulnerability_bonus > 0:
                bullets.append(f"High-risk vulnerability flags present (+{vulnerability_bonus:.1f} bonus)")
        elif resolved_severity == SeverityLevel.WARN:
            if regex_eval.get("matched_rules"):
                bullets.append(f"Urgent distress indicators matched ({', '.join(regex_eval['matched_rules'])})")
            if local_model_score >= 35:
                bullets.append(f"On-device model assessed moderate urgency (score: {int(local_model_score)})")
            if is_groq_active and groq_dict.get("urgency"):
                bullets.append(f"Groq cloud teacher assessed urgency {groq_dict.get('urgency')}/5")
        else:
            bullets.append("Non-emergency or safe status check-in verified")

        if not is_groq_active:
            bullets.append("Groq cloud triage unavailable — prioritized via deterministic rules and on-device model")

        if corroborating_reports_count > 0:
            bullets.append(f"Corroborated by {corroborating_reports_count} reports in local cluster (+{corroboration_bonus:.1f} bonus)")
        if abs(location_bonus) > 0.01:
            bullets.append(f"Spatial hazard risk modifier ({location_bonus:+.1f})")
        if abs(trend_bonus) > 0.01:
            bullets.append(f"Incident report acceleration trend ({trend_bonus:+.1f})")

        if disagreement_detected:
            bullets.append(
                f"⚠️ Signal disagreement: sources diverged by {int(score_spread)} pts. "
                f"{disagreement_policy_applied or 'Evaluated under life-safety policy.'}"
            )

        if needs_human_review:
            bullets.append(f"🚨 Flagged for human review: {abstention_reason}")

        if groq_dict.get("injection_suspected"):
            bullets.append("⚠️ Prompt injection / override pattern detected and neutralized")

        factors_summary = {
            "severity": round(contrib_sev, 2),
            "regex": round(contrib_reg, 2),
            "local_model": round(contrib_loc, 2),
            "groq": round(contrib_grq, 2),
            "corroboration": round(corroboration_bonus, 2),
            "vulnerability": round(vulnerability_bonus, 2),
            "location": round(location_bonus, 2),
            "trend": round(trend_bonus, 2),
            "decay": round(decay_factor, 3),
        }

        source_confidences = {
            "severity_header": round(conf_sev, 3),
            "server_regex": round(conf_regex, 3),
            "local_model": round(conf_local, 3),
            "groq_cloud": round(conf_groq, 3),
        }

        # 11. Complete Auditable Reasoning Breakdown
        reasoning = AIReasoningBreakdown(
            regex_contribution=round(contrib_reg, 2),
            local_model_contribution=round(contrib_loc, 2),
            groq_contribution=round(contrib_grq, 2),
            corroboration_bonus=round(corroboration_bonus, 2),
            vulnerability_bonus=round(vulnerability_bonus, 2),
            location_modifier=round(location_bonus, 2),
            trend_modifier=round(trend_bonus, 2),
            time_decay_factor=round(decay_factor, 3),
            extracted_entities=groq_dict.get("entities", []),
            groq_rationale=groq_dict.get("rationale", ""),
            matched_rules=regex_eval.get("matched_rules", []),
            origin_severity=origin_sev_val,
            origin_regex_score=header.regex_score,
            origin_local_model_score=header.local_model_score,
            origin_confidence=header.confidence,
            origin_category=origin_cat_val,
            server_regex_score=int(server_regex_score),
            disagreement_detected=disagreement_detected,
            disagreement_reason=disagreement_reason,
            disagreement_policy_applied=disagreement_policy_applied,
            needs_human_review=needs_human_review,
            abstention_reason=abstention_reason,
            source_confidences=source_confidences,
            groq=groq_status,
            per_report_severity=origin_sev_val,
            incident_priority=int_priority,
            injection_suspected=bool(groq_dict.get("injection_suspected", False)),
            injection_reasons=list(groq_dict.get("injection_reasons", [])),
            explanation_bullets=bullets,
            factors=factors_summary,
        )

        return {
            "severity": resolved_severity,
            "priority_score": final_priority,
            "category": resolved_category,
            "confidence": aggregate_confidence,
            "needs_human_review": needs_human_review,
            "reasoning": reasoning,
        }
