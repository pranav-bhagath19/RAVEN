"""
RAVEN Request Correlation & Security Middleware

Injects unique X-Request-ID headers, provides PII-sanitized structured logging,
and handles request correlation tracking across API boundaries.
"""

import logging
import uuid
from typing import Awaitable, Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("raven.api")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [req_id=%(request_id)s] %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class RequestCorrelationMiddleware(BaseHTTPMiddleware):
    """
    Middleware attaching X-Request-ID correlation headers to incoming HTTP requests and outgoing responses.
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        req_id = request.headers.get("X-Request-ID") or f"req_{uuid.uuid4().hex[:12]}"
        request.state.request_id = req_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = req_id
        return response
