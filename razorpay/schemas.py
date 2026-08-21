"""
Razorpay Webhook Event Schemas

Provides strongly typed Pydantic models for Razorpay webhook payload envelopes and payment entities.
"""

from typing import Any
from pydantic import BaseModel, Field


class RazorpayErrorEntity(BaseModel):
    """Razorpay failure error details payload."""

    code: str | None = Field(default=None, description="Razorpay error code, e.g. BAD_REQUEST_ERROR")
    description: str | None = Field(default=None, description="Human-readable error explanation")
    source: str | None = Field(default=None, description="Error source: bank, gateway, customer")
    step: str | None = Field(default=None, description="Processing step where failure occurred")
    reason: str | None = Field(default=None, description="Detailed failure reason")


class RazorpayPaymentEntity(BaseModel):
    """Razorpay Payment Entity structure inside payload.payment.entity."""

    id: str = Field(..., description="Razorpay Payment ID, e.g. pay_01H...")
    entity: str = Field("payment", description="Entity type string")
    amount: int = Field(..., ge=0, description="Amount in minor units (paise)")
    currency: str = Field("INR", description="ISO 4217 currency code")
    status: str = Field(..., description="Payment status: created, authorized, captured, failed, refunded")
    order_id: str | None = Field(default=None, description="Associated Order ID")
    invoice_id: str | None = Field(default=None, description="Associated Invoice ID")
    method: str | None = Field(default=None, description="Payment method: card, upi, netbanking, wallet")
    amount_refunded: int = Field(default=0, ge=0, description="Refunded amount in minor units")
    refund_status: str | None = Field(default=None, description="Refund status if applicable")
    captured: bool = Field(default=False, description="Whether payment is captured")
    description: str | None = Field(default=None, description="Transaction description")
    card_id: str | None = Field(default=None, description="Associated Card ID")
    bank: str | None = Field(default=None, description="Issuer bank code")
    wallet: str | None = Field(default=None, description="Wallet provider name")
    vpa: str | None = Field(default=None, description="UPI Virtual Payment Address")
    email: str | None = Field(default=None, description="Customer email address")
    contact: str | None = Field(default=None, description="Customer phone contact number")
    error_code: str | None = Field(default=None, description="Error code if failed")
    error_description: str | None = Field(default=None, description="Error description if failed")
    error_source: str | None = Field(default=None, description="Error source if failed")
    error_step: str | None = Field(default=None, description="Error step if failed")
    error_reason: str | None = Field(default=None, description="Error reason if failed")
    error: RazorpayErrorEntity | None = Field(default=None, description="Nested error object if present")
    created_at: int = Field(..., ge=0, description="Unix timestamp UTC")


class RazorpayPayloadWrapper(BaseModel):
    """Payload container holding entity snapshots."""

    payment: dict[str, Any] | None = Field(default=None, description="Payment wrapper containing 'entity'")
    order: dict[str, Any] | None = Field(default=None, description="Order wrapper containing 'entity'")
    refund: dict[str, Any] | None = Field(default=None, description="Refund wrapper containing 'entity'")


class RazorpayWebhookPayload(BaseModel):
    """Razorpay Webhook Envelope received at HTTP endpoint."""

    entity: str = Field("event", description="Wrapper entity type")
    account_id: str = Field(..., description="Razorpay Merchant Account ID, e.g. acc_01H...")
    event: str = Field(..., description="Webhook event name (e.g. payment.failed, payment.captured)")
    contains: list[str] = Field(default_factory=list, description="Entities contained in payload")
    payload: RazorpayPayloadWrapper = Field(..., description="Event payload wrapper")
    created_at: int = Field(..., ge=0, description="Event occurrence Unix timestamp UTC")

    def extract_payment_entity(self) -> RazorpayPaymentEntity | None:
        """Helper extracting RazorpayPaymentEntity from nested payload object."""
        if self.payload and self.payload.payment and "entity" in self.payload.payment:
            return RazorpayPaymentEntity.model_validate(self.payload.payment["entity"])
        return None
