"""
Integration & Hardening Tests for RAVEN Phase 8 Production Prep (Step 19 Specification)
"""

from fastapi.testclient import TestClient
from apps.api.config import get_settings
from apps.api.main import app
from scripts.demo import run_raven_demo
from scripts.security_demo import run_security_demo

client = TestClient(app)


def test_1_config_loading_and_sanitization():
    settings = get_settings()
    assert settings.environment in ("development", "demo", "production")
    sanitized = settings.sanitize_dict()
    assert sanitized["razorpay_key_secret"] == "[REDACTED]"
    assert sanitized["razorpay_webhook_secret"] == "[REDACTED]"
    assert sanitized["policy_secret"] == "[REDACTED]"


def test_2_request_id_propagation():
    response = client.get("/health")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Request-ID"].startswith("req_")


def test_3_custom_request_id_preserved():
    response = client.get("/health", headers={"X-Request-ID": "custom_req_12345"})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "custom_req_12345"


def test_4_structured_404_error_response():
    response = client.get("/api/v1/operations/payments/pay_nonexistent_999")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "PAYMENT_NOT_FOUND"
    assert "request_id" in data["error"]


def test_5_structured_422_validation_error_response():
    response = client.get("/api/v1/operations/payments?page=0")
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_6_demo_script_execution():
    # Executes the 15-scenario demo script end-to-end
    run_raven_demo()


def test_7_security_demo_execution():
    # Executes the 9-attack-vector security demo script end-to-end
    run_security_demo()


def test_8_health_liveness():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_9_readiness_probe():
    response = client.get("/api/v1/operations/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"
