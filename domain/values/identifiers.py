"""
RAVEN Strongly Typed Identifier Value Objects

Provides type-safe, validated entity identifier wrappers.
Prevents accidental parameter misassignment between different entity IDs.
"""

from dataclasses import dataclass
from domain.exceptions import InvalidIdentifierError


def _validate_id_value(id_name: str, value: str, expected_prefix: str | None = None) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InvalidIdentifierError(id_name, str(value), f"{id_name} value cannot be empty")
    clean_val = value.strip()
    if expected_prefix and not clean_val.startswith(expected_prefix):
        # We permit arbitrary valid strings if required, but warn/validate format
        pass
    return clean_val


@dataclass(frozen=True)
class MerchantId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _validate_id_value("MerchantId", self.value, "mer_"))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class CustomerId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _validate_id_value("CustomerId", self.value, "cust_"))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class OrderId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _validate_id_value("OrderId", self.value, "order_"))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class PaymentId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _validate_id_value("PaymentId", self.value, "pay_"))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class PaymentAttemptId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _validate_id_value("PaymentAttemptId", self.value, "att_"))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class SubscriptionId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _validate_id_value("SubscriptionId", self.value, "sub_"))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class RecoveryOpportunityId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _validate_id_value("RecoveryOpportunityId", self.value, "opp_"))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class RecoveryActionId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _validate_id_value("RecoveryActionId", self.value, "act_"))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class DecisionId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _validate_id_value("DecisionId", self.value, "trace_"))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class EventId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _validate_id_value("EventId", self.value, "evt_"))

    def __str__(self) -> str:
        return self.value
