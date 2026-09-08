import logging
import time
from collections import defaultdict, deque

from fastapi import Header, HTTPException, Request

logger = logging.getLogger(__name__)

# Gateway Ingestion Rate Limiter (10 req / sec per gateway)
_gateway_limits: dict[str, deque] = defaultdict(deque)
GATEWAY_MAX = 10
GATEWAY_WINDOW = 1.0

# IP OTP Rate Limiter (3 req / 60 sec)
_ip_limits: dict[str, deque] = defaultdict(deque)
IP_MAX = 3
IP_WINDOW = 60.0

# --- Memory-leak guard: cap total tracked keys to prevent OOM DoS ---
_GATEWAY_MAX_KEYS = 5_000
_IP_MAX_KEYS = 50_000

# --- Last prune timestamp ---
_last_prune: float = 0.0
_PRUNE_INTERVAL = 300.0  # prune every 5 minutes


def _prune_old_entries() -> None:
    """Evict stale keys from both dicts to prevent unbounded memory growth."""
    global _last_prune
    now = time.time()
    if now - _last_prune < _PRUNE_INTERVAL:
        return
    _last_prune = now
    for key in list(_gateway_limits.keys()):
        q = _gateway_limits[key]
        while q and now - q[0] > GATEWAY_WINDOW:
            q.popleft()
        if not q:
            del _gateway_limits[key]
    for key in list(_ip_limits.keys()):
        q = _ip_limits[key]
        while q and now - q[0] > IP_WINDOW:
            q.popleft()
        if not q:
            del _ip_limits[key]
    logger.debug("[RateLimiter] Pruned stale entries. gateway=%d ip=%d",
                 len(_gateway_limits), len(_ip_limits))


async def check_rate_limit(x_gateway_id: str = Header(..., description="ID of the forwarding gateway phone")):
    """Rate limit ingestion requests per gateway ID."""
    if not x_gateway_id or not x_gateway_id.strip():
        raise HTTPException(status_code=422, detail="MISSING_GATEWAY_ID")

    _prune_old_entries()

    # Hard cap on tracked keys — reject new gateways if dict is full (DoS guard)
    if x_gateway_id not in _gateway_limits and len(_gateway_limits) >= _GATEWAY_MAX_KEYS:
        logger.warning("[RateLimiter] Gateway dict full — rejecting new key %s", x_gateway_id)
        raise HTTPException(status_code=429, detail="RATE_LIMITED")

    now = time.time()
    q = _gateway_limits[x_gateway_id]
    while q and now - q[0] > GATEWAY_WINDOW:
        q.popleft()

    if len(q) >= GATEWAY_MAX:
        logger.warning("[RateLimiter] Rate limit exceeded for Gateway %s", x_gateway_id)
        raise HTTPException(status_code=429, detail="RATE_LIMITED")

    q.append(now)
    return x_gateway_id


async def check_otp_rate_limit(request: Request):
    """
    Rate limit OTP requests per real client IP.

    IP source priority:
    1. request.client.host (set by ASGI server/proxy — cannot be spoofed by clients)
    2. X-Forwarded-For ONLY as fallback for local dev where no proxy sets client.host

    SECURITY NOTE: In production (Render/Nginx), the proxy MUST be configured to
    strip X-Forwarded-For from incoming requests and overwrite it. If the proxy does
    that correctly, request.client.host will already be the real IP and we never
    need to read X-Forwarded-For here.
    """
    _prune_old_entries()

    # Prefer the ASGI transport-level IP (cannot be forged by the HTTP client)
    client_ip = request.client.host if request.client else None

    if not client_ip or client_ip in ("127.0.0.1", "::1", "testclient"):
        # Local dev / test: fall back to X-Forwarded-For (acceptable in dev)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = "unknown"

    # Hard cap — prevent OOM from millions of spoofed IPs
    if client_ip not in _ip_limits and len(_ip_limits) >= _IP_MAX_KEYS:
        logger.warning("[RateLimiter] IP dict full — rejecting request from %s", client_ip)
        raise HTTPException(status_code=429, detail="TOO_MANY_REQUESTS")

    now = time.time()
    q = _ip_limits[client_ip]
    while q and now - q[0] > IP_WINDOW:
        q.popleft()

    if len(q) >= IP_MAX:
        logger.warning("[RateLimiter] OTP rate limit exceeded for IP %s", client_ip)
        raise HTTPException(status_code=429, detail="TOO_MANY_REQUESTS")

    q.append(now)
    return client_ip
