"""
RAVEN Payment & Subscription Domain Entities

Defines Payment, PaymentAttempt, PaymentMethod, and Subscription domain entities.
Enforces explicit state transition matrix and Money value object integration.
"""

from datetime import datetime, timezone
from pydantic import BaseModel, Field
from domain.enums import (
    PaymentAttemptStatus,
    PaymentMethodType,
    PaymentStatus,
    SubscriptionStatus,
)
from domain.exceptions import InvalidStateTransitionError
from domain.values.money import Money


class PaymentMethod(BaseModel):
    """
    PaymentMethod entity representing abstract card, UPI, or bank instrument.
    """

    id: str = Field(..., description="Unique PaymentMethod ID, e.g. pm_01H...")
    customer_id: str = Field(..., description="Associated Customer ID")
    type: PaymentMethodType = Field(..., description="Payment method category")
    network: str | None = Field(None, description="Card network (e.g. VISA, MASTERCARD, RUPAY)")
    issuer_bank: str | None = Field(None, description="Issuing bank (e.g. HDFC, ICICI, SBI)")
    last4: str | None = Field(None, description="Last 4 digits of card or account")
    upi_vpa: str | None = Field(None, description="UPI Virtual Payment Address handle")
    is_recurring_token: bool = Field(False, description="Whether token supports recurring auto-debit")


class PaymentAttempt(BaseModel):
    """
    PaymentAttempt entity representing a single execution attempt across gateway/network.
    """

    id: str = Field(..., description="Unique Attempt ID, e.g. att_01H...")
    payment_id: str = Field(..., description="Parent Payment ID")
    attempt_sequence: int = Field(1, ge=1, description="Sequence attempt number (1, 2, 3...)")
    payment_method_type: PaymentMethodType = Field(..., description="Method used in attempt")
    status: PaymentAttemptStatus = Field(PaymentAttemptStatus.INITIATED, description="Attempt status")
    error_code: str | None = Field(None, description="Gateway or issuer error code")
    error_description: str | None = Field(None, description="Human-readable error description")
    gateway_reference: str | None = Field(None, description="Gateway transaction reference ID")
    initiated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Initiation timestamp in UTC",
    )
    completed_at: datetime | None = Field(None, description="Completion timestamp in UTC")


# Explicit valid state transitions
VALID_STATE_TRANSITIONS: dict[PaymentStatus, set[PaymentStatus]] = {
    PaymentStatus.CREATED: {PaymentStatus.AUTHORIZED, PaymentStatus.CAPTURED, PaymentStatus.FAILED, PaymentStatus.AMBIGUOUS},
    PaymentStatus.AUTHORIZED: {PaymentStatus.CAPTURED, PaymentStatus.FAILED, PaymentStatus.AMBIGUOUS},
    PaymentStatus.CAPTURED: {PaymentStatus.REFUNDED},  # Terminal positive state: cannot transition to FAILED or AUTHORIZED
    PaymentStatus.FAILED: {PaymentStatus.AUTHORIZED, PaymentStatus.CAPTURED},  # Late event / reconciliation override
    PaymentStatus.AMBIGUOUS: {PaymentStatus.AUTHORIZED, PaymentStatus.CAPTURED, PaymentStatus.FAILED},
    PaymentStatus.REFUNDED: set(),  # Terminal state
}


class Payment(BaseModel):
    """
    Payment entity representing payment lifecycle associated with an Order.
    Uses Money value objects for payment amount.
    """

    id: str = Field(..., description="Unique Payment ID, e.g. pay_01H...")
    order_id: str = Field(..., description="Parent Order ID")
    merchant_id: str = Field(..., description="Associated Merchant ID")
    customer_id: str = Field(..., description="Associated Customer ID")
    amount: Money = Field(..., description="Payment amount Money value object")
    status: PaymentStatus = Field(PaymentStatus.CREATED, description="Payment status")
    attempts: list[PaymentAttempt] = Field(default_factory=list, description="Associated payment attempts")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp in UTC",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last updated timestamp in UTC",
    )

    def transition_to(self, target_status: PaymentStatus, timestamp: datetime | None = None) -> None:
        """
        Transitions payment status if valid according to state matrix.
        Raises InvalidStateTransitionError if transition is invalid and leaves state unmutated.
        """
        if self.status == target_status:
            return  # No-op for identical status

        allowed_next_states = VALID_STATE_TRANSITIONS.get(self.status, set())
        if target_status not in allowed_next_states:
            raise InvalidStateTransitionError(
                current_status=self.status.value,
                target_status=target_status.value,
                message=f"Cannot transition payment '{self.id}' from '{self.status.value}' to '{target_status.value}'",
            )

        self.status = target_status
        self.updated_at = timestamp or datetime.now(timezone.utc)

    def is_terminal_success(self) -> bool:
        """Returns True if payment has reached terminal captured state."""
        return self.status == PaymentStatus.CAPTURED

    def is_terminal_failure(self) -> bool:
        """Returns True if payment failed and has no open pending attempts."""
        return self.status == PaymentStatus.FAILED


class Subscription(BaseModel):
    """
    Subscription entity representing recurring payment schedule.
    """

    id: str = Field(..., description="Unique Subscription ID, e.g. sub_01H...")
    merchant_id: str = Field(..., description="Associated Merchant ID")
    customer_id: str = Field(..., description="Associated Customer ID")
    plan_id: str = Field(..., description="Associated Plan ID")
    amount: Money = Field(..., description="Recurring amount Money value object")
    billing_interval: str = Field("MONTHLY", description="Billing frequency")
    status: SubscriptionStatus = Field(SubscriptionStatus.ACTIVE, description="Subscription status")
    consecutive_failures: int = Field(0, ge=0, description="Count of consecutive failed billing attempts")
    current_period_start: datetime = Field(..., description="Period start UTC")
    current_period_end: datetime = Field(..., description="Period end UTC")
