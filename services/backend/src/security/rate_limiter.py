import logging
import time
from collections import defaultdict, deque

from fastapi import Header, HTTPException, Request

logger = logging.getLogger(__name__)

# Gateway Ingestion Rate Limiter (10 req / sec)
_gateway_limits = defaultdict(deque)
GATEWAY_MAX = 10
GATEWAY_WINDOW = 1.0

# IP OTP Rate Limiter (3 req / 60 sec)
_ip_limits = defaultdict(deque)
IP_MAX = 3
IP_WINDOW = 60.0


async def check_rate_limit(x_gateway_id: str = Header(..., description="ID of the forwarding gateway phone")):
    """Rate limit ingestion requests per gateway ID."""
    if not x_gateway_id:
        raise HTTPException(status_code=422, detail="MISSING_GATEWAY_ID")

    now = time.time()
    q = _gateway_limits[x_gateway_id]

    while q and now - q[0] > GATEWAY_WINDOW:
        q.popleft()

    if len(q) >= GATEWAY_MAX:
        logger.warning(f"Rate limit exceeded for Gateway {x_gateway_id}")
        raise HTTPException(status_code=429, detail="RATE_LIMITED")

    q.append(now)
    return x_gateway_id


async def check_otp_rate_limit(request: Request):
    """
    Rate limit OTP requests per real client IP.
    Reads X-Forwarded-For first (Render sits behind a proxy).
    Falls back to request.client.host so local dev still works.
    """
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For can be a comma-separated list; leftmost is the originating client
        client_ip = forwarded_for.split(",")[0].strip()
    else:
        client_ip = request.client.host if request.client else "unknown"

    now = time.time()
    q = _ip_limits[client_ip]

    while q and now - q[0] > IP_WINDOW:
        q.popleft()

    if len(q) >= IP_MAX:
        logger.warning(f"OTP rate limit exceeded for IP {client_ip}")
        raise HTTPException(status_code=429, detail="TOO_MANY_REQUESTS")

    q.append(now)
    return client_ip
