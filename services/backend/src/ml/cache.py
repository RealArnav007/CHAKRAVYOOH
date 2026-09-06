"""
Project Pukar - Response Cache Keyed by Text Hash with TTL
==========================================================
Caches expensive Groq semantic inferences, multilingual normalizations,
structured entity extractions, and briefings.

In disaster events, duplicate / identical SOS messages frequently arrive across
mesh hops. Caching eliminates redundant LLM calls, lowering latency to < 1ms
and slashing Groq cloud API consumption.
"""

from __future__ import annotations

import hashlib
import logging
import threading
import time
from typing import Any

logger = logging.getLogger("pukar.ml.cache")

# Default TTL: 5 minutes (300 seconds)
DEFAULT_CACHE_TTL_SECONDS = 300.0
DEFAULT_MAX_CACHE_ENTRIES = 2000


class TextHashResponseCache:
    """
    Thread-safe in-memory cache partitioned by namespace and keyed by SHA-256 text hash.
    Enforces TTL expiration and capacity bounds.
    """

    def __init__(
        self,
        default_ttl: float = DEFAULT_CACHE_TTL_SECONDS,
        max_entries: int = DEFAULT_MAX_CACHE_ENTRIES,
    ):
        self.default_ttl = default_ttl
        self.max_entries = max_entries
        self._lock = threading.Lock()
        # Storage format: {cache_key: (value, expire_timestamp, created_timestamp)}
        self._store: dict[str, tuple[Any, float, float]] = {}
        self.hits: int = 0
        self.misses: int = 0

    @staticmethod
    def compute_hash(text: str) -> str:
        """Computes deterministic SHA-256 hex hash from raw text."""
        normalized = str(text or "").strip().lower().encode("utf-8")
        return hashlib.sha256(normalized).hexdigest()

    def _make_key(self, namespace: str, text: str, extra_key: str | None = None) -> str:
        h = self.compute_hash(text)
        if extra_key:
            return f"{namespace}:{h}:{extra_key}"
        return f"{namespace}:{h}"

    def get(self, namespace: str, text: str, extra_key: str | None = None) -> Any | None:
        """
        Retrieves a cached value if present and unexpired.
        Returns None on miss or expired entry.
        """
        key = self._make_key(namespace, text, extra_key)
        now = time.time()

        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                self.misses += 1
                return None

            val, expire_at, _ = entry
            if now > expire_at:
                # Expired
                del self._store[key]
                self.misses += 1
                return None

            self.hits += 1
            return val

    def set(
        self,
        namespace: str,
        text: str,
        value: Any,
        ttl_seconds: float | None = None,
        extra_key: str | None = None,
    ) -> None:
        """
        Caches a computed result with a given TTL.
        """
        key = self._make_key(namespace, text, extra_key)
        ttl = self.default_ttl if ttl_seconds is None else float(ttl_seconds)
        now = time.time()
        expire_at = now + ttl

        with self._lock:
            # Capacity check: if exceeding bounds, prune expired entries
            if len(self._store) >= self.max_entries:
                self._prune_expired_locked(now)
                # If still at max, drop oldest 10%
                if len(self._store) >= self.max_entries:
                    sorted_keys = sorted(self._store.keys(), key=lambda k: self._store[k][1])
                    for k in sorted_keys[: max(1, len(sorted_keys) // 10)]:
                        self._store.pop(k, None)

            self._store[key] = (value, expire_at, now)

    def _prune_expired_locked(self, now: float) -> None:
        expired = [k for k, (_, exp, _) in self._store.items() if now > exp]
        for k in expired:
            del self._store[k]

    def clear(self, namespace: str | None = None) -> None:
        """Clears all entries or entries within a specific namespace."""
        with self._lock:
            if namespace is None:
                self._store.clear()
            else:
                prefix = f"{namespace}:"
                to_delete = [k for k in self._store if k.startswith(prefix)]
                for k in to_delete:
                    del self._store[k]

    def get_stats(self) -> dict[str, Any]:
        """Returns cache telemetry including hit rate, entry count, hits, and misses."""
        with self._lock:
            total = self.hits + self.misses
            hit_rate = round((self.hits / total) * 100.0, 2) if total > 0 else 0.0
            now = time.time()
            active_entries = sum(1 for _, exp, _ in self._store.values() if exp >= now)

            return {
                "active_entries": active_entries,
                "total_entries": len(self._store),
                "size": len(self._store),
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate_pct": hit_rate,
            }


# Global singleton cache instance
_global_cache = TextHashResponseCache()


def get_response_cache() -> TextHashResponseCache:
    """Returns the global response cache singleton."""
    return _global_cache


def get_cached_response(namespace: str, text: str, extra_key: str | None = None) -> Any | None:
    """Convenience getter for cached values."""
    return _global_cache.get(namespace, text, extra_key)


def cache_response(
    namespace: str,
    text: str,
    value: Any,
    ttl_seconds: float | None = None,
    extra_key: str | None = None,
) -> None:
    """Convenience setter for cached values."""
    _global_cache.set(namespace, text, value, ttl_seconds, extra_key)


def clear_response_cache(namespace: str | None = None) -> None:
    """Clears global response cache."""
    _global_cache.clear(namespace)


def get_cache_stats() -> dict[str, Any]:
    """Returns telemetry stats from global response cache."""
    return _global_cache.get_stats()
