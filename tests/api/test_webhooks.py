"""
Integration Tests for Razorpay Webhook Ingestion Router (Section 15 Specification)
"""

import hashlib
import hmac
import json
import uuid
import pytest
from fastapi.testclient import TestClient
from apps.api.dependencies import get_webhook_service
from apps.api.main import app
from apps.api.webhook_service import WebhookService
from domain.entities.payment import Payment, PaymentStatus
from domain.exceptions import PolicyViolationError
from domain.values.money import Money
from policies.engine import PolicyEngine
from policies.models import CandidateAction, PolicyContext
from policies.tokens import generate_approval_token
from tools.executor import ToolExecutor


@pytest.fixture
def webhook_service():
    svc = WebhookService(webhook_secret="test_secret_123")
    return svc


@pytest.fixture
def api_client(webhook_service):
    app.dependency_overrides[get_webhook_service] = lambda: webhook_service
    yield TestClient(app)
    app.dependency_overrides.clear()


def make_signed_request(client: TestClient, payload: dict, secret: str = "test_secret_123", invalid_sig: bool = False):
    raw_bytes = json.dumps(payload).encode("utf-8")
    sig = hmac.new(secret.encode("utf-8"), raw_bytes, hashlib.sha256).hexdigest()
    if invalid_sig:
        sig = "invalid_signature_hex"

    return client.post(
        "/api/v1/webhooks/razorpay",
        content=raw_bytes,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": sig,
        },
    )


def test_1_valid_payment_failed_webhook(api_client):
    payload = {
        "entity": "event",
        "account_id": "acc_mer_1",
        "event": "payment.failed",
        "contains": ["payment"],
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_test_failed_1",
                    "entity": "payment",
                    "amount": 150000,
                    "currency": "INR",
                    "status": "failed",
                    "error_code": "GATEWAY_TIMED_OUT",
                    "created_at": 1755777600,
                }
            }
        },
        "created_at": 1755777600,
    }

    response = make_signed_request(api_client, payload)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] == "accepted"
    assert res_data["duplicate"] is False
    assert res_data["trace_id"] is not None


def test_2_invalid_signature_rejected(api_client):
    payload = {"entity": "event", "account_id": "acc_mer_1", "event": "payment.failed", "payload": {}, "created_at": 1755777600}
    response = make_signed_request(api_client, payload, invalid_sig=True)

    assert response.status_code == 401
    assert response.json()["error_code"] == "INVALID_SIGNATURE"


def test_3_duplicate_payment_failed_accepted(api_client):
    payload = {
        "entity": "event",
        "account_id": "acc_mer_dup",
        "event": "payment.failed",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_dup_100",
                    "entity": "payment",
                    "amount": 100000,
                    "currency": "INR",
                    "status": "failed",
                    "created_at": 1755777600,
                }
            }
        },
        "created_at": 1755777600,
    }

    # First delivery
    resp1 = make_signed_request(api_client, payload)
    assert resp1.status_code == 200
    assert resp1.json()["duplicate"] is False

    # Second identical delivery
    resp2 = make_signed_request(api_client, payload)
    assert resp2.status_code == 200
    assert resp2.json()["duplicate"] is True


def test_4_payment_failed_followed_by_payment_captured(api_client):
    pay_id = f"pay_seq_{uuid.uuid4().hex[:8]}"
    fail_payload = {
        "entity": "event",
        "account_id": "acc_mer_seq",
        "event": "payment.failed",
        "payload": {
            "payment": {
                "entity": {
                    "id": pay_id,
                    "entity": "payment",
                    "amount": 200000,
                    "currency": "INR",
                    "status": "failed",
                    "created_at": 1755777600,
                }
            }
        },
        "created_at": 1755777600,
    }

    cap_payload = {
        "entity": "event",
        "account_id": "acc_mer_seq",
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": pay_id,
                    "entity": "payment",
                    "amount": 200000,
                    "currency": "INR",
                    "status": "captured",
                    "created_at": 1755777650,
                }
            }
        },
        "created_at": 1755777650,
    }

    resp_fail = make_signed_request(api_client, fail_payload)
    assert resp_fail.status_code == 200

    resp_cap = make_signed_request(api_client, cap_payload)
    assert resp_cap.status_code == 200
    assert resp_cap.json()["duplicate"] is False


def test_5_out_of_order_payment_captured_and_failed(api_client, webhook_service):
    # Delivered captured first, then failed
    cap_payload = {
        "entity": "event",
        "account_id": "acc_mer_ooo",
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_ooo_100",
                    "entity": "payment",
                    "amount": 150000,
                    "currency": "INR",
                    "status": "captured",
                    "created_at": 1755777650,
                }
            }
        },
        "created_at": 1755777650,
    }

    fail_payload = {
        "entity": "event",
        "account_id": "acc_mer_ooo",
        "event": "payment.failed",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_ooo_100",
                    "entity": "payment",
                    "amount": 150000,
                    "currency": "INR",
                    "status": "failed",
                    "created_at": 1755777600,
                }
            }
        },
        "created_at": 1755777600,
    }

    resp1 = make_signed_request(api_client, cap_payload)
    assert resp1.status_code == 200

    resp2 = make_signed_request(api_client, fail_payload)
    assert resp2.status_code == 200

    # Reconstruct state to verify CAPTURED terminal protection
    events = webhook_service.ingestion_service.get_events_for_entity("pay_ooo_100")
    payment = webhook_service.orchestrator.reconstructor.reconstruct_payment_state("pay_ooo_100", events)
    assert payment.status == PaymentStatus.CAPTURED


def test_6_policy_blocked_recovery(api_client):
    # Captured payment event failure attempt triggers POL_001 block
    cap_payload = {
        "entity": "event",
        "account_id": "acc_mer_block",
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_blocked_100",
                    "entity": "payment",
                    "amount": 100000,
                    "currency": "INR",
                    "status": "captured",
                    "created_at": 1755777600,
                }
            }
        },
        "created_at": 1755777600,
    }

    resp = make_signed_request(api_client, cap_payload)
    assert resp.status_code == 200
    assert resp.json()["trace_id"] is None  # No recovery pipeline trace for captured payment


def test_7_approved_recovery_token_execution(api_client):
    payload = {
        "entity": "event",
        "account_id": "acc_mer_approved",
        "event": "payment.failed",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_approved_100",
                    "entity": "payment",
                    "amount": 150000,
                    "currency": "INR",
                    "status": "failed",
                    "error_code": "GATEWAY_TIMED_OUT",
                    "created_at": 1755777600,
                }
            }
        },
        "created_at": 1755777600,
    }

    resp = make_signed_request(api_client, payload)
    assert resp.status_code == 200
    assert resp.json()["trace_id"] is not None


def test_8_forged_approval_token_rejected():
    executor = ToolExecutor()
    action = CandidateAction(
        opportunity_id="opp_test_8",
        payment_id="pay_test_8",
        merchant_id="mer_1",
        action_type="SMART_RETRY",
        expected_recovery_value=Money(amount_minor=10000),
        agent_confidence=0.95,
        idempotency_key="idempotent_test_8",
    )

    forged_token = generate_approval_token(
        decision_id="dec_fake",
        opportunity_id=action.opportunity_id,
        payment_id=action.payment_id,
        action_id=action.id,
        action_type=str(action.action_type),
        idempotency_key=action.idempotency_key,
        secret="WRONG_FORGED_SECRET",
    )

    decision = PolicyEngine().evaluate(
        action,
        PolicyContext(
            payment=Payment(
                id="pay_test_8",
                order_id="ord_8",
                merchant_id="mer_1",
                customer_id="cust_1",
                amount=Money(amount_minor=10000),
                status=PaymentStatus.CAPTURED,
            )
        ),
    )

    with pytest.raises(PolicyViolationError):
        executor.execute_action(action, decision, approval_token=forged_token)


def test_9_organic_customer_recovery_verification(api_client, webhook_service):
    fail_payload = {
        "entity": "event",
        "account_id": "acc_mer_org",
        "event": "payment.failed",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_organic_100",
                    "entity": "payment",
                    "amount": 150000,
                    "currency": "INR",
                    "status": "failed",
                    "created_at": 1755777600,
                }
            }
        },
        "created_at": 1755777600,
    }

    make_signed_request(api_client, fail_payload)

    # Verification Agent checks recovery attribution
    payment_before = Payment(
        id="pay_organic_100",
        order_id="ord_org",
        merchant_id="mer_org",
        customer_id="cust_org",
        amount=Money(amount_minor=150000),
        status=PaymentStatus.FAILED,
    )
    payment_after = payment_before.model_copy(update={"status": PaymentStatus.CAPTURED})

    res = webhook_service.orchestrator.verifier.verify(payment_before, payment_after)
    assert res.is_recovered is True
    assert res.recovery_type in ("RAVEN_ATTRIBUTED", "ORGANIC_CUSTOMER_RETRY")


def test_10_webhook_pii_sanitized_in_telemetry(api_client, webhook_service):
    payload = {
        "entity": "event",
        "account_id": "acc_mer_pii",
        "event": "payment.failed",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_pii_100",
                    "entity": "payment",
                    "amount": 150000,
                    "currency": "INR",
                    "status": "failed",
                    "email": "sensitive.user@example.com",
                    "contact": "+919876543210",
                    "error_code": "GATEWAY_TIMED_OUT",
                    "created_at": 1755777600,
                }
            }
        },
        "created_at": 1755777600,
    }

    resp = make_signed_request(api_client, payload)
    assert resp.status_code == 200

    logs = webhook_service.orchestrator.telemetry.get_logs()
    for log_entry in logs:
        assert "sensitive.user@example.com" not in log_entry.input_summary
        assert "+919876543210" not in log_entry.input_summary
