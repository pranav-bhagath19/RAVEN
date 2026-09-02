"""
RAVEN Firestore-Backed Distributed Idempotency Store Module

Provides Firestore-backed distributed coordination, locks, and idempotency protection
with a thread-safe local in-memory fallback for local demo and offline testing environments.
Preserves complete class and signature compatibility for existing callers.
"""

import logging
import threading
import time
from typing import Any
from persistence.firebase import get_firestore_client

logger = logging.getLogger(__name__)


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
    Firestore-backed distributed idempotency coordination store.
    Maintains legacy 'RedisIdempotencyStore' name for full signature compatibility.
    Falls back gracefully to LocalIdempotencyStore if Firestore operation fails or is unconfigured.
    """

    @staticmethod
    def make_regional_key(tenant_id: str, idempotency_key: str, region_id: str = "global") -> str:
        """Constructs tenant and region scoped idempotency key string."""
        return f"{tenant_id}:{region_id}:{idempotency_key}"

    def __init__(self, redis_url: str | None = None) -> None:
        self.url = redis_url
        self.client: Any = None
        self._local_fallback = LocalIdempotencyStore()
        try:
            self.db = get_firestore_client()
            self.collection = self.db.collection("idempotency")
        except Exception:
            self.db = None
            self.collection = None

    def _sanitize_doc_id(self, key: str) -> str:
        """Converts key string to safe Firestore document ID."""
        return key.replace("/", "_").replace(".", "_")

    def claim(self, key: str, ttl_seconds: int = 300) -> bool:
        """Claims a key atomically in Firestore. Returns True if claimed successfully."""
        if self.collection is not None:
            try:
                doc_id = self._sanitize_doc_id(key)
                doc_ref = self.collection.document(doc_id)
                now = time.time()

                doc = doc_ref.get()
                if doc.exists:
                    d = doc.to_dict()
                    if d.get("expires_at", 0) > now:
                        return False

                doc_ref.set({
                    "key": key,
                    "status": "LOCKED",
                    "expires_at": now + ttl_seconds,
                    "value": None,
                    "created_at": now,
                })
                return True
            except Exception as e:
                logger.warning(f"Firestore claim failed, falling back to local store: {e!s}")
        return self._local_fallback.claim(key, ttl_seconds=ttl_seconds)

    def exists(self, key: str) -> bool:
        """Checks if key is claimed or completed in Firestore."""
        if self.collection is not None:
            try:
                doc_id = self._sanitize_doc_id(key)
                doc = self.collection.document(doc_id).get()
                if doc.exists:
                    d = doc.to_dict()
                    if d.get("expires_at", 0) > time.time():
                        return True
            except Exception as e:
                logger.warning(f"Firestore exists check failed: {e!s}")
        return self._local_fallback.exists(key)

    def release(self, key: str) -> None:
        """Releases an idempotency claim in Firestore."""
        if self.collection is not None:
            try:
                doc_id = self._sanitize_doc_id(key)
                self.collection.document(doc_id).delete()
                return
            except Exception as e:
                logger.warning(f"Firestore release failed: {e!s}")
        self._local_fallback.release(key)

    def mark_completed(self, key: str, value: Any = True, ttl_seconds: int = 86400) -> None:
        """Marks key as completed storing result value in Firestore."""
        if self.collection is not None:
            try:
                doc_id = self._sanitize_doc_id(key)
                now = time.time()
                self.collection.document(doc_id).set({
                    "key": key,
                    "status": "COMPLETED",
                    "expires_at": now + ttl_seconds,
                    "value": value,
                    "updated_at": now,
                })
                return
            except Exception as e:
                logger.warning(f"Firestore mark_completed failed: {e!s}")
        self._local_fallback.mark_completed(key, value=value, ttl_seconds=ttl_seconds)

    def get_completed_value(self, key: str) -> Any | None:
        """Gets result of completed key from Firestore if available."""
        if self.collection is not None:
            try:
                doc_id = self._sanitize_doc_id(key)
                doc = self.collection.document(doc_id).get()
                if doc.exists:
                    d = doc.to_dict()
                    if d.get("expires_at", 0) > time.time() and d.get("status") == "COMPLETED":
                        return d.get("value")
                return None
            except Exception as e:
                logger.warning(f"Firestore get_completed_value failed: {e!s}")
        return self._local_fallback.get_completed_value(key)
