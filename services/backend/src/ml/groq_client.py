"""
Project Pukar - Groq Online Teacher & Semantic Triage Client
============================================================

Provides high-fidelity crisis semantic triage, entity extraction, and structured
reasoning using cloud LLM (Llama-3 on Groq).

Key Design Tenets:
1. Strict Typed JSON: Validates outputs into `GroqTriageResult` (severity, category, urgency 1-5, entities, rationale, confidence).
2. Corrective JSON Repair: Local syntax repair pass, with one corrective re-prompt on malformed JSON before fallback.
3. Cost-Efficient Self-Consistency: Single-shot for clear-cut cases; N=3 majority-vote sampling ONLY for borderline cases.
4. Centralized Retry & Backoff: Structured exponential backoff with a categorized error taxonomy.
5. Externalized Configuration: Dynamic settings loaded from `ml/configs/groq.yaml`.
6. Prompt Injection Defense: Untrusted SOS inputs sanitized and isolated in boundary delimiters.
7. Graceful Degradation: Never raises unhandled exceptions into dispatch pipelines.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

from .cache import cache_response, get_cached_response
from .contracts import Category, EmergencyCategory, GroqTriageResult, Severity, SeverityLevel
from .guard import (
    SanitizationResult,
    get_guard_system_instruction,
    sanitize,
    validate_schema,
    wrap_untrusted_data,
)
from .meter import record_usage

load_dotenv()

logger = logging.getLogger("pukar.ml.groq_client")


# ==============================================================================
# Structured Error Taxonomy
# ==============================================================================

class GroqErrorCode(StrEnum):
    """Structured taxonomy of Groq LLM API and processing errors."""
    AUTHENTICATION_ERROR = "authentication_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    TIMEOUT_ERROR = "timeout_error"
    SERVER_ERROR = "server_error"
    CONNECTION_ERROR = "connection_error"
    MALFORMED_OUTPUT_ERROR = "malformed_output_error"
    SCHEMA_VALIDATION_ERROR = "schema_validation_error"
    UNKNOWN_ERROR = "unknown_error"


class GroqExecutionError(Exception):
    """Structured exception wrapping Groq API and parsing failures."""

    def __init__(
        self,
        error_code: GroqErrorCode,
        message: str,
        status_code: int | None = None,
        retryable: bool = False,
    ):
        super().__init__(f"[{error_code.value}] {message}")
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.retryable = retryable


# ==============================================================================
# Groq Client Implementation
# ==============================================================================

class GroqClient:
    """
    Online semantic triage teacher powered by Groq LLM API with self-consistency
    and corrective auto-repair.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        config_path: str | Path | None = None,
        prompt_path: str | Path | None = None,
    ):
        # 1. Load externalized YAML configuration
        self.config_path = self._resolve_config_path(config_path)
        self.config = self._load_config()

        # 2. Extract settings from config with env overrides
        # Prefer get_settings() as single source of truth over raw os.getenv;
        # this ensures config.py value takes precedence over stale environment.
        try:
            from src.config import get_settings as _get_settings
            _s = _get_settings()
            self.api_key = api_key or _s.GROQ_API_KEY or os.getenv("GROQ_API_KEY")
            self.model = model or _s.GROQ_MODEL or os.getenv("GROQ_MODEL", self.config.get("model", "llama3-8b-8192"))
        except Exception:
            self.api_key = api_key or os.getenv("GROQ_API_KEY")
            self.model = model or os.getenv("GROQ_MODEL", self.config.get("model", "llama3-8b-8192"))

        env_timeout = os.getenv("GROQ_TIMEOUT_SECONDS")
        cfg_timeout = float(self.config.get("timeout_seconds", 2.0))
        self.timeout = float(timeout if timeout is not None else (env_timeout if env_timeout else cfg_timeout))

        env_retries = os.getenv("GROQ_MAX_RETRIES")
        cfg_retries = int(self.config.get("max_retries", 2))
        self.max_retries = int(max_retries if max_retries is not None else (env_retries if env_retries else cfg_retries))

        self.temperature = float(self.config.get("temperature", 0.1))
        self.max_tokens = int(self.config.get("max_tokens", 300))

        # 3. Subsystem configurations
        self.self_consistency_cfg = self.config.get("self_consistency", {})
        self.json_repair_cfg = self.config.get("json_repair", {})
        self.error_taxonomy_cfg = self.config.get("error_taxonomy", {})

        # 4. Load externalized prompt
        self.prompt_path = self._resolve_prompt_path(prompt_path)
        self.system_prompt = self._load_system_prompt()

        # 5. Initialize SDK Client
        self._client = None
        if self.api_key:
            try:
                from groq import Groq
                self._client = Groq(
                    api_key=self.api_key,
                    timeout=self.timeout,
                    max_retries=0,  # We manage explicit application-level retry/backoff
                )
            except Exception as e:
                logger.warning(f"Groq SDK client initialization deferred/failed: {e}")

    def _resolve_config_path(self, custom_path: str | Path | None) -> Path:
        if custom_path:
            return Path(custom_path)

        candidates = [
            Path(__file__).parent / "configs" / "groq.yaml",
            Path(__file__).resolve().parents[4] / "ml" / "configs" / "groq.yaml",
            Path("ml/configs/groq.yaml"),
        ]
        for p in candidates:
            if p.exists():
                return p
        return candidates[0]

    def _load_config(self) -> dict[str, Any]:
        if self.config_path and self.config_path.exists():
            try:
                with open(self.config_path, encoding="utf-8") as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                logger.warning(f"Failed to load groq.yaml from {self.config_path}: {e}")
        return {}

    def _resolve_prompt_path(self, custom_path: str | Path | None) -> Path:
        if custom_path:
            return Path(custom_path)

        candidates = [
            Path(__file__).parent / "configs" / "groq_prompt.txt",
            Path(__file__).resolve().parents[4] / "ml" / "configs" / "groq_prompt.txt",
            Path("ml/configs/groq_prompt.txt"),
        ]
        for p in candidates:
            if p.exists():
                return p
        return candidates[0]

    def _load_system_prompt(self) -> str:
        base_prompt = ""
        if self.prompt_path and self.prompt_path.exists():
            try:
                with open(self.prompt_path, encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        base_prompt = content
            except Exception as e:
                logger.warning(f"Could not read prompt from {self.prompt_path}: {e}")

        # Fallback default prompt if file missing
        if not base_prompt:
            base_prompt = (
                "You are the Crisis Intelligence Triage Engine for Project Pukar (Emergency Mesh SOS Platform). "
                "Analyze the given emergency message (English, Hindi, or Hinglish). "
                "Output actionable dispatcher rationale and strictly valid JSON matching this schema:\n"
                "{\n"
                '  "severity": "info" | "warn" | "critical",\n'
                '  "category": "rescue" | "medical" | "fire" | "shelter" | "other",\n'
                '  "urgency": 1 | 2 | 3 | 4 | 5,\n'
                '  "entities": [<list of strings>],\n'
                '  "rationale": "<actionable operational dispatcher rationale>",\n'
                '  "confidence": <float 0.0 to 1.0>\n'
                "}"
            )

        # Append mandatory data isolation and injection defense guardrail
        return f"{base_prompt}\n\n{get_guard_system_instruction()}"

    def is_available(self) -> bool:
        """Returns True if a configured Groq client is ready."""
        return bool(self._client and self.api_key)

    # ==========================================================================
    # Error Taxonomy & Classification
    # ==========================================================================

    def classify_error(self, exc: Exception) -> tuple[GroqErrorCode, bool]:
        """
        Categorizes an exception into a structured GroqErrorCode and retryability flag.
        """
        err_str = str(exc).lower()

        # Check for authentication failures (non-retryable)
        auth_keywords = self.error_taxonomy_cfg.get(
            "auth_error_keywords",
            ["invalid_api_key", "401", "authentication", "unauthorized", "permission_denied"],
        )
        if any(k in err_str for k in auth_keywords):
            return GroqErrorCode.AUTHENTICATION_ERROR, False

        # Check for rate limit / quota exhaustion (retryable)
        rate_keywords = self.error_taxonomy_cfg.get(
            "rate_limit_keywords",
            ["rate_limit", "429", "resource_exhausted", "quota"],
        )
        if any(k in err_str for k in rate_keywords):
            return GroqErrorCode.RATE_LIMIT_ERROR, True

        # Check for timeouts (retryable)
        timeout_keywords = self.error_taxonomy_cfg.get(
            "timeout_keywords",
            ["timeout", "timed out", "deadline_exceeded", "connection_timeout"],
        )
        if any(k in err_str for k in timeout_keywords) or isinstance(exc, (TimeoutError,)):
            return GroqErrorCode.TIMEOUT_ERROR, True

        # Check for server errors (500, 502, 503, 504) (retryable)
        server_keywords = self.error_taxonomy_cfg.get(
            "server_error_keywords",
            ["500", "502", "503", "504", "internal_server_error", "service_unavailable"],
        )
        if any(k in err_str for k in server_keywords):
            return GroqErrorCode.SERVER_ERROR, True

        # Check for connection drops
        if "connection" in err_str or "broken pipe" in err_str or "reset by peer" in err_str:
            return GroqErrorCode.CONNECTION_ERROR, True

        return GroqErrorCode.UNKNOWN_ERROR, False

    # ==========================================================================
    # Centralized API Execution with Retry & Backoff
    # ==========================================================================

    def _call_groq_api(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
        timeout: float | None = None,
    ) -> tuple[str, float, dict[str, int]]:
        """
        Executes a Groq chat completion request with exponential backoff and error taxonomy handling.
        Returns: (raw_content, latency_ms, token_usage_dict)
        """
        temp = self.temperature if temperature is None else temperature
        tokens = self.max_tokens if max_tokens is None else max_tokens
        tout = self.timeout if timeout is None else timeout

        last_error: Exception | None = None

        for attempt in range(self.max_retries + 1):
            t_start = time.perf_counter()
            try:
                response = self._client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temp,
                    max_tokens=tokens,
                    response_format={"type": "json_object"},
                    timeout=tout,
                )
                latency_ms = round((time.perf_counter() - t_start) * 1000.0, 2)

                usage = getattr(response, "usage", None)
                prompt_tokens = getattr(usage, "prompt_tokens", 0) if usage else 0
                completion_tokens = getattr(usage, "completion_tokens", 0) if usage else 0
                total_tokens = getattr(usage, "total_tokens", 0) if usage else 0

                token_dict = {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                }

                raw_content = response.choices[0].message.content or "{}"
                record_usage(
                    operation="triage",
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    latency_ms=latency_ms,
                    model=self.model,
                )
                return raw_content, latency_ms, token_dict

            except Exception as e:
                latency_ms = round((time.perf_counter() - t_start) * 1000.0, 2)
                last_error = e
                err_code, is_retryable = self.classify_error(e)
                record_usage(
                    operation="triage",
                    latency_ms=latency_ms,
                    error=True,
                    model=self.model,
                )

                logger.warning(
                    "Groq attempt %d/%d failed | error_code=%s | retryable=%s | latency_ms=%.1f | error=%s",
                    attempt + 1,
                    self.max_retries + 1,
                    err_code.value,
                    is_retryable,
                    latency_ms,
                    e,
                )

                if not is_retryable or attempt >= self.max_retries:
                    raise GroqExecutionError(
                        error_code=err_code,
                        message=str(e),
                        retryable=is_retryable,
                    ) from e

                # Exponential backoff: 0.1s, 0.2s, 0.4s
                time.sleep(0.1 * (2 ** attempt))

        raise GroqExecutionError(
            error_code=GroqErrorCode.UNKNOWN_ERROR,
            message=f"All retries exhausted ({last_error!s})",
            retryable=False,
        )

    # ==========================================================================
    # Public Triage Seam
    # ==========================================================================

    def triage(self, text: str) -> GroqTriageResult:
        """
        Executes semantic triage on decrypted SOS distress message.
        Returns validated GroqTriageResult Pydantic model.
        """
        raw_dict = self.analyze_message(text)
        return GroqTriageResult(
            severity=raw_dict["severity"],
            category=raw_dict["category"],
            urgency=raw_dict["urgency"],
            entities=raw_dict["entities"],
            rationale=raw_dict["rationale"],
            confidence=raw_dict["confidence"],
            injection_suspected=raw_dict.get("injection_suspected", False),
            injection_reasons=raw_dict.get("injection_reasons", []),
        )

    def analyze_message(self, text: str) -> dict[str, Any]:
        """
        Core inference method called by backend pipelines and PriorityEngine.
        Employs:
        1. Prompt injection defense and isolation formatting.
        2. Response cache check by decrypted-text hash (0ms latency on hit).
        3. Single-shot fast path for clear-cut emergencies (cheap & fast).
        4. Self-consistency majority voting (N=3) for borderline cases only.
        5. One corrective re-prompt on malformed JSON before degradation.
        """
        # 0. Check Response Cache
        cached_result = get_cached_response("groq_triage", text)
        if cached_result is not None:
            record_usage(operation="triage", cached=True, model=self.model)
            res_copy = dict(cached_result)
            res_copy["cached"] = True
            logger.debug("Groq triage response cache hit for text hash")
            return res_copy

        guard_res = sanitize(text)

        if not guard_res.sanitized_text:
            return self._fallback_response("Empty distress text provided", guard_res=guard_res)

        if not self.is_available():
            return self._fallback_response(
                "Groq API unavailable or unconfigured - fallback to rule scoring",
                guard_res=guard_res,
            )

        isolated_content = f"EMERGENCY SOS MESSAGE DATA:\n{wrap_untrusted_data(guard_res.sanitized_text)}"
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": isolated_content},
        ]

        # 1. Single-shot Initial Sample
        try:
            raw_content, latency_ms, token_usage = self._call_groq_api(
                messages=messages,
                temperature=self.temperature,
            )
            initial_result = self._parse_and_validate_response(
                raw_content=raw_content,
                messages=messages,
                latency_ms=latency_ms,
                guard_res=guard_res,
            )
        except Exception as e:
            err_code, _ = self.classify_error(e)
            logger.warning("Groq triage initial call failed | error_code=%s | error=%s", err_code.value, e)
            return self._fallback_response(f"Groq invocation failed ({e!s}) - graceful fallback active", guard_res=guard_res)

        # 2. Check Borderline Criteria for Self-Consistency
        is_sc_enabled = self.self_consistency_cfg.get("enabled", True)
        is_borderline = self._is_borderline_case(initial_result)

        if not is_sc_enabled or not is_borderline:
            # Fast, single-shot cheap path
            initial_result["self_consistency_used"] = False
            initial_result["sample_count"] = 1
            cache_response("groq_triage", text, initial_result)
            logger.info(
                "Groq triage single-shot completed | model=%s | severity=%s | urgency=%d | confidence=%.2f | self_consistency=False",
                self.model,
                initial_result["severity"].value,
                initial_result["urgency"],
                initial_result["confidence"],
            )
            return initial_result

        # 3. Borderline Case -> Sample N=3 at low temperature and majority-vote
        sample_count = int(self.self_consistency_cfg.get("sample_count", 3))
        sample_temp = float(self.self_consistency_cfg.get("sample_temperature", 0.3))

        samples = [initial_result]
        additional_needed = max(0, sample_count - 1)

        for s_idx in range(additional_needed):
            try:
                s_raw, s_lat, _ = self._call_groq_api(
                    messages=messages,
                    temperature=sample_temp,
                )
                s_parsed = self._parse_and_validate_response(
                    raw_content=s_raw,
                    messages=messages,
                    latency_ms=s_lat,
                    guard_res=guard_res,
                )
                samples.append(s_parsed)
            except Exception as e:
                logger.debug("Self-consistency additional sample %d failed: %s", s_idx + 1, e)

        # 4. Perform Majority Voting
        fused = self._majority_vote_fusion(samples, guard_res=guard_res)
        cache_response("groq_triage", text, fused)
        return fused

    def _is_borderline_case(self, result: dict[str, Any]) -> bool:
        """
        Determines if an inference result lies on a decision boundary or has low confidence.
        """
        conf_threshold = float(self.self_consistency_cfg.get("confidence_threshold", 0.75))
        borderline_urgencies = self.self_consistency_cfg.get("borderline_urgencies", [3, 4])
        borderline_urgency_scores = self.self_consistency_cfg.get("borderline_urgency_scores", [50, 60, 70])
        borderline_severities = self.self_consistency_cfg.get("borderline_severities", ["warn"])

        confidence = float(result.get("confidence", 0.8))
        urgency = int(result.get("urgency", 3))
        urgency_score = int(result.get("urgency_score", 50))
        sev_val = str(result.get("severity", "")).lower()

        # Low confidence trigger
        if confidence < conf_threshold:
            return True

        # Urgency boundary trigger (e.g. 3 or 4)
        if urgency in borderline_urgencies or urgency_score in borderline_urgency_scores:
            return True

        # Warn/Critical boundary trigger
        if sev_val in borderline_severities:
            return True

        return False

    def _majority_vote_fusion(
        self,
        samples: list[dict[str, Any]],
        guard_res: SanitizationResult | None = None,
    ) -> dict[str, Any]:
        """
        Synthesizes multiple stochastic samples into one calibrated majority verdict.
        """
        if not samples:
            return self._fallback_response("No valid samples for majority voting", guard_res=guard_res)

        if len(samples) == 1:
            samples[0]["self_consistency_used"] = True
            samples[0]["sample_count"] = 1
            return samples[0]

        # 1. Tally Severity Votes
        sev_votes: dict[SeverityLevel, int] = {}
        for s in samples:
            sev = s["severity"]
            sev_votes[sev] = sev_votes.get(sev, 0) + 1

        # Determine winner (tie-break goes to highest urgency / higher severity)
        def severity_rank(sev: SeverityLevel) -> int:
            return {SeverityLevel.CRITICAL: 3, SeverityLevel.WARN: 2, SeverityLevel.INFO: 1}.get(sev, 0)

        sorted_sevs = sorted(
            sev_votes.keys(),
            key=lambda k: (sev_votes[k], severity_rank(k)),
            reverse=True,
        )
        resolved_sev = sorted_sevs[0]
        majority_count = sev_votes[resolved_sev]

        # Filter samples agreeing with majority severity
        agreeing_samples = [s for s in samples if s["severity"] == resolved_sev]
        if not agreeing_samples:
            agreeing_samples = samples

        # 2. Tally Category Votes
        cat_votes: dict[EmergencyCategory, int] = {}
        for s in agreeing_samples:
            cat = s["category"]
            cat_votes[cat] = cat_votes.get(cat, 0) + 1
        resolved_cat = max(cat_votes.keys(), key=lambda k: cat_votes[k])

        # 3. Urgency: Median of agreeing samples
        urgencies = [s["urgency"] for s in agreeing_samples]
        urgencies.sort()
        resolved_urgency = urgencies[len(urgencies) // 2]
        urgency_score_mapping = {1: 20, 2: 40, 3: 60, 4: 80, 5: 100}
        resolved_urgency_score = urgency_score_mapping.get(resolved_urgency, resolved_urgency * 20)

        # 4. Entities: Union across agreeing samples
        merged_entities: list[str] = []
        for s in agreeing_samples:
            for ent in s.get("entities", []):
                if ent not in merged_entities:
                    merged_entities.append(ent)

        # 5. Rationale: Highest confidence sample agreeing with majority
        best_sample = max(agreeing_samples, key=lambda s: s.get("confidence", 0.0))
        resolved_rationale = best_sample.get("rationale", "")

        # 6. Calibrated Confidence (agreement ratio * average confidence)
        agreement_ratio = float(majority_count) / float(len(samples))
        avg_conf = sum(s.get("confidence", 0.8) for s in agreeing_samples) / len(agreeing_samples)
        calibrated_conf = round(min(1.0, max(0.5, (agreement_ratio * 0.5) + (avg_conf * 0.5))), 4)

        # 7. Aggregate flags
        is_trapped = any(s.get("is_trapped", False) for s in agreeing_samples)
        has_medical_need = any(s.get("has_medical_need", False) for s in agreeing_samples)
        vulnerable_victims = any(s.get("vulnerable_victims", False) for s in agreeing_samples)

        vote_summary = [s["severity"].value for s in samples]
        logger.info(
            "Groq self-consistency majority voting applied | samples=%d | votes=%s | resolved_severity=%s | confidence=%.2f",
            len(samples),
            vote_summary,
            resolved_sev.value,
            calibrated_conf,
        )

        return {
            "severity": resolved_sev,
            "category": resolved_cat,
            "urgency": resolved_urgency,
            "urgency_score": resolved_urgency_score,
            "confidence": calibrated_conf,
            "entities": merged_entities,
            "rationale": resolved_rationale,
            "is_trapped": is_trapped,
            "has_medical_need": has_medical_need,
            "vulnerable_victims": vulnerable_victims,
            "latency_ms": sum(s.get("latency_ms", 0.0) for s in samples),
            "injection_suspected": guard_res.injection_suspected if guard_res else False,
            "injection_reasons": guard_res.injection_reasons if guard_res else [],
            "self_consistency_used": True,
            "sample_count": len(samples),
            "sample_votes": vote_summary,
        }

    # ==========================================================================
    # JSON Parsing, Validation & Corrective Re-prompting
    # ==========================================================================

    def _parse_and_validate_response(
        self,
        raw_content: str,
        messages: list[dict[str, str]] | None = None,
        latency_ms: float = 0.0,
        guard_res: SanitizationResult | None = None,
    ) -> dict[str, Any]:
        """
        Parses raw LLM content. If malformed, attempts local repair first;
        if local repair fails, executes one corrective re-prompt before falling back.
        """
        parsed: dict[str, Any] = self._repair_json(raw_content)

        # If local repair failed and corrective prompts are permitted
        if not parsed and messages is not None:
            max_corrective = int(self.json_repair_cfg.get("max_corrective_prompts", 1))
            if max_corrective >= 1:
                logger.info("Triggering corrective re-prompt for malformed LLM JSON output")
                corrective_messages = list(messages) + [
                    {"role": "assistant", "content": raw_content},
                    {
                        "role": "user",
                        "content": (
                            "CORRECTION REQUIRED: Your previous response was not valid JSON. "
                            "Please fix the formatting/syntax error and output ONLY strictly valid JSON "
                            "matching the required schema without preamble or commentary."
                        ),
                    },
                ]
                try:
                    repaired_raw, rep_lat, _ = self._call_groq_api(
                        messages=corrective_messages,
                        temperature=0.0,
                    )
                    parsed = self._repair_json(repaired_raw)
                    latency_ms += rep_lat
                    if parsed:
                        logger.info("Corrective re-prompt successfully repaired JSON output")
                except Exception as ce:
                    logger.warning("Corrective re-prompt failed (%s)", ce)

        # 1. Sanitize Severity
        raw_sev = str(parsed.get("severity", "warn")).strip().lower()
        sev = self._coerce_severity(raw_sev)

        # 2. Sanitize Category
        raw_cat = str(parsed.get("category", "other")).strip().lower()
        cat = self._coerce_category(raw_cat)

        # 3. Sanitize Urgency (1 to 5)
        raw_urgency = parsed.get("urgency")
        if raw_urgency is None:
            raw_urgency = parsed.get("urgency_score")
            if raw_urgency is not None:
                urgency = max(1, min(5, int(round(float(raw_urgency) / 20.0))))
            else:
                urgency = 5 if sev == Severity.CRITICAL else (3 if sev == Severity.WARN else 1)
        else:
            try:
                urgency = max(1, min(5, int(raw_urgency)))
            except (ValueError, TypeError):
                urgency = 3

        urgency_score_mapping = {1: 20, 2: 40, 3: 60, 4: 80, 5: 100}
        urgency_score = urgency_score_mapping.get(urgency, urgency * 20)

        # 4. Sanitize Confidence
        try:
            confidence = max(0.0, min(1.0, float(parsed.get("confidence", 0.85))))
        except (ValueError, TypeError):
            confidence = 0.80

        # 5. Sanitize Entities
        raw_entities = parsed.get("entities", [])
        if isinstance(raw_entities, list):
            entities = [str(item).strip() for item in raw_entities if str(item).strip()]
        elif isinstance(raw_entities, str) and raw_entities.strip():
            entities = [raw_entities.strip()]
        else:
            entities = []

        # 6. Sanitize Rationale
        rationale = str(parsed.get("rationale", "")).strip()
        if not rationale:
            rationale = f"Operational triage: {sev.value.upper()} urgency ({urgency}/5) in domain {cat.value}."

        # 7. Derived flags for PriorityEngine compatibility
        entities_text = " ".join(entities).lower()
        is_trapped = bool(parsed.get("is_trapped", False)) or any(
            k in entities_text or k in rationale.lower() for k in ["trapped", "fase", "rubble", "collapse", "debris"]
        )
        has_medical_need = bool(parsed.get("has_medical_need", False)) or any(
            k in entities_text or k in rationale.lower() for k in ["bleeding", "injury", "unconscious", "fracture", "medical"]
        )
        vulnerable_victims = bool(parsed.get("vulnerable_victims", False)) or any(
            k in entities_text or k in rationale.lower() for k in ["child", "infant", "pregnant", "elderly", "baby", "dadi", "buzurg"]
        )

        injection_suspected = guard_res.injection_suspected if guard_res else False
        injection_reasons = guard_res.injection_reasons if guard_res else []

        result_dict = {
            "severity": SeverityLevel(sev.value),
            "category": EmergencyCategory(cat.value),
            "urgency": urgency,
            "urgency_score": urgency_score,
            "confidence": round(confidence, 4),
            "entities": entities,
            "rationale": rationale,
            "is_trapped": is_trapped,
            "has_medical_need": has_medical_need,
            "vulnerable_victims": vulnerable_victims,
            "latency_ms": latency_ms,
            "injection_suspected": injection_suspected,
            "injection_reasons": injection_reasons,
        }

        # Pydantic schema validation check
        validate_schema(result_dict, GroqTriageResult)

        return result_dict

    def _repair_json(self, text: str) -> dict[str, Any]:
        """
        Attempts direct JSON parsing, then applies regex extraction and sanitization repairs.
        """
        cleaned = text.strip()

        # Remove markdown code fences if present (```json ... ```)
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r"\s*```$", "", cleaned)

        # 1. Direct parse attempt
        try:
            return json.loads(cleaned)
        except Exception:
            pass

        # 2. Extract outermost JSON object { ... }
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            candidate = match.group(0)
            try:
                return json.loads(candidate)
            except Exception:
                # Remove trailing commas before closing braces
                fixed = re.sub(r",\s*([\}\]])", r"\1", candidate)
                try:
                    return json.loads(fixed)
                except Exception:
                    pass

        return {}

    def _coerce_severity(self, raw_sev: str) -> Severity:
        sev_map = {
            "critical": Severity.CRITICAL,
            "high": Severity.CRITICAL,
            "severe": Severity.CRITICAL,
            "extreme": Severity.CRITICAL,
            "warn": Severity.WARN,
            "warning": Severity.WARN,
            "medium": Severity.WARN,
            "moderate": Severity.WARN,
            "urgent": Severity.WARN,
            "info": Severity.INFO,
            "low": Severity.INFO,
            "informational": Severity.INFO,
            "safe": Severity.INFO,
        }
        return sev_map.get(raw_sev, Severity.WARN)

    def _coerce_category(self, raw_cat: str) -> Category:
        cat_map = {
            "rescue": Category.RESCUE,
            "trapped": Category.RESCUE,
            "flood": Category.RESCUE,
            "evacuation": Category.RESCUE,
            "medical": Category.MEDICAL,
            "injury": Category.MEDICAL,
            "health": Category.MEDICAL,
            "ambulance": Category.MEDICAL,
            "fire": Category.FIRE,
            "blast": Category.FIRE,
            "explosion": Category.FIRE,
            "gas": Category.FIRE,
            "shelter": Category.SHELTER,
            "food": Category.SHELTER,
            "water": Category.SHELTER,
            "ration": Category.SHELTER,
            "blanket": Category.SHELTER,
            "other": Category.OTHER,
            "hazard": Category.OTHER,
            "safe": Category.OTHER,
        }
        return cat_map.get(raw_cat, Category.OTHER)

    def _fallback_response(self, reason: str, guard_res: SanitizationResult | None = None) -> dict[str, Any]:
        """
        Resilient default response guaranteeing zero crashes in downstream dispatch.
        """
        return {
            "severity": SeverityLevel.WARN,
            "category": EmergencyCategory.OTHER,
            "urgency": 3,
            "urgency_score": 50,
            "confidence": 0.5,
            "entities": [],
            "rationale": reason,
            "is_trapped": False,
            "has_medical_need": False,
            "vulnerable_victims": False,
            "latency_ms": 0.0,
            "injection_suspected": guard_res.injection_suspected if guard_res else False,
            "injection_reasons": guard_res.injection_reasons if guard_res else [],
            "self_consistency_used": False,
            "sample_count": 0,
        }
