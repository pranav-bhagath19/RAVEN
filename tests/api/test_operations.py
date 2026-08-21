"""
Integration Tests for RAVEN Operations Control Plane API (Step 20 Specification)
"""

import hmac
import hashlib
import json
import pytest
from fastapi.testclient import TestClient
from apps.api.dependencies import get_operations_service, get_webhook_service
from apps.api.main import app
from apps.api.operations_service import OperationsService
from apps.api.webhook_service import WebhookService


@pytest.fixture
def ops_service():
    return OperationsService()


@pytest.fixture
def webhook_service(ops_service):
    svc = WebhookService(
        webhook_secret="ops_test_secret_123",
        ingestion_service=ops_service.repository.ingestion_service,
        orchestrator=ops_service.orchestrator,
        provider=ops_service.provider,
    )
    svc.repository = ops_service.repository
    return svc


@pytest.fixture
def api_client(webhook_service, ops_service):
    app.dependency_overrides[get_webhook_service] = lambda: webhook_service
    app.dependency_overrides[get_operations_service] = lambda: ops_service
    yield TestClient(app)
    app.dependency_overrides.clear()


def ingest_sample_webhook(client: TestClient, payment_id: str = "pay_ops_100", secret: str = "ops_test_secret_123"):
    payload = {
        "entity": "event",
        "account_id": "acc_mer_ops",
        "event": "payment.failed",
        "contains": ["payment"],
        "payload": {
            "payment": {
                "entity": {
                    "id": payment_id,
                    "entity": "payment",
                    "amount": 250000,
                    "currency": "INR",
                    "status": "failed",
                    "email": "user@example.com",
                    "contact": "+919876543210",
                    "error_code": "GATEWAY_TIMED_OUT",
                    "error_description": "Gateway timed out",
                    "created_at": 1755777600,
                }
            }
        },
        "created_at": 1755777600,
    }
    raw_bytes = json.dumps(payload).encode("utf-8")
    sig = hmac.new(secret.encode("utf-8"), raw_bytes, hashlib.sha256).hexdigest()

    res = client.post(
        "/api/v1/webhooks/razorpay",
        content=raw_bytes,
        headers={"Content-Type": "application/json", "X-Razorpay-Signature": sig},
    )
    return res.json()


def test_1_overview_endpoint(api_client):
    ingest_sample_webhook(api_client, payment_id="pay_ops_ov1")
    response = api_client.get("/api/v1/operations/overview")
    assert response.status_code == 200
    data = response.json()
    assert "total_payments" in data
    assert "recovery_rate" in data
    assert data["total_payments"] >= 1


def test_2_payment_listing(api_client):
    ingest_sample_webhook(api_client, payment_id="pay_ops_list1")
    response = api_client.get("/api/v1/operations/payments")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) >= 1


def test_3_payment_filtering(api_client):
    ingest_sample_webhook(api_client, payment_id="pay_ops_filter1")
    response = api_client.get("/api/v1/operations/payments?status=failed")
    assert response.status_code == 200
    data = response.json()
    assert any(item["payment_id"] == "pay_ops_filter1" for item in data["items"])


def test_4_payment_pagination(api_client):
    ingest_sample_webhook(api_client, payment_id="pay_ops_page1")
    ingest_sample_webhook(api_client, payment_id="pay_ops_page2")
    response = api_client.get("/api/v1/operations/payments?page=1&page_size=1")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["page_size"] == 1


def test_5_payment_detail(api_client):
    ingest_sample_webhook(api_client, payment_id="pay_ops_detail1")
    response = api_client.get("/api/v1/operations/payments/pay_ops_detail1")
    assert response.status_code == 200
    data = response.json()
    assert data["payment_id"] == "pay_ops_detail1"
    assert "events" in data
    assert "status" in data


def test_6_event_listing(api_client):
    ingest_sample_webhook(api_client, payment_id="pay_ops_evt1")
    response = api_client.get("/api/v1/operations/events")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) >= 1


def test_7_decision_listing(api_client):
    ingest_sample_webhook(api_client, payment_id="pay_ops_dec1")
    response = api_client.get("/api/v1/operations/decisions")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data


def test_8_decision_trace_retrieval(api_client):
    res_wb = ingest_sample_webhook(api_client, payment_id="pay_ops_trace1")
    trace_id = res_wb["trace_id"]

    response = api_client.get(f"/api/v1/operations/traces/{trace_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["decision_id"] == trace_id
    assert "chronological_timeline" in data
    assert len(data["chronological_timeline"]) >= 2


def test_9_policy_listing(api_client):
    response = api_client.get("/api/v1/operations/policies")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 7  # POL_001 through POL_007
    pol_ids = {p["policy_id"] for p in data}
    assert "POL_001" in pol_ids
    assert "POL_007" in pol_ids


def test_10_tool_execution_listing(api_client):
    ingest_sample_webhook(api_client, payment_id="pay_ops_tool1")
    response = api_client.get("/api/v1/operations/tool-executions")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data


def test_11_verification_listing(api_client):
    ingest_sample_webhook(api_client, payment_id="pay_ops_ver1")
    response = api_client.get("/api/v1/operations/verifications")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data


def test_12_agent_telemetry_listing(api_client):
    ingest_sample_webhook(api_client, payment_id="pay_ops_telem1")
    response = api_client.get("/api/v1/operations/agents/telemetry")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data


def test_13_benchmark_retrieval(api_client):
    response = api_client.get("/api/v1/operations/benchmarks")
    assert response.status_code == 200
    data = response.json()
    assert "benchmark_version" in data
    assert "benchmark_hash" in data


def test_14_health_endpoint(api_client):
    response = api_client.get("/api/v1/operations/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["api_status"] == "healthy"


def test_15_readiness_endpoint(api_client):
    response = api_client.get("/api/v1/operations/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"


def test_16_unknown_payment_404(api_client):
    response = api_client.get("/api/v1/operations/payments/pay_nonexistent_999")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PAYMENT_NOT_FOUND"


def test_17_unknown_trace_404(api_client):
    response = api_client.get("/api/v1/operations/traces/trace_nonexistent_999")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "TRACE_NOT_FOUND"


def test_18_invalid_pagination(api_client):
    response = api_client.get("/api/v1/operations/payments?page=0")
    assert response.status_code == 422  # Pydantic Query validation error (ge=1)


def test_19_maximum_pagination_enforcement(api_client):
    response = api_client.get("/api/v1/operations/payments?page_size=500")
    assert response.status_code == 422  # Pydantic Query validation error (le=100)


def test_20_pii_sanitization_in_telemetry(api_client):
    ingest_sample_webhook(api_client, payment_id="pay_ops_pii1")
    response = api_client.get("/api/v1/operations/agents/telemetry")
    assert response.status_code == 200
    data = response.json()
    for item in data["items"]:
        assert "user@example.com" not in item["input_summary"]
        assert "+919876543210" not in item["input_summary"]


def test_21_secret_redaction_in_operations(api_client):
    res_wb = ingest_sample_webhook(api_client, payment_id="pay_ops_sec1")
    trace_id = res_wb["trace_id"]
    response = api_client.get(f"/api/v1/operations/traces/{trace_id}")
    assert response.status_code == 200
    text = json.dumps(response.json())
    assert "ops_test_secret_123" not in text
    assert "RAZORPAY_WEBHOOK_SECRET" not in text


def test_22_management_reprocess_policy_enforcement(api_client):
    response = api_client.post("/api/v1/operations/payments/pay_reprocess_100/reprocess")
    assert response.status_code == 200
    data = response.json()
    assert data["payment_id"] == "pay_reprocess_100"
    assert "policy_decision" in data
    assert "trace_id" in data


def test_23_management_endpoint_cannot_bypass_policy_engine(api_client):
    # Attempts reprocess on a payment; must result in a valid trace with policy decision
    response = api_client.post("/api/v1/operations/payments/pay_reprocess_200/reprocess")
    assert response.status_code == 200
    data = response.json()
    assert data["policy_decision"] in ("APPROVED", "BLOCKED", "ESCALATE_TO_HUMAN")


def test_24_escalation_endpoint(api_client):
    response = api_client.post("/api/v1/operations/payments/pay_esc_100/escalate")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ESCALATED_TO_HUMAN"
