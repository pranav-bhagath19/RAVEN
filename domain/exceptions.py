"""
RAVEN Domain Exceptions Module

Defines explicit, typed domain exceptions for RAVEN.
Broad exception swallowing (e.g. `except Exception:`) is strictly prohibited.
"""

from typing import Any


class RavenDomainError(Exception):
    """Base exception for all RAVEN domain errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class InvalidMoneyError(RavenDomainError):
    """Raised when a Money object is instantiated with invalid minor units or currency."""

    def __init__(self, message: str = "Invalid monetary amount or currency") -> None:
        super().__init__(message)


class CurrencyMismatchError(RavenDomainError):
    """Raised when performing arithmetic on Money objects with differing currencies."""

    def __init__(self, currency_a: str, currency_b: str) -> None:
        super().__init__(
            f"Cannot perform operation between Money in '{currency_a}' and '{currency_b}'",
            {"currency_a": currency_a, "currency_b": currency_b},
        )


class InvalidIdentifierError(RavenDomainError):
    """Raised when an identifier string fails validation rules or prefix expectations."""

    def __init__(self, identifier_type: str, value: str, message: str | None = None) -> None:
        msg = message or f"Invalid {identifier_type} value: '{value}'"
        super().__init__(msg, {"identifier_type": identifier_type, "value": value})


class InvalidStateTransitionError(RavenDomainError):
    """Raised when an illegal state transition is attempted on an entity (e.g. CAPTURED -> AUTHORIZED)."""

    def __init__(self, current_status: str, target_status: str, message: str | None = None) -> None:
        msg = message or f"Illegal state transition from '{current_status}' to '{target_status}'"
        super().__init__(msg, {"current_status": current_status, "target_status": target_status})


class PaymentStateConflictError(RavenDomainError):
    """Raised when an incoming event conflicts with an established terminal payment state."""

    def __init__(self, current_status: str, attempted_event: str) -> None:
        super().__init__(
            f"Event '{attempted_event}' conflicts with terminal payment status '{current_status}'",
            {"current_status": current_status, "attempted_event": attempted_event},
        )


class InvalidEventError(RavenDomainError):
    """Raised when a FinancialEvent payload or schema is malformed or invalid."""

    def __init__(self, message: str = "Invalid financial event representation") -> None:
        super().__init__(message)


class DuplicateEventIdentityError(RavenDomainError):
    """Raised when an incoming event fails identity deduplication checks."""

    def __init__(self, event_id: str, message: str = "Duplicate event identity detected") -> None:
        super().__init__(
            message,
            {"event_id": event_id},
        )


# Alias for backward compatibility
DuplicateEventError = DuplicateEventIdentityError


class InvalidDecisionTraceError(RavenDomainError):
    """Raised when a DecisionTrace object contains inconsistent or missing lifecycle data."""

    def __init__(self, message: str = "Invalid DecisionTrace lifecycle data") -> None:
        super().__init__(message)


class PolicyViolationError(RavenDomainError):
    """Raised when an operation violates Policy Engine bounds or lacks authorization."""

    def __init__(self, policy_rule_code: str, message: str = "Policy violation blocked action") -> None:
        super().__init__(message, {"policy_rule_code": policy_rule_code})


class RecoveryActionError(RavenDomainError):
    """Raised when a recovery action representation or parameter is invalid."""

    def __init__(self, action_id: str, message: str = "Recovery action error") -> None:
        super().__init__(message, {"action_id": action_id})


class WebhookSignatureError(RavenDomainError):
    """Raised when incoming webhook HMAC-SHA256 signature verification fails."""

    def __init__(self, message: str = "Webhook signature verification failed") -> None:
        super().__init__(message)


class ExternalServiceError(RavenDomainError):
    """Raised when an external service interface fails."""

    def __init__(self, service_name: str, status_code: int | None = None, message: str = "External service call failed") -> None:
        super().__init__(message, {"service_name": service_name, "status_code": status_code})


class EntityNotFoundError(RavenDomainError):
    """Raised when a requested domain entity is not found."""

    def __init__(self, entity_type: str, entity_id: str) -> None:
        super().__init__(f"{entity_type} '{entity_id}' not found", {"entity_type": entity_type, "entity_id": entity_id})
