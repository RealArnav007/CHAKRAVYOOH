"""
Project Pukar - Master Scorer Interface & Ingestion Public Seam
==============================================================

Overview:
---------
Defines the primary public entry point `score(packet, decrypted_text)` invoked by Harshit's
backend ingestion pipeline immediately after verifying cryptographic packet signatures and
decrypting the distress message payload.

Architectural Contract & Trust Boundary:
----------------------------------------
1. Input Contract:
   - `packet`: Dict containing the signed immutable packet header (or SignedSOSHeader model).
     Contains on-device assessed signals: severity, regex_score, local_model_score, confidence,
     category, and language.
   - `decrypted_text`: Raw decrypted distress message string (or DecryptedSOSPayload model/dict).
2. Trusted-but-Reverified:
   - On-device telemetry in the packet header is trusted as the initial edge assessment, but
     immediately reverified server-side against deterministic regex rules and cloud Groq LLM triage.
3. Graceful Degradation SLA:
   - External dependencies (Groq cloud API, network timeouts, unparseable telemetry) NEVER raise
     exceptions into Harshit's ingestion pipeline. Any failure degrades smoothly to deterministic
     rule-based scoring.
4. Output Contract:
   - Returns a strictly-typed Pydantic `ScoreResult` containing:
     * severity: Severity enum ('info', 'warn', 'critical')
     * priority: int (0 to 100 calibrated dispatch priority)
     * category: Category enum ('rescue', 'medical', 'fire', 'shelter', 'other')
     * confidence: float (0.0 to 1.0)
     * reasoning: dict containing auditable multi-factor transparency breakdown
"""

import asyncio
import concurrent.futures
import logging
import time
import uuid
from typing import Any

from .briefing import brief
from .cache import cache_response, get_cached_response
from .contracts import (
    Briefing,
    Category,
    CorrelationVerdict,
    DecryptedSOSPayload,
    Entities,
    EscalationResult,
    ResourceCategory,
    ScoreResult,
    Severity,
    SignedSOSHeader,
)
from .correlate import correlate, embed
from .extract import extract
from .false_alarm import false_alarm
from .groq_client import GroqClient
from .guard import sanitize
from .meter import record_usage
from .normalize import normalize
from .observability import ReportTrace, record_report_trace
from .priority_engine import PriorityEngine
from .regex_engine import RegexEngine
from .trend import escalation

logger = logging.getLogger("pukar.scorer")


def _run_sync(coro: Any) -> Any:
    """Helper to run an async coroutine synchronously across all environments."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # Inside an existing event loop: run in a dedicated worker thread
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            return executor.submit(asyncio.run, coro).result()
    else:
        return asyncio.run(coro)


class Scorer:
    """
    Master Ingestion Scorer.
    Coordinates on-device packet telemetry ingestion, deterministic regex recomputation,
    semantic triage teacher evaluation, and PriorityEngine weighted fusion.
    """

    def __init__(
        self,
        regex_engine: RegexEngine | None = None,
        groq_client: GroqClient | None = None,
        priority_engine: PriorityEngine | None = None,
    ):
        self.regex_engine = regex_engine or RegexEngine()
        self.groq_client = groq_client or GroqClient()
        self.priority_engine = priority_engine or PriorityEngine()

    async def score_async(
        self,
        packet: dict[str, Any] | SignedSOSHeader,
        decrypted_text: str | dict[str, Any] | DecryptedSOSPayload,
        corroborating_reports_count: int = 0,
        hours_elapsed: float = 0.0,
        location_risk_modifier: float = 0.0,
        escalation_trend: float = 0.0,
        zone_timestamps: list[Any] | None = None,
        candidates: list[dict[str, Any]] | None = None,
        time_budget_ms: float | None = None,
        correlation_id: str | None = None,
        **kwargs: Any,
    ) -> ScoreResult:
        """
        Asynchronous public triage scoring interface with concurrent sub-step execution,
        response caching, per-stage telemetry, and hard per-report time budget enforcement.
        """
        t_start_pipeline = time.perf_counter()
        corr_id = correlation_id or f"corr_{uuid.uuid4().hex[:12]}"
        skipped_steps: list[str] = []
        time_budget_exceeded = False
        stage_latencies: dict[str, float] = {
            "guard_ms": 0.0,
            "regex_ms": 0.0,
            "normalize_ms": 0.0,
            "embed_ms": 0.0,
            "groq_ms": 0.0,
            "extract_ms": 0.0,
            "correlate_ms": 0.0,
            "escalation_ms": 0.0,
            "false_alarm_ms": 0.0,
            "fusion_ms": 0.0,
            "briefing_ms": 0.0,
        }

        # Load performance & budget config
        perf_cfg = self.priority_engine.config.get("performance", {}) if hasattr(self.priority_engine, "config") else {}
        budget_ms = (
            float(time_budget_ms)
            if time_budget_ms is not None
            else float(perf_cfg.get("per_report_time_budget_ms", 1500.0))
        )
        budget_sec = max(0.1, budget_ms / 1000.0)
        try:
            # 1. Parse & Normalize Header Input
            if isinstance(packet, SignedSOSHeader):
                header = packet
            elif isinstance(packet, dict):
                header = SignedSOSHeader(
                    packet_id=packet.get("packet_id"),
                    device_id=packet.get("device_id"),
                    timestamp=packet.get("timestamp"),
                    hop_count=packet.get("hop_count", 0),
                    severity=packet.get("severity", Severity.WARN),
                    regex_score=int(packet.get("regex_score", 0)),
                    local_model_score=int(packet.get("local_model_score", 0)),
                    confidence=float(packet.get("confidence", 0.5)),
                    category=packet.get("category", Category.OTHER),
                    language=packet.get("language", "en"),
                )
            else:
                header = SignedSOSHeader(severity=Severity.WARN, category=Category.OTHER)

            # 2. Parse & Normalize Payload Input
            if isinstance(decrypted_text, DecryptedSOSPayload):
                payload = decrypted_text
                raw_text = payload.text
            elif isinstance(decrypted_text, dict):
                raw_text = str(decrypted_text.get("text", "")).strip()
                payload = DecryptedSOSPayload(
                    text=raw_text,
                    lat=decrypted_text.get("lat"),
                    lon=decrypted_text.get("lon"),
                    sender_name=decrypted_text.get("sender_name"),
                    victim_count=decrypted_text.get("victim_count", 1),
                    has_medical_need=bool(decrypted_text.get("has_medical_need", False)),
                    is_trapped=bool(decrypted_text.get("is_trapped", False)),
                    metadata=decrypted_text.get("metadata", {}),
                )
            else:
                raw_text = str(decrypted_text).strip()
                payload = DecryptedSOSPayload(text=raw_text)

            # Check Master Response Cache by Decrypted Text Hash
            cached_score = get_cached_response("full_score", raw_text)
            if cached_score is not None and isinstance(cached_score, ScoreResult):
                record_usage(operation="full_score", cached=True)
                hit_dur = round((time.perf_counter() - t_start_pipeline) * 1000.0, 2)
                res_dict = cached_score.model_dump()
                res_dict["reasoning"]["cache_hit"] = True
                res_dict["reasoning"]["correlation_id"] = corr_id
                res_dict["reasoning"]["processing_duration_ms"] = hit_dur
                
                trace = ReportTrace(
                    correlation_id=corr_id,
                    total_duration_ms=hit_dur,
                    stage_latencies_ms=stage_latencies,
                    cache_telemetry={"hit": True, "key_hash": raw_text[:16]},
                    severity=str(res_dict.get("severity", "info")),
                    priority=int(res_dict.get("priority", 50)),
                    category=str(res_dict.get("category", "other")),
                    confidence=float(res_dict.get("confidence", 0.5)),
                    needs_human_review=bool(res_dict.get("needs_human_review", False)),
                )
                record_report_trace(trace)
                return ScoreResult(**res_dict)

            # Groq config
            groq_cfg = self.priority_engine.config.get("groq", {}) if hasattr(self.priority_engine, "config") else {}
            groq_enabled = groq_cfg.get(
                "groq_enabled",
                self.priority_engine.config.get("groq_enabled", True) if hasattr(self.priority_engine, "config") else True
            )
            groq_timeout_ms = groq_cfg.get(
                "groq_timeout_ms",
                self.priority_engine.config.get("groq_timeout_ms", 2000) if hasattr(self.priority_engine, "config") else 2000
            )

            # Step 1: Multilingual Normalization
            t_norm_start = time.perf_counter()
            norm = normalize(raw_text, groq_client=self.groq_client if groq_enabled else None)
            stage_latencies["normalize_ms"] = round((time.perf_counter() - t_norm_start) * 1000.0, 2)

            # ------------------------------------------------------------------
            # Phase 1: Concurrent Sanitization, Regex, Embedding, Extraction, Groq
            # ------------------------------------------------------------------
            def _compute_guard():
                t0 = time.perf_counter()
                res = sanitize(raw_text)
                stage_latencies["guard_ms"] = round((time.perf_counter() - t0) * 1000.0, 2)
                return res

            def _compute_regex():
                t0 = time.perf_counter()
                res = self.regex_engine.evaluate(raw_text)
                stage_latencies["regex_ms"] = round((time.perf_counter() - t0) * 1000.0, 2)
                return res

            def _compute_embed():
                t0 = time.perf_counter()
                vec = embed(norm.canonical_en)
                stage_latencies["embed_ms"] = round((time.perf_counter() - t0) * 1000.0, 2)
                return vec

            def _compute_extract():
                t0 = time.perf_counter()
                res = extract(
                    canonical_en=norm.canonical_en,
                    original=raw_text,
                    groq_client=self.groq_client if (groq_enabled and not time_budget_exceeded) else None,
                )
                stage_latencies["extract_ms"] = round((time.perf_counter() - t0) * 1000.0, 2)
                return res

            def _compute_groq():
                t0 = time.perf_counter()
                if not groq_enabled:
                    stage_latencies["groq_ms"] = 0.0
                    return {
                        "available": False,
                        "groq": "unavailable — rules-only",
                        "groq_status": "unavailable — rules-only",
                        "rationale": "Groq disabled via configuration — fallback to deterministic rule scoring",
                    }
                try:
                    if self.groq_client is not None:
                        if hasattr(self.groq_client, "timeout"):
                            self.groq_client.timeout = float(groq_timeout_ms) / 1000.0
                        raw_groq = self.groq_client.analyze_message(raw_text)
                        stage_latencies["groq_ms"] = round((time.perf_counter() - t0) * 1000.0, 2)
                        if (
                            raw_groq
                            and not str(raw_groq.get("rationale", "")).startswith("Groq API unavailable")
                            and not str(raw_groq.get("rationale", "")).startswith("Groq invocation failed")
                        ):
                            res = dict(raw_groq)
                            res["groq"] = "active"
                            res["groq_status"] = "active"
                            return res
                except Exception as e:
                    logger.warning("Groq semantic triage failed: %s", e)
                stage_latencies["groq_ms"] = round((time.perf_counter() - t0) * 1000.0, 2)
                return {
                    "available": False,
                    "groq": "unavailable — rules-only",
                    "groq_status": "unavailable — rules-only",
                    "rationale": "Groq unavailable — rules-only",
                }

            elapsed_so_far = time.perf_counter() - t_start_pipeline
            phase1_budget = max(0.01, budget_sec - elapsed_so_far)

            try:
                guard_res, regex_eval, embedding_vector, extracted_entities, groq_eval = await asyncio.wait_for(
                    asyncio.gather(
                        asyncio.to_thread(_compute_guard),
                        asyncio.to_thread(_compute_regex),
                        asyncio.to_thread(_compute_embed),
                        asyncio.to_thread(_compute_extract),
                        asyncio.to_thread(_compute_groq),
                    ),
                    timeout=phase1_budget,
                )
            except (asyncio.TimeoutError, TimeoutError):
                time_budget_exceeded = True
                skipped_steps.append("phase1_timeout")
                guard_res = sanitize(raw_text)
                regex_eval = self.regex_engine.evaluate(raw_text)
                embedding_vector = embed(norm.canonical_en)
                extracted_entities = extract(canonical_en=norm.canonical_en, original=raw_text, groq_client=None)
                groq_eval = {
                    "available": False,
                    "groq": "unavailable — rules-only",
                    "groq_status": "unavailable — rules-only",
                    "rationale": "Groq triage skipped due to per-report time budget deadline",
                }

            # ------------------------------------------------------------------
            # Phase 2: Correlation, Escalation, and False Alarm Scoring
            # ------------------------------------------------------------------
            t_corr_start = time.perf_counter()
            if candidates:
                correlation_verdict = correlate(new_embedding=embedding_vector, candidates=candidates)
            else:
                correlation_verdict = CorrelationVerdict(match_id=None, similarity=0.0, is_duplicate=False)
            stage_latencies["correlate_ms"] = round((time.perf_counter() - t_corr_start) * 1000.0, 2)

            t_esc_start = time.perf_counter()
            if zone_timestamps:
                escalation_res = escalation(zone_timestamps)
                effective_escalation = escalation_res.escalation_signal
            else:
                # Clamp to [0.0, 1.0] — EscalationResult enforces le=1.0 at the Pydantic level.
                # Callers may pass raw trend multipliers (e.g. 2.0) that exceed the normalised range.
                effective_escalation = min(1.0, max(0.0, float(escalation_trend)))
                escalation_res = EscalationResult(escalation_signal=effective_escalation)
            stage_latencies["escalation_ms"] = round((time.perf_counter() - t_esc_start) * 1000.0, 2)

            trigger_context = kwargs.get("trigger_type") or (payload.metadata.get("trigger_type") if payload.metadata else None)
            t_fa_start = time.perf_counter()
            fa_result = false_alarm(
                canonical_en=norm.canonical_en,
                entities=extracted_entities,
                trigger_type=trigger_context,
                groq_eval=groq_eval,
                groq_client=self.groq_client if (groq_enabled and not time_budget_exceeded) else None,
            )
            stage_latencies["false_alarm_ms"] = round((time.perf_counter() - t_fa_start) * 1000.0, 2)

            # ------------------------------------------------------------------
            # Phase 3: Priority Fusion
            # ------------------------------------------------------------------
            t_fus_start = time.perf_counter()
            fusion = self.priority_engine.calculate_priority(
                header=header,
                payload=payload,
                regex_eval=regex_eval,
                groq_eval=groq_eval,
                corroborating_reports_count=corroborating_reports_count,
                hours_elapsed=hours_elapsed,
                location_risk_modifier=location_risk_modifier,
                escalation_trend=effective_escalation,
                **kwargs,
            )
            stage_latencies["fusion_ms"] = round((time.perf_counter() - t_fus_start) * 1000.0, 2)

            raw_priority = fusion.get("priority_score", 50.0)
            int_priority = max(0, min(100, int(round(float(raw_priority)))))

            # ------------------------------------------------------------------
            # Phase 4: Briefing Synthesis
            # ------------------------------------------------------------------
            elapsed_so_far = time.perf_counter() - t_start_pipeline
            phase4_budget = max(0.05, budget_sec - elapsed_so_far)

            def _compute_brief():
                t0 = time.perf_counter()
                res = brief(
                    entities=extracted_entities,
                    severity=fusion["severity"],
                    priority=int_priority,
                    canonical_en=norm.canonical_en,
                    groq_client=self.groq_client if (groq_enabled and not time_budget_exceeded) else None,
                )
                stage_latencies["briefing_ms"] = round((time.perf_counter() - t0) * 1000.0, 2)
                return res

            try:
                incident_briefing = await asyncio.wait_for(
                    asyncio.to_thread(_compute_brief),
                    timeout=phase4_budget,
                )
            except (asyncio.TimeoutError, TimeoutError):
                time_budget_exceeded = True
                skipped_steps.append("phase4_briefing_timeout")
                incident_briefing = brief(
                    entities=extracted_entities,
                    severity=fusion["severity"],
                    priority=int_priority,
                    canonical_en=norm.canonical_en,
                    groq_client=None,
                )

            # ------------------------------------------------------------------
            # Phase 5: Format Auditable Reasoning Breakdown & Assemble ScoreResult
            # ------------------------------------------------------------------
            reasoning_data = fusion.get("reasoning")
            if hasattr(reasoning_data, "model_dump"):
                reasoning_dict = reasoning_data.model_dump()
            elif isinstance(reasoning_data, dict):
                reasoning_dict = reasoning_data
            else:
                reasoning_dict = {
                    "regex_score": regex_eval.get("score", 0),
                    "matched_rules": regex_eval.get("matched_rules", []),
                    "groq_rationale": groq_eval.get("rationale", ""),
                    "groq": groq_eval.get("groq", "unavailable — rules-only"),
                }

            if not reasoning_dict.get("groq"):
                reasoning_dict["groq"] = groq_eval.get("groq", "unavailable — rules-only")

            # Attach Prompt Injection Guard Telemetry
            is_injection_suspected = guard_res.injection_suspected or bool(groq_eval.get("injection_suspected", False))
            combined_injection_reasons = list(dict.fromkeys(guard_res.injection_reasons + list(groq_eval.get("injection_reasons", []))))

            reasoning_dict["injection_suspected"] = is_injection_suspected
            reasoning_dict["injection_reasons"] = combined_injection_reasons
            reasoning_dict["extracted_entities_detail"] = extracted_entities.to_dict()

            # Attach False Alarm & Correlation Telemetry
            reasoning_dict["false_alarm_likelihood"] = fa_result.false_alarm_likelihood
            reasoning_dict["false_alarm_reasons"] = fa_result.reasons
            reasoning_dict["is_likely_drill"] = fa_result.is_likely_drill
            reasoning_dict["correlation"] = correlation_verdict.to_dict()
            reasoning_dict["escalation"] = escalation_res.to_dict()

            # Performance, Observability & Time Budget Telemetry
            total_duration_ms = round((time.perf_counter() - t_start_pipeline) * 1000.0, 2)
            reasoning_dict["processing_duration_ms"] = total_duration_ms
            reasoning_dict["correlation_id"] = corr_id
            reasoning_dict["stage_latencies_ms"] = stage_latencies
            reasoning_dict["time_budget_ms"] = budget_ms
            reasoning_dict["time_budget_exceeded"] = time_budget_exceeded
            reasoning_dict["skipped_steps"] = skipped_steps
            reasoning_dict["cache_hit"] = False

            explanation_bullets = reasoning_dict.get("explanation_bullets", [])
            if is_injection_suspected and not any("injection" in str(b).lower() for b in explanation_bullets):
                explanation_bullets.append("⚠️ Prompt injection / override pattern detected and neutralized")
            if fa_result.is_likely_drill and not any("test" in str(b).lower() or "drill" in str(b).lower() for b in explanation_bullets):
                explanation_bullets.append(f"ℹ️ Potential test/drill pattern detected ({int(fa_result.false_alarm_likelihood * 100)}% likelihood)")
            if correlation_verdict.is_duplicate:
                explanation_bullets.append(f"🔗 Corroborated by existing incident cluster (match: {correlation_verdict.match_id})")
            if time_budget_exceeded:
                explanation_bullets.append(f"⚡ Time budget ({int(budget_ms)}ms) honored — returned partial intelligence")
            reasoning_dict["explanation_bullets"] = explanation_bullets
            reasoning_dict["briefing"] = incident_briefing.to_dict()

            score_res = ScoreResult(
                schema_version="2.0.0",
                severity=fusion["severity"],
                priority=int_priority,
                category=fusion["category"],
                confidence=round(float(fusion.get("confidence", 0.5)), 4),
                reasoning=reasoning_dict,
                entities=extracted_entities,
                briefing=incident_briefing,
                recommended_resources=incident_briefing.recommended_resources if incident_briefing else [],
                correlation=correlation_verdict,
                embedding=embedding_vector,
                escalation_signal=escalation_res.escalation_signal,
                false_alarm_likelihood=fa_result.false_alarm_likelihood,
                false_alarm_reasons=fa_result.reasons,
                needs_human_review=bool(fusion.get("needs_human_review", False)),
                injection_suspected=is_injection_suspected,
                injection_reasons=combined_injection_reasons,
                correlation_id=corr_id,
            )

            # Store in response cache
            cache_response("full_score", raw_text, score_res)

            # Record Observability Trace
            trace = ReportTrace(
                correlation_id=corr_id,
                total_duration_ms=total_duration_ms,
                stage_latencies_ms=stage_latencies,
                groq_telemetry={
                    "called": groq_eval.get("available", False),
                    "cached": groq_eval.get("cached", False),
                    "status": groq_eval.get("groq_status", "active" if groq_eval.get("available") else "unavailable"),
                    "prompt_tokens": groq_eval.get("prompt_tokens", 0),
                    "completion_tokens": groq_eval.get("completion_tokens", 0),
                    "total_tokens": groq_eval.get("total_tokens", 0),
                    "estimated_cost_usd": groq_eval.get("estimated_cost_usd", 0.0),
                    "model": groq_eval.get("model", "llama-3.3-70b-versatile"),
                },
                fusion_telemetry={
                    "inputs": {
                        "regex_score": regex_eval.get("score", 0),
                        "local_model_score": header.local_model_score,
                        "confidence": header.confidence,
                        "corroborating_reports_count": corroborating_reports_count,
                    },
                    "outputs": {
                        "severity": str(fusion.get("severity", "info")),
                        "priority": int_priority,
                        "category": str(fusion.get("category", "other")),
                        "confidence": float(fusion.get("confidence", 0.5)),
                        "needs_human_review": bool(fusion.get("needs_human_review", False)),
                    },
                },
                cache_telemetry={
                    "hit": False,
                    "key_hash": raw_text[:16],
                },
                security_telemetry={
                    "injection_suspected": is_injection_suspected,
                    "injection_reasons": combined_injection_reasons,
                },
                false_alarm_telemetry={
                    "likelihood": fa_result.false_alarm_likelihood,
                    "reasons": fa_result.reasons,
                },
                severity=str(score_res.severity.value if hasattr(score_res.severity, "value") else score_res.severity),
                priority=int_priority,
                category=str(score_res.category.value if hasattr(score_res.category, "value") else score_res.category),
                confidence=score_res.confidence,
                needs_human_review=score_res.needs_human_review,
                time_budget_exceeded=time_budget_exceeded,
                skipped_steps=skipped_steps,
            )
            record_report_trace(trace)

            return score_res

        except Exception as e:
            # Fallback Safety Net: Ensure Harshit's pipeline is NEVER disrupted by unhandled exceptions
            logger.error("Unexpected error in scorer triage pipeline (applying safe fallback): %s", e, exc_info=True)
            guard_fallback = sanitize(str(decrypted_text))
            fallback_regex = self.regex_engine.evaluate(str(decrypted_text)) if self.regex_engine else {"score": 50, "category": Category.OTHER, "matched_rules": []}
            fallback_score = int(fallback_regex.get("score", 50))
            fallback_sev = Severity.CRITICAL if fallback_score >= 75 else (Severity.WARN if fallback_score >= 35 else Severity.INFO)
            fallback_entities = extract(str(decrypted_text), str(decrypted_text), groq_client=None)
            fallback_briefing = brief(
                entities=fallback_entities,
                severity=fallback_sev,
                priority=fallback_score,
                canonical_en=str(decrypted_text),
                groq_client=None,
            )

            header_obj = locals().get("header")
            fallback_bullets = [
                f"Emergency triage calculated via safe fallback mode (error: {e!s})",
                f"Server deterministic regex score: {fallback_score}",
            ]
            if guard_fallback.injection_suspected:
                fallback_bullets.append("⚠️ Prompt injection / override pattern detected and neutralized")

            fallback_res = ScoreResult(
                schema_version="2.0.0",
                severity=fallback_sev,
                priority=fallback_score,
                category=fallback_regex.get("category", Category.OTHER),
                confidence=0.5,
                entities=fallback_entities,
                briefing=fallback_briefing,
                recommended_resources=fallback_briefing.recommended_resources,
                correlation=CorrelationVerdict(match_id=None, similarity=0.0, is_duplicate=False),
                embedding=None,
                escalation_signal=0.0,
                false_alarm_likelihood=0.0,
                false_alarm_reasons=[],
                needs_human_review=True,
                injection_suspected=guard_fallback.injection_suspected,
                injection_reasons=guard_fallback.injection_reasons,
                correlation_id=locals().get("corr_id", f"corr_{uuid.uuid4().hex[:12]}"),
                reasoning={
                    "fallback_mode": True,
                    "error": str(e),
                    "matched_rules": fallback_regex.get("matched_rules", []),
                    "origin_severity": str(header_obj.severity) if header_obj else None,
                    "origin_regex_score": header_obj.regex_score if header_obj else None,
                    "origin_local_model_score": header_obj.local_model_score if header_obj else None,
                    "origin_confidence": header_obj.confidence if header_obj else None,
                    "origin_category": str(header_obj.category) if header_obj else None,
                    "server_regex_score": fallback_score,
                    "disagreement_detected": False,
                    "disagreement_reason": None,
                    "disagreement_policy_applied": None,
                    "needs_human_review": True,
                    "abstention_reason": f"Fallback mode active due to exception ({e!s})",
                    "groq": "unavailable — rules-only",
                    "injection_suspected": guard_fallback.injection_suspected,
                    "injection_reasons": guard_fallback.injection_reasons,
                    "explanation_bullets": fallback_bullets,
                    "factors": {
                        "severity": 0.0,
                        "regex": float(fallback_score),
                        "local_model": 0.0,
                        "groq": 0.0,
                        "corroboration": 0.0,
                        "vulnerability": 0.0,
                        "location": 0.0,
                        "trend": 0.0,
                        "decay": 1.0,
                    },
                },
            )

            fallback_trace = ReportTrace(
                correlation_id=locals().get("corr_id", f"corr_{uuid.uuid4().hex[:12]}"),
                total_duration_ms=round((time.perf_counter() - locals().get("t_start_pipeline", time.perf_counter())) * 1000.0, 2),
                stage_latencies_ms=locals().get("stage_latencies", {}),
                severity=fallback_sev.value,
                priority=fallback_score,
                category=fallback_regex.get("category", Category.OTHER).value if hasattr(fallback_regex.get("category", Category.OTHER), "value") else str(fallback_regex.get("category", Category.OTHER)),
                confidence=0.5,
                needs_human_review=True,
                time_budget_exceeded=locals().get("time_budget_exceeded", False),
                skipped_steps=locals().get("skipped_steps", ["exception_fallback"]),
            )
            record_report_trace(fallback_trace)

            return fallback_res

    def score(
        self,
        packet: dict[str, Any] | SignedSOSHeader,
        decrypted_text: str | dict[str, Any] | DecryptedSOSPayload,
        corroborating_reports_count: int = 0,
        hours_elapsed: float = 0.0,
        location_risk_modifier: float = 0.0,
        escalation_trend: float = 0.0,
        zone_timestamps: list[Any] | None = None,
        candidates: list[dict[str, Any]] | None = None,
        time_budget_ms: float | None = None,
        correlation_id: str | None = None,
        **kwargs: Any,
    ) -> ScoreResult:
        """
        Synchronous public triage scoring interface.
        Executes concurrent async pipeline under the hood.
        """
        return _run_sync(
            self.score_async(
                packet=packet,
                decrypted_text=decrypted_text,
                corroborating_reports_count=corroborating_reports_count,
                hours_elapsed=hours_elapsed,
                location_risk_modifier=location_risk_modifier,
                escalation_trend=escalation_trend,
                zone_timestamps=zone_timestamps,
                candidates=candidates,
                time_budget_ms=time_budget_ms,
                correlation_id=correlation_id,
                **kwargs,
            )
        )


# Global default instance
_default_scorer = Scorer()


async def score_async(
    packet: dict[str, Any] | SignedSOSHeader,
    decrypted_text: str | dict[str, Any] | DecryptedSOSPayload,
    corroborating_reports_count: int = 0,
    hours_elapsed: float = 0.0,
    location_risk_modifier: float = 0.0,
    escalation_trend: float = 0.0,
    zone_timestamps: list[Any] | None = None,
    candidates: list[dict[str, Any]] | None = None,
    time_budget_ms: float | None = None,
    correlation_id: str | None = None,
    **kwargs: Any,
) -> ScoreResult:
    """
    Asynchronous public seam entry point called by Harshit's ingestion pipeline.
    """
    return await _default_scorer.score_async(
        packet=packet,
        decrypted_text=decrypted_text,
        corroborating_reports_count=corroborating_reports_count,
        hours_elapsed=hours_elapsed,
        location_risk_modifier=location_risk_modifier,
        escalation_trend=escalation_trend,
        zone_timestamps=zone_timestamps,
        candidates=candidates,
        time_budget_ms=time_budget_ms,
        correlation_id=correlation_id,
        **kwargs,
    )


def score(
    packet: dict[str, Any] | SignedSOSHeader,
    decrypted_text: str | dict[str, Any] | DecryptedSOSPayload,
    corroborating_reports_count: int = 0,
    hours_elapsed: float = 0.0,
    location_risk_modifier: float = 0.0,
    escalation_trend: float = 0.0,
    zone_timestamps: list[Any] | None = None,
    candidates: list[dict[str, Any]] | None = None,
    time_budget_ms: float | None = None,
    correlation_id: str | None = None,
    **kwargs: Any,
) -> ScoreResult:
    """
    Synchronous public seam entry point called by Harshit's ingestion pipeline.
    """
    return _default_scorer.score(
        packet=packet,
        decrypted_text=decrypted_text,
        corroborating_reports_count=corroborating_reports_count,
        hours_elapsed=hours_elapsed,
        location_risk_modifier=location_risk_modifier,
        escalation_trend=escalation_trend,
        zone_timestamps=zone_timestamps,
        candidates=candidates,
        time_budget_ms=time_budget_ms,
        correlation_id=correlation_id,
        **kwargs,
    )
