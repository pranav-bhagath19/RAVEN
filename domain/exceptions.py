"""
RAVEN Domain Exceptions Module

Defines explicit, typed domain and infrastructure exceptions for RAVEN.
Broad exception swallowing is strictly prohibited per RAVEN Engineering Quality Standards.
"""


class RavenDomainError(Exception):
    """Base exception class for all RAVEN domain errors."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class DuplicateEventError(RavenDomainError):
    """Raised when an incoming event fails deduplication check (matching event_hash or gateway_event_id)."""

    def __init__(self, event_id: str, message: str = "Duplicate event detected") -> None:
        super().__init__(message, {"event_id": event_id})


class PaymentStateConflictError(RavenDomainError):
    """Raised when an illegal or conflicting payment state transition is attempted."""

    def __init__(
        self, current_status: str, attempted_event: str, message: str = "Invalid state transition"
    ) -> None:
        super().__init__(
            message, {"current_status": current_status, "attempted_event": attempted_event}
        )


class PolicyViolationError(RavenDomainError):
    """Raised when an operation violates Policy Engine bounds or lacks a valid PolicyApprovalToken."""

    def __init__(self, policy_rule_code: str, message: str = "Policy violation blocked action") -> None:
        super().__init__(message, {"policy_rule_code": policy_rule_code})


class RecoveryActionError(RavenDomainError):
    """Raised when a recovery intervention fails execution or validation."""

    def __init__(self, action_id: str, message: str = "Recovery action execution failed") -> None:
        super().__init__(message, {"action_id": action_id})


class WebhookSignatureError(RavenDomainError):
    """Raised when incoming webhook HMAC-SHA256 signature verification fails."""

    def __init__(self, message: str = "Webhook signature verification failed") -> None:
        super().__init__(message)


class ExternalServiceError(RavenDomainError):
    """Raised when an external API or gateway adapter fails."""

    def __init__(self, service_name: str, status_code: int | None = None, message: str = "External service call failed") -> None:
        super().__init__(message, {"service_name": service_name, "status_code": status_code})


class EntityNotFoundError(RavenDomainError):
    """Raised when a queried entity (Order, Payment, Customer, Merchant) is not found."""

    def __init__(self, entity_type: str, entity_id: str) -> None:
        super().__init__(f"{entity_type} '{entity_id}' not found", {"entity_type": entity_type, "entity_id": entity_id})
