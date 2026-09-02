"""
RAVEN External Service Circuit Breaker

Protects application against cascading failures when external services (Razorpay, LLMs) degrade.
"""

import threading
import time
from typing import Any, Callable, TypeVar

T = TypeVar("T")


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is OPEN."""


class CircuitBreaker:
    """
    Circuit breaker wrapper supporting CLOSED, OPEN, and HALF_OPEN state transitions.
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout_seconds: float = 30.0,
    ) -> None:
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout_seconds
        self.state = "CLOSED"
        self.failure_count = 0
        self.last_state_change = time.time()
        self._lock = threading.Lock()

    def call(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Executes func within circuit breaker protection."""
        now = time.time()
        with self._lock:
            if self.state == "OPEN":
                if now - self.last_state_change > self.recovery_timeout:
                    self.state = "HALF_OPEN"
                else:
                    raise CircuitBreakerOpenError(f"Circuit breaker '{self.name}' is OPEN. Call rejected.")

        try:
            result = func(*args, **kwargs)
            with self._lock:
                if self.state == "HALF_OPEN":
                    self.state = "CLOSED"
                    self.failure_count = 0
            return result
        except Exception:
            with self._lock:
                self.failure_count += 1
                if self.failure_count >= self.failure_threshold:
                    self.state = "OPEN"
                    self.last_state_change = time.time()
            raise
