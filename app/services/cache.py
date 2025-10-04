from __future__ import annotations
import json
import os
from typing import Optional, Callable, Any
from config import settings

try:
    import redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None

_client: Optional["redis.Redis"] = None


def get_client() -> Optional["redis.Redis"]:
    global _client
    if _client is not None:
        return _client
    if redis is None or not settings.redis_url:
        return None
    try:
        _client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
        _client.ping()
        return _client
    except Exception:
        return None


def cache_get(key: str) -> Optional[Any]:
    c = get_client()
    if not c:
        return None
    v = c.get(key)
    if v is None:
        return None
    try:
        return json.loads(v)
    except Exception:
        return None


def cache_set(key: str, value: Any, ttl_seconds: int = 60) -> None:
    c = get_client()
    if not c:
        return
    try:
        c.setex(key, ttl_seconds, json.dumps(value))
    except Exception:
        pass
