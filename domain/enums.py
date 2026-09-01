"""
RAVEN Domain Enums Module

Defines standard constrained state enumerations derived strictly from approved domain documentation.
"""

from enum import Enum


class MerchantStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    ONBOARDING = "ONBOARDING"


class PaymentStatus(str, Enum):
    CREATED = "CREATED"
    AUTHORIZED = "AUTHORIZED"
    CAPTURED = "CAPTURED"
    REFUNDED = "REFUNDED"
    FAILED = "FAILED"
    AMBIGUOUS = "AMBIGUOUS"


class PaymentAttemptStatus(str, Enum):
    INITIATED = "INITIATED"
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class PaymentMethodType(str, Enum):
    CARD = "CARD"
    UPI = "UPI"
    NETBANKING = "NETBANKING"
    WALLET = "WALLET"
    NACH = "NACH"


class FinancialEventType(str, Enum):
    PAYMENT_AUTHORIZED = "payment.authorized"
    PAYMENT_CAPTURED = "payment.captured"
    PAYMENT_FAILED = "payment.failed"
    ORDER_PAID = "order.paid"
    REFUND_CREATED = "refund.created"


class RecoveryActionType(str, Enum):
    SMART_RETRY = "SMART_RETRY"
    PAYMENT_LINK_DISPATCH = "PAYMENT_LINK_DISPATCH"
    FALLBACK_CHANNEL_NOTIFY = "FALLBACK_CHANNEL_NOTIFY"
    ESCALATE_TO_HUMAN = "ESCALATE_TO_HUMAN"


class RecoveryOutcomeStatus(str, Enum):
    RECOVERED = "RECOVERED"
    UNRECOVERED = "UNRECOVERED"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"


class OpportunityStatus(str, Enum):
    OPEN = "OPEN"
    ANALYZING = "ANALYZING"
    ACTION_PROPOSED = "ACTION_PROPOSED"
    EXECUTING = "EXECUTING"
    VERIFYING = "VERIFYING"
    RECOVERED = "RECOVERED"
    FAILED = "FAILED"
    ESCALATED = "ESCALATED"


class SubscriptionStatus(str, Enum):
    ACTIVE = "ACTIVE"
    PAST_DUE = "PAST_DUE"
    HALTED = "HALTED"
    CANCELLED = "CANCELLED"


class OrderStatus(str, Enum):
    CREATED = "CREATED"
    ATTEMPTED = "ATTEMPTED"
    PAID = "PAID"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class ActorType(str, Enum):
    SYSTEM = "SYSTEM"
    AGENT_ROOT_CAUSE = "AGENT_ROOT_CAUSE"
    AGENT_RECOVERY_PLANNER = "AGENT_RECOVERY_PLANNER"
    AGENT_VERIFIER = "AGENT_VERIFIER"
    POLICY_ENGINE = "POLICY_ENGINE"
    HUMAN_OPERATOR = "HUMAN_OPERATOR"


class RegionStatus(str, Enum):
    ACTIVE = "ACTIVE"
    DEGRADED = "DEGRADED"
    OFFLINE = "OFFLINE"
    RECOVERING = "RECOVERING"


class ReplicationStatus(str, Enum):
    PENDING = "PENDING"
    SYNCHRONIZED = "SYNCHRONIZED"
    CONFLICT = "CONFLICT"
    FAILED = "FAILED"
    STALE = "STALE"


class ReconciliationStrategy(str, Enum):
    AUTHORITATIVE_DESCENDANT = "AUTHORITATIVE_DESCENDANT"
    FAIL_CLOSED = "FAIL_CLOSED"
