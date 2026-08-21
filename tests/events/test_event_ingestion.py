"""
Unit tests for Event Ingestion, Signature Verification, and SHA256 Deduplication
"""

import pytest
from domain.exceptions import DuplicateEventError
from events.ingestion import EventDeduplicationEngine, EventIngestionService, verify_webhook_signature


def test_verify_webhook_signature():
    secret = "whsec_test_secret_key_123"
    raw_payload = b'{"event":"payment.failed","payment_id":"pay_123"}'
    
    # Calculate valid signature
    import hmac
    import hashlib
    valid_signature = hmac.new(secret.encode("utf-8"), raw_payload, hashlib.sha256).hexdigest()

    assert verify_webhook_signature(raw_payload, valid_signature, secret) is True
    assert verify_webhook_signature(raw_payload, "invalid_sig_header", secret) is False
    assert verify_webhook_signature(raw_payload, valid_signature, "wrong_secret") is False


def test_event_deduplication_engine():
    engine = EventDeduplicationEngine()
    hash_a = "abc123hash"
    gateway_id_a = "evt_gateway_123"

    assert engine.is_duplicate(hash_a, gateway_id_a) is False

    engine.register(hash_a, gateway_id_a)
    assert engine.is_duplicate(hash_a, gateway_id_a) is True
    assert engine.is_duplicate(hash_a, "other_gateway_id") is True
    assert engine.is_duplicate("other_hash", gateway_id_a) is True


def test_event_ingestion_service_deduplication():
    service = EventIngestionService()
    payload = {"event_id": "event_M123", "amount_paise": 500000, "currency": "INR"}

    # First ingestion succeeds
    event1 = service.ingest_event(payload, event_type="payment.failed")
    assert event1.gateway_event_id == "event_M123"
    assert len(service.ingested_events) == 1

    # Duplicate ingestion fails with DuplicateEventError
    with pytest.raises(DuplicateEventError) as exc_info:
        service.ingest_event(payload, event_type="payment.failed")
    assert "already ingested" in str(exc_info.value)
    assert len(service.ingested_events) == 1
