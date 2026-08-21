"""
RAVEN Order Domain Entity

Represents a commercial order intent.
Enforces integer minor unit currency standards and strict balance invariants.
"""

from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, Field, model_validator


class OrderStatus(str, Enum):
    CREATED = "CREATED"
    ATTEMPTED = "ATTEMPTED"
    PAID = "PAID"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class Order(BaseModel):
    """
    Order entity representing commercial purchase intent.
    All monetary amounts are represented as integer minor units (e.g. paise).
    """

    id: str = Field(..., description="Unique Order ID, e.g. order_01H...")
    merchant_id: str = Field(..., description="Associated Merchant ID")
    customer_id: str = Field(..., description="Associated Customer ID")
    amount: int = Field(..., gt=0, description="Total order amount in integer minor units")
    amount_paid: int = Field(0, ge=0, description="Amount paid so far in integer minor units")
    amount_due: int = Field(..., ge=0, description="Amount remaining due in integer minor units")
    currency: str = Field("INR", description="ISO 4217 currency code")
    status: OrderStatus = Field(OrderStatus.CREATED, description="Order lifecycle status")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp in UTC",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last updated timestamp in UTC",
    )

    @model_validator(mode="after")
    def validate_order_balances(self) -> "Order":
        """Enforces domain invariant: amount_paid + amount_due == amount."""
        if self.amount_paid + self.amount_due != self.amount:
            raise ValueError(
                f"Order balance invariant violated: amount_paid ({self.amount_paid}) + "
                f"amount_due ({self.amount_due}) != total amount ({self.amount})"
            )
        return self

    def is_fully_paid(self) -> bool:
        """Returns True if order is completely settled."""
        return self.amount_paid >= self.amount and self.amount_due == 0
