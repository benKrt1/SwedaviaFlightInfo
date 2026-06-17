import time
from typing import Any, Callable, Optional


class TTLCache:
    """A small in-memory cache where each entry expires after a fixed TTL."""

    def __init__(self, ttl_seconds: int = 60, time_fn: Callable[[], float] = time.time):
        self._ttl = ttl_seconds
        self._time_fn = time_fn
        self._store: dict[str, tuple[float, Any]] = {}

    def set(self, key: str, value: Any) -> None:
        self._store[key] = (self._time_fn(), value)

    def get(self, key: str) -> Optional[Any]:
        entry = self._store.get(key)
        if entry is None:
            return None
        stored_at, value = entry
        if self._time_fn() - stored_at >= self._ttl:
            del self._store[key]
            return None
        return value
