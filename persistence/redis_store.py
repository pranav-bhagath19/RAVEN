"""
RAVEN Redis & Distributed Idempotency Store Module

Provides Redis-backed distributed coordination, locks, and idempotency protection with a
thread-safe local in-memory fallback for local demo and offline testing environments.
"""

import os
import threading
import time
from typing import Any


class LocalIdempotencyStore:
    """Thread-safe in-memory fallback idempotency store for local development and demo modes."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._store: dict[str, dict[str, Any]] = {}

    def claim(self, key: str, ttl_seconds: int = 300) -> bool:
        """Claims an idempotency lock for key. Returns True if claimed, False if already claimed."""
        with self._lock:
            now = time.time()
            if key in self._store:
                entry = self._store[key]
                if entry["expires_at"] > now:
                    return False
            self._store[key] = {"status": "CLAIMED", "expires_at": now + ttl_seconds, "value": None}
            return True

    def exists(self, key: str) -> bool:
        """Returns True if key is currently active or completed."""
        with self._lock:
            now = time.time()
            if key in self._store:
                if self._store[key]["expires_at"] > now:
                    return True
                del self._store[key]
            return False

    def release(self, key: str) -> None:
        """Releases an idempotency claim."""
        with self._lock:
            self._store.pop(key, None)

    def mark_completed(self, key: str, value: Any = True, ttl_seconds: int = 86400) -> None:
        """Marks key as completed storing result value."""
        with self._lock:
            now = time.time()
            self._store[key] = {"status": "COMPLETED", "expires_at": now + ttl_seconds, "value": value}

    def get_completed_value(self, key: str) -> Any | None:
        """Returns completed value if present."""
        with self._lock:
            now = time.time()
            if key in self._store:
                entry = self._store[key]
                if entry["expires_at"] > now and entry["status"] == "COMPLETED":
                    return entry["value"]
            return None


class RedisIdempotencyStore:
    """
    Redis-backed distributed idempotency coordination store.
    Falls back gracefully to LocalIdempotencyStore if Redis connection fails or is unconfigured.
    """

    def __init__(self, redis_url: str | None = None) -> None:
        self.url = redis_url or os.getenv("REDIS_URL")
        self.client: Any = None
        self._local_fallback = LocalIdempotencyStore()

        if self.url:
            try:
                import redis
                self.client = redis.Redis.from_url(self.url, decode_responses=True)
                self.client.ping()
            except Exception:
                self.client = None

    def claim(self, key: str, ttl_seconds: int = 300) -> bool:
        """Claims a key atomically. Returns True if claimed successfully."""
        if self.client:
            try:
                res = self.client.set(f"idempotency:lock:{key}", "LOCKED", nx=True, ex=ttl_seconds)
                return bool(res)
            except Exception:
                pass
        return self._local_fallback.claim(key, ttl_seconds=ttl_seconds)

    def exists(self, key: str) -> bool:
        """Checks if key is claimed or completed."""
        if self.client:
            try:
                return bool(self.client.exists(f"idempotency:lock:{key}", f"idempotency:completed:{key}"))
            except Exception:
                pass
        return self._local_fallback.exists(key)

    def release(self, key: str) -> None:
        """Releases an idempotency claim."""
        if self.client:
            try:
                self.client.delete(f"idempotency:lock:{key}")
                return
            except Exception:
                pass
        self._local_fallback.release(key)

    def mark_completed(self, key: str, value: Any = True, ttl_seconds: int = 86400) -> None:
        """Marks key as completed storing result value."""
        if self.client:
            try:
                import json
                val_str = json.dumps(value) if not isinstance(value, str) else value
                self.client.set(f"idempotency:completed:{key}", val_str, ex=ttl_seconds)
                self.client.delete(f"idempotency:lock:{key}")
                return
            except Exception:
                pass
        self._local_fallback.mark_completed(key, value=value, ttl_seconds=ttl_seconds)

    def get_completed_value(self, key: str) -> Any | None:
        """Gets result of completed key if available."""
        if self.client:
            try:
                import json
                val_str = self.client.get(f"idempotency:completed:{key}")
                if val_str:
                    try:
                        return json.loads(val_str)
                    except Exception:
                        return val_str
                return None
            except Exception:
                pass
        return self._local_fallback.get_completed_value(key)
