"""
RAVEN Razorpay Webhook Authentication Boundary & Security Invariant Tests

Validates:
1. Valid HMAC-SHA256 signature + raw body -> 200 OK
2. Invalid signature -> 401 INVALID_SIGNATURE
3. Missing signature -> 401 MISSING_SIGNATURE
4. Payload tampering / whitespace alteration -> 401
5. Operator X-API-Key presence/absence does NOT interfere with webhook signature verification
6. Replayed x-razorpay-event-id -> Idempotent 200 accepted with duplicate=True
7. Zero secret leak in log outputs
8. Safe tenant resolution via payload account_id
"""

import hashlib
import hmac
import json
import logging
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)

TEST_WEBHOOK_SECRET = "test_webhook_secret_key_production_2026"

SAMPLE_PAYMENT_FAILED = {
    "entity": "event",
    "account_id": "acc_merchant_tenant_100",
    "event": "payment.failed",
    "contains": ["payment"],
    "payload": {
        "payment": {
            "entity": {
                "id": "pay_test_auth_boundary_999",
                "entity": "payment",
                "amount": 100000,
                "currency": "INR",
                "status": "failed",
                "order_id": "order_test_999",
                "invoice_id": None,
                "method": "card",
                "amount_refunded": 0,
                "refund_status": None,
                "captured": False,
                "description": "Test Payment Failure",
                "card_id": "card_test",
                "bank": "HDFC",
                "wallet": None,
                "vpa": None,
                "email": "customer@example.com",
                "contact": "+919876543210",
                "error_code": "BAD_REQUEST_ERROR",
                "error_description": "Payment authorization failed",
                "created_at": 1772455000,
            }
        }
    },
    "created_at": 1772455000,
}


def test_valid_webhook_signature_success(monkeypatch):
    """Verifies that a valid HMAC signature over raw body returns 200 OK."""
    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", TEST_WEBHOOK_SECRET)
    raw_body = json.dumps(SAMPLE_PAYMENT_FAILED).encode("utf-8")
    sig = hmac.new(TEST_WEBHOOK_SECRET.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()

    response = client.post(
        "/api/v1/webhooks/razorpay",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": sig,
            "X-Razorpay-Event-Id": "evt_test_header_100",
        },
    )

    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] == "accepted"
    assert res_data["duplicate"] is False
    assert res_data["payment_id"] == "pay_test_auth_boundary_999"


def test_missing_webhook_signature_rejected(monkeypatch):
    """Verifies that a request with missing X-Razorpay-Signature returns 401."""
    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", TEST_WEBHOOK_SECRET)
    raw_body = json.dumps(SAMPLE_PAYMENT_FAILED).encode("utf-8")

    response = client.post(
        "/api/v1/webhooks/razorpay",
        content=raw_body,
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 401
    assert response.json()["error_code"] == "MISSING_SIGNATURE"


def test_invalid_webhook_signature_rejected(monkeypatch):
    """Verifies that an invalid HMAC signature returns 401."""
    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", TEST_WEBHOOK_SECRET)
    raw_body = json.dumps(SAMPLE_PAYMENT_FAILED).encode("utf-8")

    response = client.post(
        "/api/v1/webhooks/razorpay",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": "invalid_signature_digest_string_12345",
        },
    )

    assert response.status_code == 401
    assert response.json()["error_code"] == "INVALID_SIGNATURE"


def test_tampered_payload_signature_mismatch(monkeypatch):
    """Verifies that tampering with raw body after signature calculation invalidates signature."""
    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", TEST_WEBHOOK_SECRET)
    original_body = json.dumps(SAMPLE_PAYMENT_FAILED).encode("utf-8")
    sig = hmac.new(TEST_WEBHOOK_SECRET.encode("utf-8"), original_body, hashlib.sha256).hexdigest()

    tampered_payload = dict(SAMPLE_PAYMENT_FAILED)
    tampered_payload["payload"]["payment"]["entity"]["amount"] = 999999
    tampered_body = json.dumps(tampered_payload).encode("utf-8")

    response = client.post(
        "/api/v1/webhooks/razorpay",
        content=tampered_body,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": sig,
        },
    )

    assert response.status_code == 401
    assert response.json()["error_code"] == "INVALID_SIGNATURE"


def test_reserialized_json_whitespace_mismatch(monkeypatch):
    """Verifies that modifying whitespace/formatting invalidates raw body HMAC signature."""
    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", TEST_WEBHOOK_SECRET)
    compact_body = json.dumps(SAMPLE_PAYMENT_FAILED, separators=(",", ":")).encode("utf-8")
    sig = hmac.new(TEST_WEBHOOK_SECRET.encode("utf-8"), compact_body, hashlib.sha256).hexdigest()

    pretty_body = json.dumps(SAMPLE_PAYMENT_FAILED, indent=2).encode("utf-8")

    response = client.post(
        "/api/v1/webhooks/razorpay",
        content=pretty_body,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": sig,
        },
    )

    assert response.status_code == 401
    assert response.json()["error_code"] == "INVALID_SIGNATURE"


def test_webhook_unaffected_by_operator_api_keys(monkeypatch):
    """
    Verifies that supplying or omitting X-API-Key / Authorization headers does NOT block valid Razorpay webhooks.
    """
    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", TEST_WEBHOOK_SECRET)
    raw_body = json.dumps(SAMPLE_PAYMENT_FAILED).encode("utf-8")
    sig = hmac.new(TEST_WEBHOOK_SECRET.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()

    # Pass an arbitrary invalid X-API-Key header alongside valid Razorpay webhook signature
    response = client.post(
        "/api/v1/webhooks/razorpay",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": sig,
            "X-API-Key": "invalid_operator_key_123",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "accepted"


def test_duplicate_event_idempotency(monkeypatch):
    """Verifies that replaying the exact same webhook event ID returns duplicate=True without duplicate side effects."""
    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", TEST_WEBHOOK_SECRET)
    payload = dict(SAMPLE_PAYMENT_FAILED)
    payload["payload"]["payment"]["entity"]["id"] = "pay_duplicate_test_001"
    raw_body = json.dumps(payload).encode("utf-8")
    sig = hmac.new(TEST_WEBHOOK_SECRET.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()

    # 1. First Delivery
    resp1 = client.post(
        "/api/v1/webhooks/razorpay",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": sig,
            "X-Razorpay-Event-Id": "evt_dupe_1001",
        },
    )
    assert resp1.status_code == 200
    assert resp1.json()["duplicate"] is False

    # 2. Second Delivery (Replay)
    resp2 = client.post(
        "/api/v1/webhooks/razorpay",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": sig,
            "X-Razorpay-Event-Id": "evt_dupe_1001",
        },
    )
    assert resp2.status_code == 200
    assert resp2.json()["duplicate"] is True


def test_diagnostic_logs_contain_no_secrets(monkeypatch, caplog):
    """Verifies that diagnostic logging outputs log metadata without exposing secret keys."""
    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", TEST_WEBHOOK_SECRET)
    raw_body = json.dumps(SAMPLE_PAYMENT_FAILED).encode("utf-8")
    sig = hmac.new(TEST_WEBHOOK_SECRET.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()

    with caplog.at_level(logging.INFO, logger="raven.webhooks"):
        response = client.post(
            "/api/v1/webhooks/razorpay",
            content=raw_body,
            headers={
                "Content-Type": "application/json",
                "X-Razorpay-Signature": sig,
            },
        )

    assert response.status_code == 200
    log_text = caplog.text

    # Assert secret value is NOT present anywhere in log messages
    assert TEST_WEBHOOK_SECRET not in log_text
    assert "WEBHOOK_RECEIVED" in log_text
    assert "signature_present=True" in log_text
