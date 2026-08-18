import hashlib
import json
import os
from pathlib import Path
from typing import Any

from diskcache import Cache

_DEFAULT_CACHE_DIR = Path(__file__).resolve().parent.parent / ".cache" / "clinisight"
CACHE_DIR = os.getenv("CLINISIGHT_CACHE_DIR", str(_DEFAULT_CACHE_DIR))

_cache = Cache(CACHE_DIR)


def _make_key(namespace: str, *parts: Any) -> str:
    payload = json.dumps(parts, sort_keys=True, default=str)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"{namespace}:{digest}"


def get_cached(namespace: str, *parts: Any) -> Any:
    """Returns the cached value for (namespace, *parts), or None on a miss."""
    return _cache.get(_make_key(namespace, *parts))


def set_cached(namespace: str, *parts: Any, value: Any) -> None:
    """Stores value under (namespace, *parts) with no expiry."""
    _cache.set(_make_key(namespace, *parts), value)


def clear_cache() -> int:
    """Removes every cached entry and returns how many were removed."""
    removed = len(_cache)
    _cache.clear()
    return removed


def cache_stats() -> dict:
    return {"entries": len(_cache), "size_bytes": _cache.volume(), "directory": CACHE_DIR}
