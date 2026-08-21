"""
RAVEN Payment & Subscription Domain Entities

Defines Payment, PaymentAttempt, PaymentMethod, and Subscription entities.
"""

from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, Field


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


class SubscriptionStatus(str, Enum):
    ACTIVE = "ACTIVE"
    PAST_DUE = "PAST_DUE"
    HALTED = "HALTED"
    CANCELLED = "CANCELLED"


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
    PaymentAttempt entity representing a single execution across gateway/network.
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


class Payment(BaseModel):
    """
    Payment entity representing payment lifecycle associated with an Order.
    """

    id: str = Field(..., description="Unique Payment ID, e.g. pay_01H...")
    order_id: str = Field(..., description="Parent Order ID")
    merchant_id: str = Field(..., description="Associated Merchant ID")
    customer_id: str = Field(..., description="Associated Customer ID")
    amount: int = Field(..., gt=0, description="Payment amount in integer minor units")
    currency: str = Field("INR", description="ISO 4217 currency code")
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
    amount: int = Field(..., gt=0, description="Recurring amount in integer minor units")
    billing_interval: str = Field("MONTHLY", description="Billing frequency")
    status: SubscriptionStatus = Field(SubscriptionStatus.ACTIVE, description="Subscription status")
    consecutive_failures: int = Field(0, ge=0, description="Count of consecutive failed billing attempts")
    current_period_start: datetime = Field(..., description="Period start UTC")
    current_period_end: datetime = Field(..., description="Period end UTC")
