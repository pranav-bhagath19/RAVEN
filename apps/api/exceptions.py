"""
RAVEN Global Production Exception Handlers

Provides structured, safe HTTP error responses without leaking stack traces, paths, or secrets.
"""

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


def register_exception_handlers(app: FastAPI) -> None:
    """Registers global Production Exception Handlers on FastAPI application."""

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        req_id = getattr(request.state, "request_id", "req_unknown")
        detail = exc.detail
        if isinstance(detail, dict):
            if "error" in detail:
                error_payload = dict(detail["error"])
                error_payload["request_id"] = req_id
                return JSONResponse(status_code=exc.status_code, content={"error": error_payload})
            error_payload = dict(detail)
            error_payload["request_id"] = req_id
            return JSONResponse(status_code=exc.status_code, content={"error": error_payload})

        code = "NOT_FOUND" if exc.status_code == 404 else "HTTP_ERROR"
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": code,
                    "message": str(detail),
                    "request_id": req_id,
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        req_id = getattr(request.state, "request_id", "req_unknown")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Input validation failed",
                    "request_id": req_id,
                    "details": exc.errors(),
                }
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        req_id = getattr(request.state, "request_id", "req_unknown")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected internal server error occurred.",
                    "request_id": req_id,
                }
            },
        )
