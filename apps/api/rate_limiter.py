"""
RAVEN Rate Limiting Module

Provides sliding-window token-bucket rate limiting for HTTP gateway and webhooks.
"""

import threading
import time
from fastapi import HTTPException, Request, status


class TokenBucketRateLimiter:
    """Sliding-window token bucket rate limiter."""

    def __init__(self, requests_per_minute: int = 120) -> None:
        self.rate = requests_per_minute
        self.capacity = requests_per_minute
        self.tokens: dict[str, float] = {}
        self.last_updated: dict[str, float] = {}
        self._lock = threading.Lock()

    def check_rate_limit(self, client_id: str) -> None:
        """Enforces rate limit. Raises HTTP 429 if capacity exceeded."""
        now = time.time()
        with self._lock:
            if client_id not in self.tokens:
                self.tokens[client_id] = float(self.capacity)
                self.last_updated[client_id] = now

            elapsed = now - self.last_updated[client_id]
            self.tokens[client_id] = min(self.capacity, self.tokens[client_id] + elapsed * (self.rate / 60.0))
            self.last_updated[client_id] = now

            if self.tokens[client_id] < 1.0:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={"error": {"code": "RATE_LIMIT_EXCEEDED", "message": "Rate limit exceeded. Please retry later."}},
                )

            self.tokens[client_id] -= 1.0


_global_limiter = TokenBucketRateLimiter(requests_per_minute=300)


def rate_limit_middleware(request: Request) -> None:
    """Dependency enforcing rate limits on incoming API requests."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    _global_limiter.check_rate_limit(client_ip)
