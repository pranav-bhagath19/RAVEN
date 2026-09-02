"""
RAVEN Forensic Ingestion Test Suite

Proves end-to-end reliability, Firestore persistence, deduplication, signature security,
tenant isolation, state reconstruction, and dashboard API visibility for Razorpay webhooks.
"""

import hmac
import hashlib
import json
import pytest
from fastapi.testclient import TestClient
from apps.api.main import app
from events.ingestion import EventIngestionService
from persistence.firestore_store import FirestoreEventRepository, FirestorePaymentRepository
from persistence.firebase import reset_firestore_emulator

TEST_WEBHOOK_SECRET = "test_razorpay_webhook_secret_key_2026"

SAMPLE_PAYMENT_FAILED_PAYLOAD = {
    "entity": "event",
    "account_id": "acc_tenant_a_100",
    "event": "payment.failed",
    "contains": ["payment"],
    "payload": {
        "payment": {
            "entity": {
                "id": "pay_test_failed_001",
                "entity": "payment",
                "amount": 50000,
                "currency": "INR",
                "status": "failed",
                "order_id": "order_test_failed_001",
                "method": "card",
                "email": "customer@example.com",
                "contact": "+919876543210",
                "error_code": "BAD_REQUEST_ERROR",
                "error_description": "Payment failed due to insufficient funds",
                "error_source": "bank",
                "error_step": "payment_authorization",
                "error_reason": "insufficient_funds",
                "created_at": 1772530000,
            }
        }
    },
    "created_at": 1772530000,
}


def generate_signature(body: bytes, secret: str = TEST_WEBHOOK_SECRET) -> str:
    return hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


@pytest.fixture(autouse=True)
def clean_firestore_emulator():
    reset_firestore_emulator()
    yield
    reset_firestore_emulator()


client = TestClient(app)


# TEST 1: Valid Razorpay failed-payment webhook -> Firebase record created.
def test_1_valid_failed_payment_webhook_creates_firebase_record(monkeypatch):
    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", TEST_WEBHOOK_SECRET)
    raw_body = json.dumps(SAMPLE_PAYMENT_FAILED_PAYLOAD).encode("utf-8")
    sig = generate_signature(raw_body)

    response = client.post(
        "/api/v1/webhooks/razorpay",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": sig,
            "X-Razorpay-Event-Id": "evt_test_001",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "accepted"
    assert data["payment_id"] == "pay_test_failed_001"

    # Verify Firestore persistence
    event_repo = FirestoreEventRepository()
    events = event_repo.get_events_for_entity("pay_test_failed_001")
    assert len(events) >= 1
    assert events[0].entity_id == "pay_test_failed_001"

    payment_repo = FirestorePaymentRepository()
    payment_rec = payment_repo.get_by_id("pay_test_failed_001")
    assert payment_rec is not None
    assert payment_rec.payment_id == "pay_test_failed_001"
    assert str(payment_rec.status).upper() == "FAILED"


# TEST 2: Same webhook delivered twice -> exactly one persistent event/payment record.
def test_2_duplicate_webhook_deduplication(monkeypatch):
    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", TEST_WEBHOOK_SECRET)
    raw_body = json.dumps(SAMPLE_PAYMENT_FAILED_PAYLOAD).encode("utf-8")
    sig = generate_signature(raw_body)
    headers = {
        "Content-Type": "application/json",
        "X-Razorpay-Signature": sig,
        "X-Razorpay-Event-Id": "evt_test_dedup_001",
    }

    resp1 = client.post("/api/v1/webhooks/razorpay", content=raw_body, headers=headers)
    assert resp1.status_code == 200
    assert resp1.json()["duplicate"] is False

    resp2 = client.post("/api/v1/webhooks/razorpay", content=raw_body, headers=headers)
    assert resp2.status_code == 200
    assert resp2.json()["duplicate"] is True

    event_repo = FirestoreEventRepository()
    events = event_repo.get_events_for_entity("pay_test_failed_001")
    assert len(events) == 1


# TEST 3: Invalid signature -> rejected and NOT persisted.
def test_3_invalid_signature_rejection(monkeypatch):
    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", TEST_WEBHOOK_SECRET)
    payload = dict(SAMPLE_PAYMENT_FAILED_PAYLOAD)
    payload["payload"]["payment"]["entity"]["id"] = "pay_test_invalid_sig_001"
    raw_body = json.dumps(payload).encode("utf-8")

    response = client.post(
        "/api/v1/webhooks/razorpay",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": "invalid_signature_hash_12345",
        },
    )

    assert response.status_code == 401
    event_repo = FirestoreEventRepository()
    events = event_repo.get_events_for_entity("pay_test_invalid_sig_001")
    assert len(events) == 0


# TEST 4: Malformed payload -> rejected safely.
def test_4_malformed_json_payload_rejection(monkeypatch):
    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", TEST_WEBHOOK_SECRET)
    raw_body = b"{ malformed_json: true, "
    sig = generate_signature(raw_body)

    response = client.post(
        "/api/v1/webhooks/razorpay",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": sig,
        },
    )

    assert response.status_code == 400
    assert response.json()["error_code"] == "MALFORMED_JSON"


# TEST 5: Firebase unavailable -> explicit processing failure, never silent success.
def test_5_firebase_persistence_failure_raises_exception():
    ingestion = EventIngestionService(raise_on_persistence_error=True)
    class BrokenEventRepo:
        def save_event(self, data):
            raise ConnectionError("Firestore cluster unreachable")

    ingestion.event_repo = BrokenEventRepo()

    with pytest.raises(RuntimeError) as exc_info:
        ingestion.ingest_event(
            raw_payload={"payment_id": "pay_fail_db_001", "amount": 1000},
            event_type="payment.failed",
        )
    assert "Cloud Firestore persistence failed" in str(exc_info.value)


# TEST 6: Wrong event type -> correctly handled without triggering recovery pipeline.
def test_6_captured_event_type_handled_without_recovery_trigger(monkeypatch):
    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", TEST_WEBHOOK_SECRET)
    payload = dict(SAMPLE_PAYMENT_FAILED_PAYLOAD)
    payload["event"] = "payment.captured"
    payload["payload"]["payment"]["entity"]["status"] = "captured"
    payload["payload"]["payment"]["entity"]["id"] = "pay_captured_001"

    raw_body = json.dumps(payload).encode("utf-8")
    sig = generate_signature(raw_body)

    response = client.post(
        "/api/v1/webhooks/razorpay",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": sig,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "accepted"
    assert data["trace_id"] is None  # Recovery pipeline not triggered for captured events


# TEST 7: Correct tenant -> record belongs to correct tenant.
def test_7_record_belongs_to_correct_tenant(monkeypatch):
    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", TEST_WEBHOOK_SECRET)
    payload = dict(SAMPLE_PAYMENT_FAILED_PAYLOAD)
    payload["account_id"] = "acc_tenant_xyz"
    payload["payload"]["payment"]["entity"]["id"] = "pay_tenant_xyz_001"

    raw_body = json.dumps(payload).encode("utf-8")
    sig = generate_signature(raw_body)

    response = client.post(
        "/api/v1/webhooks/razorpay",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": sig,
        },
    )

    assert response.status_code == 200
    payment_repo = FirestorePaymentRepository()
    rec = payment_repo.get_by_id("pay_tenant_xyz_001")
    assert rec is not None
    assert rec.merchant_id == "acc_tenant_xyz"
    assert rec.tenant_id == "acc_tenant_xyz"


# TEST 8: Tenant A cannot read Tenant B's transaction.
def test_8_tenant_isolation_filter(monkeypatch):
    payment_repo = FirestorePaymentRepository()
    payment_repo.upsert_payment({
        "payment_id": "pay_tenant_a",
        "tenant_id": "acc_tenant_a",
        "merchant_id": "acc_tenant_a",
        "status": "failed",
    })
    payment_repo.upsert_payment({
        "payment_id": "pay_tenant_b",
        "tenant_id": "acc_tenant_b",
        "merchant_id": "acc_tenant_b",
        "status": "failed",
    })

    tenant_a_payments, total_a = payment_repo.list_payments(merchant_id="acc_tenant_a")
    assert total_a == 1
    assert tenant_a_payments[0].payment_id == "pay_tenant_a"


# TEST 9: Persisted failed payment -> state reconstruction works.
def test_9_state_reconstruction_from_persisted_events():
    event_repo = FirestoreEventRepository()
    event_repo.save_event({
        "event_id": "evt_recon_001",
        "tenant_id": "acc_test",
        "event_hash": "hash_recon_001",
        "event_type": "payment.failed",
        "entity_id": "pay_recon_001",
        "merchant_id": "acc_test",
        "amount_minor": 25000,
        "currency": "INR",
        "occurred_at": "2026-09-02T12:00:00Z",
        "payload_json": {"error_code": "BAD_REQUEST_ERROR", "error_description": "Card declined"},
    })

    ingestion = EventIngestionService()
    events = ingestion.get_events_for_entity("pay_recon_001")
    assert len(events) >= 1

    payment_state = ingestion.reconstructor.reconstruct_payment_state("pay_recon_001", events)
    assert payment_state.id == "pay_recon_001"
    assert str(payment_state.status.value).upper() == "FAILED"
    assert len(payment_state.attempts) == 1
    assert payment_state.attempts[0].error_code == "BAD_REQUEST_ERROR"


# TEST 10: Persisted failed payment -> dashboard API returns it.
import copy
import time
import uuid

def test_10_dashboard_api_returns_persisted_payment(monkeypatch):
    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", TEST_WEBHOOK_SECRET)
    unique_suffix = uuid.uuid4().hex[:8]
    unique_pay_id = f"pay_test_dash_{unique_suffix}"
    payload = copy.deepcopy(SAMPLE_PAYMENT_FAILED_PAYLOAD)
    payload["payload"]["payment"]["entity"]["id"] = unique_pay_id
    payload["created_at"] = int(time.time()) + 500
    payload["payload"]["payment"]["entity"]["created_at"] = int(time.time()) + 500
    raw_body = json.dumps(payload).encode("utf-8")
    sig = generate_signature(raw_body)

    # 1. Post webhook
    client.post(
        "/api/v1/webhooks/razorpay",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": sig,
        },
    )

    # 2. Query Dashboard REST API GET /api/v1/operations/payments
    response = client.get(
        "/api/v1/operations/payments",
        headers={
            "X-API-Key": "admin_dev_key",
            "X-Tenant-ID": "acc_tenant_a_100",
        },
    )

    assert response.status_code == 200
    res_json = response.json()
    items = res_json["items"]
    assert len(items) >= 1
    matching = [item for item in items if item["payment_id"] == unique_pay_id]
    assert len(matching) == 1
    assert matching[0]["status"].upper() == "FAILED"
    assert matching[0]["amount_minor"] == 50000
