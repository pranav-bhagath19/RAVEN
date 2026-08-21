"""
RAVEN Idempotency Store Module

Thread-safe in-memory idempotency registry preventing duplicate side-effect executions.
"""

import threading
from typing import Any


class IdempotencyStore:
    """
    In-memory, thread-safe idempotency registry checking and recording action execution keys.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._executed_keys: dict[str, Any] = {}

    def is_executed(self, idempotency_key: str) -> bool:
        """Returns True if idempotency key has already been executed."""
        with self._lock:
            return idempotency_key in self._executed_keys

    def record_execution(self, idempotency_key: str, result: Any) -> None:
        """Records completed execution result for idempotency key."""
        with self._lock:
            self._executed_keys[idempotency_key] = result

    def get_result(self, idempotency_key: str) -> Any | None:
        """Retrieves cached execution result for idempotency key if present."""
        with self._lock:
            return self._executed_keys.get(idempotency_key)

    def clear(self) -> None:
        """Clears idempotency registry (used in testing)."""
        with self._lock:
            self._executed_keys.clear()
