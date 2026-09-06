"""
Project Pukar - Intelligence Layer Structured Observability & Telemetry
======================================================================

Provides structured per-stage execution tracing, secret-safe logging, and real-time
health analytics (`intelligence_health()`) across the ML pipeline.

Key Capabilities:
1. End-to-end trace collection per report with a unique correlation ID.
2. Per-stage latency accounting: guard, regex, normalization, Groq, extraction,
   false-alarm, priority fusion, and briefing synthesis.
3. Central Groq token, cost, and availability tracking.
4. Response cache hit/miss tracking.
5. Strict secret redaction: zero API keys, auth tokens, or secrets leaked into logs.
6. `intelligence_health()`: Live operational telemetry queryable as simple JSON
   (p50/p95 stage latencies, Groq availability %, cache hit rate, cost/hour, abstention rate).
"""

from __future__ import annotations

import copy
import json
import logging
import math
import os
import threading
import time
import uuid
from collections import deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from .cache import get_cache_stats
from .meter import get_usage_summary

logger = logging.getLogger("pukar.ml.observability")


# ==============================================================================
# Configuration & Secret Redaction
# ==============================================================================

DEFAULT_REDACT_KEYS = {
    "api_key",
    "groq_api_key",
    "secret",
    "token",
    "authorization",
    "password",
    "private_key",
    "signature",
    "aes_key",
    "auth_token",
    "bearer",
}


def _resolve_observability_config() -> dict[str, Any]:
    """Loads externalized observability settings from YAML."""
    candidates = [
        Path(__file__).parent / "configs" / "observability.yaml",
        Path(__file__).resolve().parents[4] / "ml" / "configs" / "observability.yaml",
        Path("ml/configs/observability.yaml"),
    ]
    for c in candidates:
        if c.exists():
            try:
                with open(c, encoding="utf-8") as f:
                    cfg = yaml.safe_load(f) or {}
                    return cfg.get("observability", {})
            except Exception as e:
                logger.warning(f"Failed to read observability config from {c}: {e}")
    return {}


def redact_secrets(data: Any, redact_keys: set[str] | None = None) -> Any:
    """
    Recursively scrubs sensitive keys (API keys, secrets, tokens) from dictionaries,
    lists, or objects before serialization to logs.
    """
    keys_to_redact = redact_keys or DEFAULT_REDACT_KEYS

    if isinstance(data, dict):
        cleaned = {}
        for k, v in data.items():
            k_lower = str(k).lower().strip()
            if any(target in k_lower for target in keys_to_redact):
                cleaned[k] = "[REDACTED]"
            else:
                cleaned[k] = redact_secrets(v, keys_to_redact)
        return cleaned
    elif isinstance(data, list):
        return [redact_secrets(item, keys_to_redact) for item in data]
    elif isinstance(data, tuple):
        return tuple(redact_secrets(item, keys_to_redact) for item in data)
    return data


# ==============================================================================
# Per-Report Structured Trace Model
# ==============================================================================

@dataclass
class ReportTrace:
    """
    Complete telemetry trace capturing granular per-stage metrics for a scored SOS report.
    """
    correlation_id: str = field(default_factory=lambda: f"corr_{uuid.uuid4().hex[:12]}")
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    total_duration_ms: float = 0.0

    # Stage Latencies (ms)
    stage_latencies_ms: dict[str, float] = field(
        default_factory=lambda: {
            "guard_ms": 0.0,
            "regex_ms": 0.0,
            "normalize_ms": 0.0,
            "groq_ms": 0.0,
            "extract_ms": 0.0,
            "false_alarm_ms": 0.0,
            "fusion_ms": 0.0,
            "briefing_ms": 0.0,
            "embed_ms": 0.0,
        }
    )

    # Groq API Telemetry
    groq_telemetry: dict[str, Any] = field(
        default_factory=lambda: {
            "called": False,
            "cached": False,
            "status": "skipped",
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "estimated_cost_usd": 0.0,
            "model": "llama-3.3-70b-versatile",
        }
    )

    # Priority Fusion Inputs & Outputs
    fusion_telemetry: dict[str, Any] = field(
        default_factory=lambda: {
            "inputs": {},
            "outputs": {},
        }
    )

    # Cache Telemetry
    cache_telemetry: dict[str, Any] = field(
        default_factory=lambda: {
            "hit": False,
            "key_hash": "",
        }
    )

    # Security & Guard Telemetry
    security_telemetry: dict[str, Any] = field(
        default_factory=lambda: {
            "injection_suspected": False,
            "injection_reasons": [],
        }
    )

    # False-Alarm Telemetry
    false_alarm_telemetry: dict[str, Any] = field(
        default_factory=lambda: {
            "likelihood": 0.0,
            "reasons": [],
        }
    )

    # Dispatch Intel Summary
    severity: str = "info"
    priority: int = 50
    category: str = "other"
    confidence: float = 0.5
    needs_human_review: bool = False
    time_budget_exceeded: bool = False
    skipped_steps: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Converts trace to dictionary with secret redaction."""
        raw = asdict(self)
        return redact_secrets(raw)

    def to_json(self) -> str:
        """Serializes trace to JSON string."""
        return json.dumps(self.to_dict(), default=str)


# ==============================================================================
# Observability Manager & Health Engine (Thread-Safe Singleton)
# ==============================================================================

class ObservabilityManager:
    """
    Thread-safe observability manager tracking live report traces, SLA latencies,
    cost telemetry, and system-wide health aggregates.
    """

    _instance: ObservabilityManager | None = None
    _lock = threading.Lock()

    def __init__(self, window_size: int = 1000):
        self.config = _resolve_observability_config()
        self.window_size = int(self.config.get("window_size", window_size))
        self.log_structured_json = bool(self.config.get("log_structured_json", True))

        self._traces: deque[ReportTrace] = deque(maxlen=self.window_size)
        self._trace_lock = threading.Lock()
        self._start_time = time.time()

    @classmethod
    def get_instance(cls) -> ObservabilityManager:
        """Thread-safe singleton accessor."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def record_trace(self, trace: ReportTrace) -> None:
        """
        Records a completed report trace and logs structured JSON trace event.
        """
        with self._trace_lock:
            self._traces.append(trace)

        # Structured JSON Log
        if self.log_structured_json:
            try:
                trace_dict = trace.to_dict()
                log_entry = {
                    "event": "report_scored",
                    "correlation_id": trace.correlation_id,
                    "timestamp": trace.timestamp,
                    "duration_ms": trace.total_duration_ms,
                    "severity": trace.severity,
                    "priority": trace.priority,
                    "category": trace.category,
                    "confidence": trace.confidence,
                    "needs_human_review": trace.needs_human_review,
                    "cache_hit": trace.cache_telemetry.get("hit", False),
                    "injection_suspected": trace.security_telemetry.get("injection_suspected", False),
                    "stages_ms": trace.stage_latencies_ms,
                    "groq": trace.groq_telemetry,
                }
                logger.info(json.dumps(log_entry, default=str))
            except Exception as e:
                logger.warning(f"Failed to emit structured trace log: {e}")

    def get_recent_traces(self, limit: int = 50) -> list[dict[str, Any]]:
        """Returns the most recent N traces."""
        with self._trace_lock:
            traces_slice = list(self._traces)[-limit:]
        return [t.to_dict() for t in reversed(traces_slice)]

    def reset_metrics(self) -> None:
        """Clears all in-memory traces and resets baseline counters."""
        with self._trace_lock:
            self._traces.clear()
            self._start_time = time.time()

    def compute_health_summary(self) -> dict[str, Any]:
        """
        Computes live, comprehensive operational health telemetry.
        Returns JSON-serializable dictionary.
        """
        with self._trace_lock:
            traces = list(self._traces)

        total_reports = len(traces)
        uptime_seconds = max(1.0, time.time() - self._start_time)
        uptime_hours = uptime_seconds / 3600.0

        # Base default for cold start
        if total_reports == 0:
            usage_summary = get_usage_summary()
            cache_stats = get_cache_stats()
            return {
                "status": "healthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "uptime_seconds": round(uptime_seconds, 1),
                "total_reports_processed": 0,
                "latency_telemetry_ms": {
                    "p50_total_ms": 0.0,
                    "p95_total_ms": 0.0,
                    "avg_total_ms": 0.0,
                    "stages": {},
                },
                "groq_health": {
                    "availability_pct": 100.0,
                    "total_calls": usage_summary["total_calls"],
                    "successful_calls": usage_summary["successful_calls"],
                    "failed_calls": usage_summary["failed_calls"],
                    "cached_calls": usage_summary["cached_calls"],
                    "total_tokens": usage_summary["token_usage"]["total_tokens"],
                    "total_cost_usd": usage_summary["cost_telemetry"]["total_estimated_cost_usd"],
                    "estimated_cost_per_hour_usd": 0.0,
                },
                "cache_health": {
                    "hit_rate_pct": cache_stats["hit_rate_pct"],
                    "hits": cache_stats["hits"],
                    "misses": cache_stats["misses"],
                    "size": cache_stats["size"],
                },
                "triage_metrics": {
                    "abstention_rate_pct": 0.0,
                    "injection_rate_pct": 0.0,
                    "false_alarm_rate_pct": 0.0,
                    "time_budget_exceeded_rate_pct": 0.0,
                    "severity_distribution": {"critical": 0, "warn": 0, "info": 0},
                    "category_distribution": {"rescue": 0, "medical": 0, "fire": 0, "shelter": 0, "other": 0},
                },
            }

        # 1. Latency Percentiles
        total_lats = sorted(t.total_duration_ms for t in traces)
        p50_total = _percentile(total_lats, 0.50)
        p95_total = _percentile(total_lats, 0.95)
        avg_total = sum(total_lats) / total_reports

        # Granular Stage Latencies
        stage_names = ["guard_ms", "regex_ms", "normalize_ms", "groq_ms", "extract_ms", "false_alarm_ms", "fusion_ms", "briefing_ms"]
        stage_metrics: dict[str, dict[str, float]] = {}
        for stage in stage_names:
            vals = sorted(t.stage_latencies_ms.get(stage, 0.0) for t in traces)
            stage_metrics[stage] = {
                "p50_ms": round(_percentile(vals, 0.50), 2),
                "p95_ms": round(_percentile(vals, 0.95), 2),
                "avg_ms": round(sum(vals) / total_reports, 2),
            }

        # 2. Groq Usage & Availability
        usage = get_usage_summary()
        total_calls = usage["total_calls"]
        succ_calls = usage["successful_calls"]
        fail_calls = usage["failed_calls"]
        cached_calls = usage["cached_calls"]
        total_cost = usage["cost_telemetry"]["total_estimated_cost_usd"]

        groq_availability = (succ_calls / (succ_calls + fail_calls) * 100.0) if (succ_calls + fail_calls) > 0 else 100.0
        cost_per_hour = round(total_cost / uptime_hours, 5)

        # 3. Cache Health
        cache_stats = get_cache_stats()

        # 4. Triage & Operational Ratios
        abstentions = sum(1 for t in traces if t.needs_human_review)
        injections = sum(1 for t in traces if t.security_telemetry.get("injection_suspected", False))
        false_alarms = sum(1 for t in traces if t.false_alarm_telemetry.get("likelihood", 0.0) >= 0.4)
        budget_exceeded = sum(1 for t in traces if t.time_budget_exceeded)

        sev_dist: dict[str, int] = {"critical": 0, "warn": 0, "info": 0}
        cat_dist: dict[str, int] = {"rescue": 0, "medical": 0, "fire": 0, "shelter": 0, "other": 0}

        for t in traces:
            s = str(t.severity).lower()
            if s in sev_dist:
                sev_dist[s] += 1
            c = str(t.category).lower()
            if c in cat_dist:
                cat_dist[c] += 1

        # Health Status Determination
        status = "healthy"
        if groq_availability < 70.0 or p95_total > 2000.0:
            status = "degraded"
        if groq_availability < 30.0 and p95_total > 5000.0:
            status = "down"

        return {
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime_seconds": round(uptime_seconds, 1),
            "total_reports_processed": total_reports,
            "latency_telemetry_ms": {
                "p50_total_ms": round(p50_total, 2),
                "p95_total_ms": round(p95_total, 2),
                "avg_total_ms": round(avg_total, 2),
                "stages": stage_metrics,
            },
            "groq_health": {
                "availability_pct": round(groq_availability, 1),
                "total_calls": total_calls,
                "successful_calls": succ_calls,
                "failed_calls": fail_calls,
                "cached_calls": cached_calls,
                "total_tokens": usage["token_usage"]["total_tokens"],
                "total_cost_usd": total_cost,
                "estimated_cost_per_hour_usd": cost_per_hour,
            },
            "cache_health": {
                "hit_rate_pct": cache_stats["hit_rate_pct"],
                "hits": cache_stats["hits"],
                "misses": cache_stats["misses"],
                "size": cache_stats["size"],
            },
            "triage_metrics": {
                "abstention_rate_pct": round((abstentions / total_reports) * 100.0, 1),
                "injection_rate_pct": round((injections / total_reports) * 100.0, 1),
                "false_alarm_rate_pct": round((false_alarms / total_reports) * 100.0, 1),
                "time_budget_exceeded_rate_pct": round((budget_exceeded / total_reports) * 100.0, 1),
                "severity_distribution": sev_dist,
                "category_distribution": cat_dist,
            },
        }


def _percentile(sorted_list: list[float], p: float) -> float:
    """Calculates percentile from a sorted list of numbers."""
    if not sorted_list:
        return 0.0
    k = (len(sorted_list) - 1) * p
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_list[int(k)]
    d0 = sorted_list[int(f)] * (c - k)
    d1 = sorted_list[int(c)] * (k - f)
    return d0 + d1


# ==============================================================================
# Public Callable Seam: `intelligence_health()`
# ==============================================================================

def intelligence_health() -> dict[str, Any]:
    """
    Public intelligence health summary endpoint.
    Returns real-time aggregated metrics (p50/p95 stage latencies, Groq availability %,
    cache hit rate, cost/hour, and abstention rate).
    """
    return ObservabilityManager.get_instance().compute_health_summary()


def record_report_trace(trace: ReportTrace) -> None:
    """Records a per-report execution trace into the central observability engine."""
    ObservabilityManager.get_instance().record_trace(trace)


def get_recent_traces(limit: int = 50) -> list[dict[str, Any]]:
    """Retrieves recent report traces with secret redaction."""
    return ObservabilityManager.get_instance().get_recent_traces(limit=limit)


def reset_observability_metrics() -> None:
    """Resets all telemetry counters, trace buffers, and usage metrics."""
    ObservabilityManager.get_instance().reset_metrics()
