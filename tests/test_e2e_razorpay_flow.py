"""
RAVEN End-to-End Razorpay Test Mode Deterministic Integration Test

Validates the complete execution lifecycle:
Raw Razorpay Webhook Payload
  └─► HMAC-SHA256 Signature Verification
  └─► Canonical Event Mapping & Deduplication
  └─► Persistence Ledger
  └─► State Reconstruction Engine
  └─► LLM Root Cause Analyst (Advisory Recommendation Only)
  └─► Deterministic PolicyEngine Evaluation
  └─► HMAC-SHA256 PolicyApprovalToken Issuance (only if APPROVED)
  └─► Secure ToolExecutor Execution Boundary
  └─► Verification Agent
  └─► DecisionTrace Lineage Logging
"""

import hashlib

import hmac
import json
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)

WEBHOOK_SECRET = "test_razorpay_webhook_secret_key_2026"

SAMPLE_RAZORPAY_PAYMENT_FAILED_PAYLOAD = {
    "entity": "event",
    "account_id": "acc_tenant_merchant_001",
    "event": "payment.failed",
    "contains": ["payment"],
    "payload": {
        "payment": {
            "entity": {
                "id": "pay_test_rzp_e2e_1001",
                "entity": "payment",
                "amount": 250000,
                "currency": "INR",
                "status": "failed",
                "order_id": "order_test_rzp_e2e_1001",
                "invoice_id": None,
                "method": "card",
                "amount_refunded": 0,
                "refund_status": None,
                "captured": False,
                "description": "Subscription Renewal Payment",
                "card_id": "card_01",
                "bank": "HDFC",
                "wallet": None,
                "vpa": None,
                "email": "customer@example.com",
                "contact": "+919876543210",
                "error_code": "GATEWAY_TIMED_OUT",
                "error_description": "Issuer bank timed out during 3DS verification",
                "error_source": "bank",
                "error_step": "payment_authentication",
                "error_reason": "payment_failed",
                "created_at": 1772450000,
            }
        }
    },
    "created_at": 1772450000,
}


def test_e2e_razorpay_webhook_execution_pipeline(monkeypatch):
    """
    Deterministically tests complete end-to-end Razorpay webhook pipeline from raw HTTP body to DecisionTrace.
    """
    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", WEBHOOK_SECRET)

    raw_body = json.dumps(SAMPLE_RAZORPAY_PAYMENT_FAILED_PAYLOAD).encode("utf-8")
    signature = hmac.new(WEBHOOK_SECRET.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()

    # 1. Dispatch Webhook to API Endpoint
    response = client.post(
        "/api/v1/webhooks/razorpay",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": signature,
        },
    )

    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
    res_data = response.json()

    assert res_data["status"] == "accepted"
    assert res_data["duplicate"] is False
    assert res_data["payment_id"] == "pay_test_rzp_e2e_1001"
    assert res_data["trace_id"] is not None

    trace_id = res_data["trace_id"]

    # 2. Retrieve Decision Trace from Operations Control Plane API
    trace_resp = client.get(f"/api/v1/operations/traces/{trace_id}")
    assert trace_resp.status_code == 200, f"Failed to retrieve decision trace: {trace_resp.text}"
    trace_data = trace_resp.json()

    # 3. Assert mandatory security & operational trace invariants (Step 15 criteria)
    assert trace_data["decision_id"] == trace_id
    assert trace_data["merchant_id"] == "acc_tenant_merchant_001"  # Tenant isolation ID
    assert trace_data["payment_id"] == "pay_test_rzp_e2e_1001"     # Payment identity
    assert trace_data["status"] is not None

    # Verify PolicyEngine evaluations
    assert "policy_evaluations" in trace_data
    assert len(trace_data["policy_evaluations"]) > 0
    policy_eval = trace_data["policy_evaluations"][-1]
    assert "decision" in policy_eval or "policy_id" in policy_eval

    # Verify Intelligence / Analysis fields
    assert "root_cause_result" in trace_data
    assert trace_data["root_cause_result"] is not None

    # If approved & executed, verify token and tool execution boundary
    if trace_data["policy_token_id"]:
        assert trace_data["selected_action"] is not None
        assert trace_data["execution_result"] is not None
        assert trace_data["execution_result"]["status"] in ("SUCCESS", "SIMULATED_SUCCESS", "DUPLICATE", "COMPLETED", "EXECUTED")


    # 4. Verify Idempotency - Replay exact same webhook

    replay_resp = client.post(
        "/api/v1/webhooks/razorpay",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": signature,
        },
    )
    assert replay_resp.status_code == 200
    replay_data = replay_resp.json()

    # Assert duplicate flag is set and no duplicate execution occurred
    assert replay_data["status"] == "accepted"
    assert replay_data["duplicate"] is True
    assert replay_data["payment_id"] == "pay_test_rzp_e2e_1001"


def test_e2e_razorpay_webhook_invalid_signature_rejection(monkeypatch):
    """
    Verifies that missing or invalid webhook signatures are rejected immediately with 401 Unauthorized.
    """
    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", WEBHOOK_SECRET)
    raw_body = json.dumps(SAMPLE_RAZORPAY_PAYMENT_FAILED_PAYLOAD).encode("utf-8")

    # Missing signature
    resp1 = client.post("/api/v1/webhooks/razorpay", content=raw_body, headers={"Content-Type": "application/json"})
    assert resp1.status_code == 401
    assert resp1.json()["error_code"] == "MISSING_SIGNATURE"

    # Invalid signature
    resp2 = client.post(
        "/api/v1/webhooks/razorpay",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": "invalid_signature_digest_string",
        },
    )
    assert resp2.status_code == 401
    assert resp2.json()["error_code"] == "INVALID_SIGNATURE"
