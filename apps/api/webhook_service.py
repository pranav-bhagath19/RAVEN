"""
RAVEN Webhook Service Application Layer

Coordinates raw webhook signature verification, canonical mapping, event ingestion,
deduplication, state reconstruction, and AgentOrchestrator execution.
"""

import json
import logging
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

logger = logging.getLogger("raven.webhooks")


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
        self._explicit_secret = webhook_secret
        self.ingestion_service = ingestion_service or EventIngestionService()
        self.orchestrator = orchestrator or AgentOrchestrator()
        self.provider = provider or MockLLMProvider()
        self.mapper = RazorpayWebhookMapper()
        self.repository: Any | None = None

    @property
    def webhook_secret(self) -> str:
        return self._explicit_secret or os.getenv("RAZORPAY_WEBHOOK_SECRET") or "placeholder_webhook_secret"

    def process_razorpay_webhook(
        self,
        raw_body: bytes,
        signature: str | None,
        event_id_header: str | None = None,
    ) -> WebhookResponse:
        """
        Verifies webhook signature, maps event, ingests into domain ledger, and triggers recovery pipeline.
        """
        effective_secret = self.webhook_secret
        has_secret = bool(effective_secret and effective_secret != "placeholder_webhook_secret")

        # Stage 1: WEBHOOK_RECEIVED
        logger.info(
            f"WEBHOOK_RECEIVED: signature_present={bool(signature)}, "
            f"event_id_present={bool(event_id_header)}, "
            f"body_length={len(raw_body)}, "
            f"secret_configured={has_secret}, "
            f"secret_len={len(effective_secret) if effective_secret else 0}"
        )

        # 1. Signature Verification
        if not signature:
            logger.warning("WEBHOOK_PROCESSING_FAILED: stage=SIGNATURE_VERIFICATION, error_code=MISSING_SIGNATURE")
            raise WebhookProcessingError("MISSING_SIGNATURE", "X-Razorpay-Signature header is missing", status_code=401)

        valid_sig = verify_razorpay_webhook_signature(
            raw_body=raw_body,
            signature=signature,
            secret=effective_secret,
        )

        if not valid_sig:
            logger.warning("WEBHOOK_PROCESSING_FAILED: stage=SIGNATURE_VERIFICATION, error_code=INVALID_SIGNATURE")
            raise WebhookProcessingError("INVALID_SIGNATURE", "HMAC-SHA256 signature verification failed", status_code=401)

        logger.info("SIGNATURE_VERIFIED: valid=True")

        # 2. JSON Parsing
        try:
            raw_payload: dict[str, Any] = json.loads(raw_body.decode("utf-8"))
        except Exception as e:
            logger.warning(f"WEBHOOK_PROCESSING_FAILED: stage=JSON_PARSING, error={e}")
            raise WebhookProcessingError("MALFORMED_JSON", f"Invalid JSON payload: {str(e)}", status_code=400) from e

        # 3. Canonical Event Mapping
        try:
            canonical_event = self.mapper.map_to_canonical_event(
                raw_payload,
                event_id_override=event_id_header,
            )
        except Exception as e:
            logger.warning(f"WEBHOOK_PROCESSING_FAILED: stage=EVENT_MAPPING, error={e}")
            raise WebhookProcessingError("MAPPING_FAILURE", f"Failed to map Razorpay event payload: {str(e)}", status_code=400) from e

        logger.info(
            f"EVENT_PARSED: event_id={canonical_event.id}, "
            f"gateway_event_id={canonical_event.gateway_event_id}, "
            f"payment_id={canonical_event.entity_id}, "
            f"event_type={canonical_event.event_type}"
        )
        logger.info(f"EVENT_CLASSIFIED: event_type={canonical_event.event_type}")
        logger.info(f"TENANT_RESOLVED: tenant_id={canonical_event.merchant_id}")

        # 4. Ingestion & Deduplication & Cloud Firestore Persistence
        try:
            self.ingestion_service.ingest_event(canonical_event)
            is_duplicate = False
        except (DuplicateEventError, DuplicateEventIdentityError):
            is_duplicate = True

        logger.info(
            f"IDEMPOTENCY_CHECKED: event_id={canonical_event.id}, "
            f"payment_id={canonical_event.entity_id}, "
            f"duplicate={is_duplicate}"
        )

        if is_duplicate:
            logger.info(f"PROCESSING_COMPLETED: status=accepted, duplicate=True, event_id={canonical_event.id}")
            return WebhookResponse(
                status="accepted",
                event_id=canonical_event.id,
                event_type=canonical_event.event_type,
                payment_id=canonical_event.entity_id,
                duplicate=True,
                trace_id=None,
            )

        # 5. State Reconstruction & Recovery Pipeline Trigger
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
            logger.info(f"STATE_RECONSTRUCTED: payment_id={canonical_event.entity_id}, event_count={len(all_events)}")

            trace = self.orchestrator.process_payment_failure(
                events=all_events,
                merchant=merchant,
                customer=customer,
                provider=self.provider,
                error_code=canonical_event.payload.get("error_code") if isinstance(canonical_event.payload, dict) else None,
            )
            trace_id = trace.decision_id
            if self.repository is not None:
                self.repository.record_trace(trace)

        logger.info(
            f"PROCESSING_COMPLETED: status=accepted, "
            f"duplicate=False, "
            f"event_id={canonical_event.id}, "
            f"payment_id={canonical_event.entity_id}, "
            f"trace_id={trace_id}"
        )

        return WebhookResponse(
            status="accepted",
            event_id=canonical_event.id,
            event_type=canonical_event.event_type,
            payment_id=canonical_event.entity_id,
            duplicate=False,
            trace_id=trace_id,
        )


