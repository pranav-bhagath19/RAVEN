"""
RAVEN Event Ingestion & Deduplication Service

Handles webhook signature verification, SHA256 content deduplication,
and canonical FinancialEvent normalization.
"""

from datetime import datetime, timezone
import hmac
import hashlib
import uuid
from typing import Any
from domain.exceptions import DuplicateEventError, WebhookSignatureError
from domain.state.event import FinancialEvent


def verify_webhook_signature(raw_payload: bytes, signature_header: str | None, secret: str | None) -> bool:
    """
    Verifies incoming webhook HMAC-SHA256 signature using constant-time string comparison.
    """
    if not signature_header or not secret or not raw_payload:
        return False
    expected_signature = hmac.new(
        secret.encode("utf-8"),
        raw_payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_signature, signature_header)


class EventDeduplicationEngine:
    """
    In-memory and indexed deduplication engine checking event content hashes and gateway IDs.
    """

    def __init__(self) -> None:
        self._processed_hashes: set[str] = set()
        self._processed_gateway_ids: set[str] = set()

    def is_duplicate(self, event_hash: str, gateway_event_id: str | None = None) -> bool:
        """Returns True if event matching hash or gateway event ID has already been ingested."""
        if event_hash in self._processed_hashes:
            return True
        if gateway_event_id and gateway_event_id in self._processed_gateway_ids:
            return True
        return False

    def register(self, event_hash: str, gateway_event_id: str | None = None) -> None:
        """Registers event hash and gateway event ID in deduplication index."""
        self._processed_hashes.add(event_hash)
        if gateway_event_id:
            self._processed_gateway_ids.add(gateway_event_id)

    def clear(self) -> None:
        """Clears deduplication index (used in testing)."""
        self._processed_hashes.clear()
        self._processed_gateway_ids.clear()


class EventIngestionService:
    """
    Ingests, deduplicates, and normalizes raw financial events.
    """

    def __init__(self, dedup_engine: EventDeduplicationEngine | None = None) -> None:
        self.dedup_engine = dedup_engine or EventDeduplicationEngine()
        self.ingested_events: list[FinancialEvent] = []

    def ingest_event(
        self,
        raw_payload: dict[str, Any],
        event_type: str,
        gateway_event_id: str | None = None,
        occurred_at: datetime | None = None,
        sequence_number: int = 1,
    ) -> FinancialEvent:
        """
        Normalizes raw payload, enforces deduplication check, and appends to event log.
        """
        event_hash = FinancialEvent.compute_hash(raw_payload)

        # Extract gateway event ID if present in payload
        extracted_gateway_id = gateway_event_id or raw_payload.get("event_id") or raw_payload.get("id")

        if self.dedup_engine.is_duplicate(event_hash, extracted_gateway_id):
            raise DuplicateEventError(
                event_id=extracted_gateway_id or event_hash,
                message=f"Event with hash '{event_hash[:8]}...' or gateway ID '{extracted_gateway_id}' already ingested"
            )

        # Extract entity IDs and metadata
        payment_payload = raw_payload.get("payment", {}).get("entity", raw_payload)
        entity_id = (
            raw_payload.get("payment_id")
            or payment_payload.get("id")
            or raw_payload.get("order_id")
            or raw_payload.get("entity_id")
            or f"pay_{uuid.uuid4().hex[:12]}"
        )
        order_id = raw_payload.get("order_id") or payment_payload.get("order_id")
        merchant_id = raw_payload.get("merchant_id") or "mer_default"
        customer_id = raw_payload.get("customer_id") or payment_payload.get("customer_id")
        amount = raw_payload.get("amount_paise") or raw_payload.get("amount") or payment_payload.get("amount")
        currency = raw_payload.get("currency") or payment_payload.get("currency") or "INR"

        event_timestamp = occurred_at or datetime.now(timezone.utc)

        financial_event = FinancialEvent(
            id=f"evt_{uuid.uuid4().hex[:12]}",
            event_hash=event_hash,
            event_type=event_type,
            gateway_event_id=extracted_gateway_id,
            entity_id=entity_id,
            order_id=order_id,
            merchant_id=merchant_id,
            customer_id=customer_id,
            amount_minor_units=int(amount) if amount is not None else None,
            currency=currency,
            payload=raw_payload,
            occurred_at=event_timestamp,
            sequence_number=sequence_number,
        )

        self.dedup_engine.register(event_hash, extracted_gateway_id)
        self.ingested_events.append(financial_event)

        return financial_event
