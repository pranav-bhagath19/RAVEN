"""
Razorpay Gateway Adapter Boundary

Provides standard gateway interface connecting Razorpay API clients and webhooks to RAVEN domain entities.
"""

from typing import Any
from domain.entities.financial_event import FinancialEvent
from razorpay.client import BaseRazorpayClient, MockRazorpayClient
from razorpay.mapper import RazorpayWebhookMapper


class RazorpayAdapter:
    """
    Gateway Adapter managing Razorpay client operations and webhook event mapping.
    """

    def __init__(self, client: BaseRazorpayClient | None = None) -> None:
        self.client = client or MockRazorpayClient()
        self.mapper = RazorpayWebhookMapper()

    def process_webhook_payload(self, raw_payload: dict[str, Any]) -> FinancialEvent:
        """Maps raw Razorpay webhook payload dictionary to canonical FinancialEvent."""
        return self.mapper.map_to_canonical_event(raw_payload)

    def fetch_payment(self, payment_id: str) -> dict[str, Any]:
        """Delegates payment fetch to client."""
        return self.client.fetch_payment(payment_id)

    def create_payment_link(
        self,
        payment_id: str,
        amount_minor: int,
        description: str,
        idempotency_key: str,
    ) -> dict[str, Any]:
        """Delegates payment link creation to client."""
        return self.client.create_payment_link(
            payment_id=payment_id,
            amount_minor=amount_minor,
            description=description,
            idempotency_key=idempotency_key,
        )
