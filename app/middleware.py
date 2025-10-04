from __future__ import annotations
from typing import Callable
from time import time
from fastapi import Request, Response
import uuid
import logging

# Simple IP-based token bucket (in-memory) for demo
_BUCKETS: dict[str, tuple[float, float]] = {}
RATE = 60  # requests per minute
logger = logging.getLogger(__name__)


async def security_headers_middleware(request: Request, call_next: Callable):
    response: Response = await call_next(request)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers['Permissions-Policy'] = 'geolocation=()'
    return response


async def rate_limit_middleware(request: Request, call_next: Callable):
    ip = request.client.host if request.client else 'unknown'
    now = time()
    tokens, last = _BUCKETS.get(ip, (RATE, now))
    # Refill
    elapsed = now - last
    tokens = min(RATE, tokens + elapsed * (RATE / 60.0))
    if tokens < 1 and request.method != 'GET':
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse('Too Many Requests', status_code=429)
    tokens -= 1
    _BUCKETS[ip] = (tokens, now)
    return await call_next(request)


async def request_id_middleware(request: Request, call_next: Callable):
    rid = request.headers.get('X-Request-ID') or str(uuid.uuid4())
    request.state.request_id = rid
    try:
        response: Response = await call_next(request)
    except Exception as e:
        logger.exception("Unhandled error: %s", e)
        # Always return JSONResponse to avoid optional orjson dependency issues
        from fastapi.responses import JSONResponse
        return JSONResponse({"error": "internal_error", "message": str(e), "request_id": rid}, status_code=500)
    response.headers['X-Request-ID'] = rid
    return response
