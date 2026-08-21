"""
RAVEN Agent & LLM Boundary Exceptions

Defines explicit typed exceptions for LLM provider calls, schema validation, and timeouts.
Inherits from RavenDomainError.
"""

from typing import Any
from domain.exceptions import RavenDomainError


class LLMProviderError(RavenDomainError):
    """Raised when an LLM provider call fails or returns an API error."""

    def __init__(self, provider_name: str, message: str = "LLM provider call failed", details: dict[str, Any] | None = None) -> None:
        det = details or {}
        det["provider_name"] = provider_name
        super().__init__(message, det)


class LLMValidationError(RavenDomainError):
    """Raised when an LLM response fails Pydantic schema validation or output bounds."""

    def __init__(self, model_name: str, message: str = "LLM output schema validation failed", details: dict[str, Any] | None = None) -> None:
        det = details or {}
        det["model_name"] = model_name
        super().__init__(message, det)


class LLMTimeoutError(RavenDomainError):
    """Raised when an LLM provider call exceeds the configured timeout."""

    def __init__(self, provider_name: str, timeout_seconds: float) -> None:
        super().__init__(
            f"LLM provider '{provider_name}' call timed out after {timeout_seconds}s",
            {"provider_name": provider_name, "timeout_seconds": timeout_seconds},
        )


class LLMSchemaError(RavenDomainError):
    """Raised when an LLM output contains invalid or unauthorized action types/fields."""

    def __init__(self, message: str = "LLM output schema structure invalid") -> None:
        super().__init__(message)
