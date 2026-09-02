"""
Razorpay Webhook Adapter & Mapper Module

Maps raw Razorpay webhook payloads into canonical RAVEN FinancialEvent domain entities.
Does NOT mutate Payment, Order, Customer, or Subscription directly.
"""

from datetime import datetime, timezone
from typing import Any
from domain.entities.financial_event import FinancialEvent
from domain.enums import FinancialEventType
from domain.values.money import Money
from razorpay.schemas import RazorpayWebhookPayload


class RazorpayWebhookMapper:
    """
    Adapter converting Razorpay webhook payloads into canonical RAVEN FinancialEvents.
    """

    @staticmethod
    def map_to_canonical_event(
        raw_payload: dict[str, Any],
        received_at: datetime | None = None,
        event_id_override: str | None = None,
    ) -> FinancialEvent:
        """
        Maps a raw Razorpay webhook payload dict into a canonical FinancialEvent entity.
        Supports X-Razorpay-Event-Id header override if present.
        """
        # Parse Pydantic envelope model
        envelope = RazorpayWebhookPayload.model_validate(raw_payload)
        payment_entity = envelope.extract_payment_entity()

        # Derive event IDs and timestamps
        event_name = envelope.event.lower()
        gateway_event_id = event_id_override or f"evt_{envelope.account_id}_{envelope.created_at}"

        if payment_entity:
            payment_id = payment_entity.id
            amount_minor = payment_entity.amount
            currency = payment_entity.currency
            order_id = payment_entity.order_id
            occurred_at = datetime.fromtimestamp(payment_entity.created_at, tz=timezone.utc)
            error_code = payment_entity.error_code or (payment_entity.error.code if payment_entity.error else None)
            error_desc = payment_entity.error_description or (payment_entity.error.description if payment_entity.error else None)
        else:
            payment_id = f"pay_unknown_{envelope.created_at}"
            amount_minor = 0
            currency = "INR"
            order_id = None
            occurred_at = datetime.fromtimestamp(envelope.created_at, tz=timezone.utc)
            error_code = None
            error_desc = None

        # Map event type string to RAVEN FinancialEventType
        if "captured" in event_name:
            mapped_event_type = FinancialEventType.PAYMENT_CAPTURED.value
        elif "authorized" in event_name:
            mapped_event_type = FinancialEventType.PAYMENT_AUTHORIZED.value
        elif "failed" in event_name:
            mapped_event_type = FinancialEventType.PAYMENT_FAILED.value
        elif "order.paid" in event_name or "paid" in event_name:
            mapped_event_type = FinancialEventType.ORDER_PAID.value
        elif "refund" in event_name:
            mapped_event_type = FinancialEventType.REFUND_CREATED.value
        else:
            mapped_event_type = event_name

        # Construct normalized payload dictionary for SHA-256 canonical hashing
        normalized_payload: dict[str, Any] = {
            "event_id": gateway_event_id,
            "payment_id": payment_id,
            "order_id": order_id or f"order_{payment_id}",
            "merchant_id": envelope.account_id,
            "customer_id": f"cust_{payment_id}",
            "amount": amount_minor,
            "currency": currency,
        }
        if error_code:
            normalized_payload["error_code"] = error_code
        if error_desc:
            normalized_payload["error_description"] = error_desc

        event_hash = FinancialEvent.compute_canonical_hash(normalized_payload)
        rx_time = received_at or datetime.now(timezone.utc)

        return FinancialEvent(
            id=f"evt_{payment_id}_{envelope.created_at}",
            event_hash=event_hash,
            event_type=mapped_event_type,
            gateway_event_id=gateway_event_id,
            entity_id=payment_id,
            order_id=order_id or f"order_{payment_id}",
            merchant_id=envelope.account_id,
            customer_id=f"cust_{payment_id}",
            amount=Money(amount_minor=amount_minor, currency=currency),
            payload=normalized_payload,
            occurred_at=occurred_at,
            received_at=rx_time,
            sequence_number=1,
        )
