"""
Project Pukar - Central Groq Usage, Cost, and Latency Meter
===========================================================
Tracks tokens, latency, call counts, cache hits, and estimated USD cloud API costs.
Provides auditable usage telemetry across all backend ML intelligence components.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any

logger = logging.getLogger("pukar.ml.meter")

# Default Pricing: Llama-3.3 70b / 3.1 8b on Groq Cloud
# Rates per 1,000,000 tokens (USD)
DEFAULT_PROMPT_COST_PER_1M = 0.59      # $0.59 per 1M prompt tokens (~$0.00000059/token)
DEFAULT_COMPLETION_COST_PER_1M = 0.79  # $0.79 per 1M completion tokens (~$0.00000079/token)


class GroqUsageMeter:
    """
    Thread-safe central usage, cost, and latency meter.
    Aggregates metrics across all Groq LLM invocations and cache hits.
    """

    def __init__(
        self,
        prompt_cost_per_1m: float = DEFAULT_PROMPT_COST_PER_1M,
        completion_cost_per_1m: float = DEFAULT_COMPLETION_COST_PER_1M,
    ):
        self._lock = threading.Lock()
        self.prompt_cost_per_1m = prompt_cost_per_1m
        self.completion_cost_per_1m = completion_cost_per_1m
        self.reset()

    def reset(self) -> None:
        """Resets all aggregated usage metrics to zero."""
        with self._lock:
            self.total_calls: int = 0
            self.successful_calls: int = 0
            self.failed_calls: int = 0
            self.cached_calls: int = 0
            self.prompt_tokens: int = 0
            self.completion_tokens: int = 0
            self.total_tokens: int = 0
            self.total_latency_ms: float = 0.0
            self.min_latency_ms: float = float("inf")
            self.max_latency_ms: float = 0.0
            self.by_operation: dict[str, dict[str, Any]] = {}
            self.created_at: float = time.time()

    def record_call(
        self,
        operation: str = "triage",
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        latency_ms: float = 0.0,
        cached: bool = False,
        error: bool = False,
        model: str = "llama-3.3-70b-versatile",
    ) -> None:
        """
        Records an API invocation, token usage, and latency.
        """
        with self._lock:
            self.total_calls += 1
            if cached:
                self.cached_calls += 1
            elif error:
                self.failed_calls += 1
            else:
                self.successful_calls += 1

            if not cached:
                p_tok = max(0, int(prompt_tokens))
                c_tok = max(0, int(completion_tokens))
                tot_tok = p_tok + c_tok

                self.prompt_tokens += p_tok
                self.completion_tokens += c_tok
                self.total_tokens += tot_tok

                lat = max(0.0, float(latency_ms))
                self.total_latency_ms += lat
                if lat < self.min_latency_ms:
                    self.min_latency_ms = lat
                if lat > self.max_latency_ms:
                    self.max_latency_ms = lat

            # Record per-operation breakdown
            op_dict = self.by_operation.setdefault(
                operation,
                {
                    "calls": 0,
                    "cached": 0,
                    "errors": 0,
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                    "latency_ms": 0.0,
                    "estimated_cost_usd": 0.0,
                },
            )
            op_dict["calls"] += 1
            if cached:
                op_dict["cached"] += 1
            elif error:
                op_dict["errors"] += 1
            else:
                op_dict["prompt_tokens"] += max(0, int(prompt_tokens))
                op_dict["completion_tokens"] += max(0, int(completion_tokens))
                op_dict["total_tokens"] += max(0, int(prompt_tokens)) + max(0, int(completion_tokens))
                op_dict["latency_ms"] += max(0.0, float(latency_ms))

                cost = (
                    (max(0, int(prompt_tokens)) / 1_000_000.0) * self.prompt_cost_per_1m
                    + (max(0, int(completion_tokens)) / 1_000_000.0) * self.completion_cost_per_1m
                )
                op_dict["estimated_cost_usd"] += round(cost, 6)

    def get_summary(self) -> dict[str, Any]:
        """
        Returns a comprehensive usage, cost, and latency summary dictionary.
        """
        with self._lock:
            # Compute estimated total cost in USD
            prompt_cost = (self.prompt_tokens / 1_000_000.0) * self.prompt_cost_per_1m
            completion_cost = (self.completion_tokens / 1_000_000.0) * self.completion_cost_per_1m
            total_cost_usd = round(prompt_cost + completion_cost, 6)

            uncached_calls = self.successful_calls + self.failed_calls
            avg_latency_ms = (
                round(self.total_latency_ms / uncached_calls, 2)
                if uncached_calls > 0
                else 0.0
            )
            min_lat = self.min_latency_ms if self.min_latency_ms != float("inf") else 0.0

            cache_hit_rate = (
                round((self.cached_calls / self.total_calls) * 100.0, 2)
                if self.total_calls > 0
                else 0.0
            )

            return {
                "total_calls": self.total_calls,
                "successful_calls": self.successful_calls,
                "cached_calls": self.cached_calls,
                "failed_calls": self.failed_calls,
                "cache_hit_rate_pct": cache_hit_rate,
                "token_usage": {
                    "prompt_tokens": self.prompt_tokens,
                    "completion_tokens": self.completion_tokens,
                    "total_tokens": self.total_tokens,
                },
                "cost_telemetry": {
                    "prompt_cost_usd": round(prompt_cost, 6),
                    "completion_cost_usd": round(completion_cost, 6),
                    "total_estimated_cost_usd": total_cost_usd,
                    "currency": "USD",
                },
                "latency_telemetry_ms": {
                    "avg_ms": avg_latency_ms,
                    "min_ms": round(min_lat, 2),
                    "max_ms": round(self.max_latency_ms, 2),
                    "total_ms": round(self.total_latency_ms, 2),
                },
                "by_operation": dict(self.by_operation),
            }


# Global singleton instance
_global_usage_meter = GroqUsageMeter()


def get_usage_meter() -> GroqUsageMeter:
    """Returns the global usage meter singleton."""
    return _global_usage_meter


def get_usage_summary() -> dict[str, Any]:
    """Returns the aggregated usage, token, and cost telemetry."""
    return _global_usage_meter.get_summary()


def record_usage(
    operation: str = "triage",
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    latency_ms: float = 0.0,
    cached: bool = False,
    error: bool = False,
    model: str = "llama-3.3-70b-versatile",
) -> None:
    """Records a single usage event into the central meter."""
    _global_usage_meter.record_call(
        operation=operation,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        latency_ms=latency_ms,
        cached=cached,
        error=error,
        model=model,
    )


def reset_usage_meter() -> None:
    """Resets the global usage meter."""
    _global_usage_meter.reset()
