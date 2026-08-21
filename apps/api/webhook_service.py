"""
RAVEN Webhook Service Application Layer

Coordinates raw webhook signature verification, canonical mapping, event ingestion,
deduplication, state reconstruction, and AgentOrchestrator execution.
"""

import json
import os
from typing import Any
from agents.common.provider import BaseLLMProvider, MockLLMProvider
from agents.orchestrator import AgentOrchestrator
from apps.api.schemas import WebhookResponse
from domain.entities.customer import Customer
from domain.entities.merchant import Merchant
from domain.enums import MerchantStatus
from domain.exceptions import DuplicateEventError, DuplicateEventIdentityError
from events.ingestion import EventIngestionService
from razorpay.mapper import RazorpayWebhookMapper
from razorpay.signatures import verify_razorpay_webhook_signature


class WebhookProcessingError(Exception):
    """Base exception for HTTP boundary webhook errors."""

    def __init__(self, error_code: str, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.message = message
        self.status_code = status_code


class WebhookService:
    """
    Application Service managing Razorpay webhook ingestion and autonomous recovery pipeline.
    """

    def __init__(
        self,
        webhook_secret: str | None = None,
        ingestion_service: EventIngestionService | None = None,
        orchestrator: AgentOrchestrator | None = None,
        provider: BaseLLMProvider | None = None,
    ) -> None:
        self.webhook_secret = webhook_secret or os.getenv("RAZORPAY_WEBHOOK_SECRET", "placeholder_webhook_secret")
        self.ingestion_service = ingestion_service or EventIngestionService()
        self.orchestrator = orchestrator or AgentOrchestrator()
        self.provider = provider or MockLLMProvider()
        self.mapper = RazorpayWebhookMapper()
        self.repository: Any | None = None

    def process_razorpay_webhook(
        self,
        raw_body: bytes,
        signature: str | None,
    ) -> WebhookResponse:
        """
        Verifies webhook signature, maps event, ingests into domain ledger, and triggers recovery pipeline.
        """
        # 1. Signature Verification
        if not signature:
            raise WebhookProcessingError("MISSING_SIGNATURE", "X-Razorpay-Signature header is missing", status_code=401)

        valid_sig = verify_razorpay_webhook_signature(
            raw_body=raw_body,
            signature=signature,
            secret=self.webhook_secret,
        )

        if not valid_sig:
            raise WebhookProcessingError("INVALID_SIGNATURE", "HMAC-SHA256 signature verification failed", status_code=401)

        # 2. JSON Parsing
        try:
            raw_payload: dict[str, Any] = json.loads(raw_body.decode("utf-8"))
        except Exception as e:
            raise WebhookProcessingError("MALFORMED_JSON", f"Invalid JSON payload: {str(e)}", status_code=400) from e

        # 3. Canonical Event Mapping
        try:
            canonical_event = self.mapper.map_to_canonical_event(raw_payload)
        except Exception as e:
            raise WebhookProcessingError("MAPPING_FAILURE", f"Failed to map Razorpay event payload: {str(e)}", status_code=400) from e

        # 4. Ingestion & Deduplication
        try:
            self.ingestion_service.ingest_event(canonical_event)
            is_duplicate = False
        except (DuplicateEventError, DuplicateEventIdentityError):
            is_duplicate = True

        if is_duplicate:
            return WebhookResponse(
                status="accepted",
                event_id=canonical_event.id,
                event_type=canonical_event.event_type,
                payment_id=canonical_event.entity_id,
                duplicate=True,
                trace_id=None,
            )

        # 5. Recovery Pipeline Trigger for failure events
        trace_id: str | None = None
        event_type_lower = canonical_event.event_type.lower()

        if "failed" in event_type_lower or "ambiguous" in event_type_lower or "pending" in event_type_lower:
            merchant = Merchant(
                id=canonical_event.merchant_id,
                name="Merchant Business",
                currency=canonical_event.currency,
                status=MerchantStatus.ACTIVE,
            )
            customer = Customer(
                id=canonical_event.customer_id or f"cust_{canonical_event.entity_id}",
                merchant_id=merchant.id,
                email="customer@example.com",
                phone="+919876543210",
                name="Customer Name",
            )

            # Retrieve accumulated event ledger for this payment
            all_events = self.ingestion_service.get_events_for_entity(canonical_event.entity_id)

            trace = self.orchestrator.process_payment_failure(
                events=all_events,
                merchant=merchant,
                customer=customer,
                provider=self.provider,
                error_code=canonical_event.payload.get("error_code"),
            )
            trace_id = trace.decision_id
            if self.repository is not None:
                self.repository.record_trace(trace)

        return WebhookResponse(
            status="accepted",
            event_id=canonical_event.id,
            event_type=canonical_event.event_type,
            payment_id=canonical_event.entity_id,
            duplicate=False,
            trace_id=trace_id,
        )
