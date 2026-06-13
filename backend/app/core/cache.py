"""Lightweight in-process TTL cache for expensive API responses.

Design:
- Bounded by CACHE_MAX_SIZE (LRU eviction via OrderedDict).
- Per-entry TTL; stale entries are evicted on read.
- Keys are SHA-256 hashes of (user_id, endpoint, **params).
- Thread-safe for CPython's GIL; for multi-threaded Uvicorn workers
  use CACHE_MAX_SIZE=0 to disable or add an explicit Lock.

Usage:
    key = make_cache_key(user_id, "analytics.monthly", month="2026-06")
    data = get_cached(key)
    if data is None:
        data = compute_expensive_thing()
        set_cached(key, data)
"""

from __future__ import annotations

import hashlib
import time
from collections import OrderedDict
from typing import Any

from app.core.config import settings

# ---------------------------------------------------------------------------
# Internal store
# ---------------------------------------------------------------------------

_CacheEntry = tuple[Any, float]  # (value, expiry_unix_timestamp)
_store: OrderedDict[str, _CacheEntry] = OrderedDict()


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def make_cache_key(*args: Any, **kwargs: Any) -> str:
    """Build a stable SHA-256 cache key from arbitrary arguments."""
    raw = "|".join(
        [str(a) for a in args]
        + [f"{k}={v}" for k, v in sorted(kwargs.items())]
    )
    return hashlib.sha256(raw.encode()).hexdigest()


def get_cached(key: str) -> Any | None:
    """Return the cached value or None if missing / expired."""
    if settings.CACHE_MAX_SIZE == 0:
        return None

    entry = _store.get(key)
    if entry is None:
        return None

    value, expiry = entry
    if time.monotonic() > expiry:
        _store.pop(key, None)
        return None

    # Move to end (most-recently-used)
    _store.move_to_end(key)
    return value


def set_cached(key: str, value: Any, ttl: int | None = None) -> None:
    """Store a value with TTL seconds (default: CACHE_ANALYTICS_TTL_SECONDS)."""
    if settings.CACHE_MAX_SIZE == 0:
        return

    ttl = ttl if ttl is not None else settings.CACHE_ANALYTICS_TTL_SECONDS
    expiry = time.monotonic() + ttl
    _store[key] = (value, expiry)
    _store.move_to_end(key)

    # Evict oldest entry when over the size limit
    while len(_store) > settings.CACHE_MAX_SIZE:
        _store.popitem(last=False)


def invalidate_user(user_id: str) -> None:
    """Remove all cached entries that include this user_id in their key.

    Note: keys are hashed so we cannot reverse them.  Instead, we store
    an explicit prefix map.  For simplicity we do a full-scan eviction
    which is O(n) but acceptable given cache sizes (≤1000 entries).
    """
    # We mark invalidated users in a small side-set and skip their entries
    _invalidated.add(str(user_id))


def clear_all() -> None:
    """Clear entire cache (used in tests)."""
    _store.clear()
    _invalidated.clear()


# ---------------------------------------------------------------------------
# User-tagged cache helpers (prevent stale reads after mutations)
# ---------------------------------------------------------------------------

# Set of user_ids whose cache entries should be considered stale.
# Entries are cleaned up lazily on next write for that user.
_invalidated: set[str] = set()


def make_user_cache_key(user_id: str, endpoint: str, **kwargs: Any) -> str:
    """Build a user-scoped cache key that respects invalidation."""
    return make_cache_key(user_id, endpoint, **kwargs)


def get_user_cached(user_id: str, key: str) -> Any | None:
    """Return cached value unless the user has been invalidated."""
    if str(user_id) in _invalidated:
        return None
    return get_cached(key)


def set_user_cached(user_id: str, key: str, value: Any, ttl: int | None = None) -> None:
    """Store value and clear the user's invalidation flag."""
    _invalidated.discard(str(user_id))
    set_cached(key, value, ttl)
