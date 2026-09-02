"""
RAVEN Event Ingestion & Deduplication Service

Handles webhook signature verification, SHA256 content deduplication,
and canonical FinancialEvent normalization.
"""

from datetime import datetime, timezone
import hashlib
import hmac
import logging
import uuid
from typing import Any
from domain.entities.financial_event import FinancialEvent
from domain.exceptions import DuplicateEventError
from domain.state.reconstructor import StateReconstructor
from domain.values.money import Money
from persistence.firestore_store import FirestoreEventRepository, FirestorePaymentRepository

logger = logging.getLogger("raven.events")


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
    Ingests, deduplicates, normalizes raw financial events, and persists them into Cloud Firestore.
    """

    def __init__(
        self,
        dedup_engine: EventDeduplicationEngine | None = None,
        event_repo: FirestoreEventRepository | None = None,
        payment_repo: FirestorePaymentRepository | None = None,
        raise_on_persistence_error: bool = False,
    ) -> None:
        self.dedup_engine = dedup_engine or EventDeduplicationEngine()
        self.ingested_events: list[FinancialEvent] = []
        self.reconstructor = StateReconstructor()
        self.raise_on_persistence_error = raise_on_persistence_error
        try:
            self.event_repo: FirestoreEventRepository | None = event_repo or FirestoreEventRepository()
            self.payment_repo: FirestorePaymentRepository | None = payment_repo or FirestorePaymentRepository()
        except Exception as err:
            logger.warning(f"Firestore repository initialization notice ({err}); using in-memory mode")
            self.event_repo = None
            self.payment_repo = None

    def ingest_event(
        self,
        raw_payload: FinancialEvent | dict[str, Any],
        event_type: str | None = None,
        gateway_event_id: str | None = None,
        occurred_at: datetime | None = None,
        sequence_number: int = 1,
    ) -> FinancialEvent:
        """
        Normalizes raw payload or FinancialEvent entity, enforces deduplication check,
        persists to Cloud Firestore, and appends to event log. Raises DuplicateEventError if duplicate.
        """
        if isinstance(raw_payload, FinancialEvent):
            financial_event = raw_payload
            event_hash = financial_event.event_hash
            extracted_gateway_id = financial_event.gateway_event_id

            if self.dedup_engine.is_duplicate(event_hash, extracted_gateway_id):
                raise DuplicateEventError(
                    event_id=extracted_gateway_id or event_hash,
                    message=f"Event with hash '{event_hash[:8]}...' or gateway ID '{extracted_gateway_id}' already ingested",
                )

            self.dedup_engine.register(event_hash, extracted_gateway_id)
            self.ingested_events.append(financial_event)
            self._persist_event_and_payment(financial_event)
            return financial_event

        target_event_type = event_type or raw_payload.get("event_type", "payment.failed")
        event_hash = FinancialEvent.compute_canonical_hash(raw_payload)
        extracted_gateway_id = gateway_event_id or raw_payload.get("event_id") or raw_payload.get("id")

        if self.dedup_engine.is_duplicate(event_hash, extracted_gateway_id):
            raise DuplicateEventError(
                event_id=extracted_gateway_id or event_hash,
                message=f"Event with hash '{event_hash[:8]}...' or gateway ID '{extracted_gateway_id}' already ingested",
            )

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
        raw_amount = raw_payload.get("amount_paise") or raw_payload.get("amount") or payment_payload.get("amount")
        currency = str(raw_payload.get("currency") or payment_payload.get("currency") or "INR")

        money_obj = (
            Money(amount_minor=int(raw_amount), currency=currency)
            if raw_amount is not None
            else None
        )

        event_timestamp = occurred_at or datetime.now(timezone.utc)

        financial_event = FinancialEvent(
            id=f"evt_{uuid.uuid4().hex[:12]}",
            event_hash=event_hash,
            event_type=target_event_type,
            gateway_event_id=extracted_gateway_id,
            entity_id=entity_id,
            order_id=order_id,
            merchant_id=merchant_id,
            customer_id=customer_id,
            amount=money_obj,
            payload=raw_payload,
            occurred_at=event_timestamp,
            sequence_number=sequence_number,
        )

        self.dedup_engine.register(event_hash, extracted_gateway_id)
        self.ingested_events.append(financial_event)
        self._persist_event_and_payment(financial_event)

        return financial_event

    def _persist_event_and_payment(self, financial_event: FinancialEvent) -> None:
        """Persists financial event and reconstructed payment state to Cloud Firestore."""
        logger.info(
            f"EVENT_INGESTED: event_id={financial_event.id}, "
            f"gateway_event_id={financial_event.gateway_event_id}, "
            f"payment_id={financial_event.entity_id}, "
            f"event_type={financial_event.event_type}"
        )

        try:
            logger.info(f"FIREBASE_WRITE_STARTED: event_id={financial_event.id}, payment_id={financial_event.entity_id}")

            if self.event_repo is not None:
                payload_data = financial_event.payload if isinstance(financial_event.payload, dict) else {}
                event_dict = {
                    "event_id": financial_event.id,
                    "tenant_id": financial_event.merchant_id or "default_tenant",
                    "event_hash": financial_event.event_hash,
                    "event_type": financial_event.event_type,
                    "entity_id": financial_event.entity_id,
                    "merchant_id": financial_event.merchant_id or "mer_default",
                    "amount_minor": financial_event.amount.amount_minor if financial_event.amount else 0,
                    "currency": financial_event.amount.currency if financial_event.amount else "INR",
                    "sequence_number": financial_event.sequence_number,
                    "occurred_at": financial_event.occurred_at,
                    "received_at": financial_event.received_at,
                    "payload_json": payload_data,
                }
                self.event_repo.save_event(event_dict)

            if self.payment_repo is not None:
                all_entity_events = self.get_events_for_entity(financial_event.entity_id)
                reconstructed = self.reconstructor.reconstruct_payment_state(financial_event.entity_id, all_entity_events)

                last_evt = all_entity_events[-1] if all_entity_events else None
                err_code = None
                err_desc = None
                if last_evt and isinstance(last_evt.payload, dict):
                    err_code = last_evt.payload.get("error_code") or last_evt.payload.get("error", {}).get("code")
                    err_desc = last_evt.payload.get("error_description") or last_evt.payload.get("error", {}).get("description")

                payment_dict = {
                    "payment_id": reconstructed.id,
                    "tenant_id": reconstructed.merchant_id or "default_tenant",
                    "order_id": reconstructed.order_id,
                    "merchant_id": reconstructed.merchant_id,
                    "customer_id": reconstructed.customer_id,
                    "amount_minor": reconstructed.amount.amount_minor if reconstructed.amount else 0,
                    "currency": reconstructed.amount.currency if reconstructed.amount else "INR",
                    "status": reconstructed.status.value,
                    "attempts_count": len(reconstructed.attempts),
                    "error_code": err_code,
                    "error_description": err_desc,
                    "created_at": reconstructed.created_at,
                }
                self.payment_repo.upsert_payment(payment_dict)

            logger.info(f"FIREBASE_WRITE_SUCCEEDED: event_id={financial_event.id}, payment_id={financial_event.entity_id}")

        except Exception as err:
            logger.error(
                f"FIREBASE_WRITE_FAILED: event_id={financial_event.id}, payment_id={financial_event.entity_id}, error={str(err)}",
                exc_info=True,
            )
            if self.raise_on_persistence_error:
                raise RuntimeError(f"Cloud Firestore persistence failed for event '{financial_event.id}': {str(err)}") from err

    def get_events_for_entity(self, entity_id: str) -> list[FinancialEvent]:
        """Returns all ingested events matching entity_id combining memory and Firestore repository."""
        mem_events = [e for e in self.ingested_events if e.entity_id == entity_id]

        if self.event_repo is not None:
            try:
                db_recs = self.event_repo.get_events_for_entity(entity_id)
                for rec in db_recs:
                    if not any(e.id == rec.event_id or e.event_hash == rec.event_hash for e in mem_events):
                        payload_dict = rec.payload_json if isinstance(rec.payload_json, dict) else {}
                        money_obj = Money(amount_minor=rec.amount_minor or 0, currency=rec.currency or "INR")
                        fe = FinancialEvent(
                            id=rec.event_id,
                            event_hash=rec.event_hash,
                            event_type=rec.event_type,
                            gateway_event_id=payload_dict.get("event_id"),
                            entity_id=rec.entity_id,
                            order_id=payload_dict.get("order_id") or f"order_{rec.entity_id}",
                            merchant_id=rec.merchant_id or "mer_default",
                            customer_id=payload_dict.get("customer_id") or f"cust_{rec.entity_id}",
                            amount=money_obj,
                            payload=payload_dict,
                            occurred_at=rec.occurred_at,
                            received_at=rec.received_at,
                            sequence_number=rec.sequence_number or 1,
                        )
                        mem_events.append(fe)
                        self.ingested_events.append(fe)
                        if rec.event_hash:
                            self.dedup_engine.register(rec.event_hash, rec.payload_json.get("event_id"))
            except Exception as err:
                logger.warning(f"Failed to load entity events from Firestore ({err}); falling back to memory")

        return mem_events

