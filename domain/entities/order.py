"""
RAVEN Order Domain Entity

Represents a commercial order intent.
Enforces Money value object integration and strict arithmetic balance invariants.
"""

from datetime import datetime, timezone
from pydantic import BaseModel, Field, model_validator
from domain.enums import OrderStatus
from domain.values.money import Money


class Order(BaseModel):
    """
    Order entity representing commercial purchase intent.
    Uses Money value objects for monetary balances.
    """

    id: str = Field(..., description="Unique Order ID, e.g. order_01H...")
    merchant_id: str = Field(..., description="Associated Merchant ID")
    customer_id: str = Field(..., description="Associated Customer ID")
    amount: Money = Field(..., description="Total order amount Money value object")
    amount_paid: Money = Field(..., description="Amount paid Money value object")
    amount_due: Money = Field(..., description="Amount due Money value object")
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
        if self.amount_paid.currency != self.amount.currency or self.amount_due.currency != self.amount.currency:
            raise ValueError(
                f"Order currency mismatch: amount ({self.amount.currency}), "
                f"paid ({self.amount_paid.currency}), due ({self.amount_due.currency})"
            )
        calculated_total = self.amount_paid + self.amount_due
        if calculated_total != self.amount:
            raise ValueError(
                f"Order balance invariant violated: amount_paid ({self.amount_paid.amount_minor}) + "
                f"amount_due ({self.amount_due.amount_minor}) != total amount ({self.amount.amount_minor})"
            )
        return self

    @classmethod
    def create(
        cls,
        order_id: str,
        merchant_id: str,
        customer_id: str,
        amount_minor: int,
        currency: str = "INR",
    ) -> "Order":
        """Factory method constructing a new unpaid Order."""
        total_money = Money(amount_minor=amount_minor, currency=currency)
        zero_money = Money.zero(currency=currency)
        return cls(
            id=order_id,
            merchant_id=merchant_id,
            customer_id=customer_id,
            amount=total_money,
            amount_paid=zero_money,
            amount_due=total_money,
            status=OrderStatus.CREATED,
        )

    def is_fully_paid(self) -> bool:
        """Returns True if order is completely settled."""
        return self.amount_paid >= self.amount and self.amount_due.amount_minor == 0
