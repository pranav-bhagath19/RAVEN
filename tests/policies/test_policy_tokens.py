"""
Unit and Security Tests for PolicyApprovalToken Generator and Verifier
"""

from datetime import datetime, timedelta, timezone
import pytest
from domain.exceptions import PolicyViolationError
from policies.tokens import generate_approval_token, verify_approval_token


def test_valid_token_verification_passes():
    now = datetime.now(timezone.utc)
    token = generate_approval_token(
        decision_id="dec_100",
        opportunity_id="opp_100",
        payment_id="pay_100",
        action_id="act_100",
        action_type="SMART_RETRY",
        idempotency_key="idempotent_100",
        issued_at=now,
    )

    assert verify_approval_token(
        token=token,
        expected_payment_id="pay_100",
        expected_action_id="act_100",
        expected_action_type="SMART_RETRY",
        expected_idempotency_key="idempotent_100",
        current_time=now + timedelta(seconds=10),
    )


def test_invalid_signature_rejected():
    now = datetime.now(timezone.utc)
    token = generate_approval_token(
        decision_id="dec_100",
        opportunity_id="opp_100",
        payment_id="pay_100",
        action_id="act_100",
        action_type="SMART_RETRY",
        idempotency_key="idempotent_100",
        issued_at=now,
    )

    # Tamper with token signature
    token.signature = "deadbeef" * 8

    with pytest.raises(PolicyViolationError) as exc_info:
        verify_approval_token(
            token=token,
            expected_payment_id="pay_100",
            expected_action_id="act_100",
            expected_action_type="SMART_RETRY",
            expected_idempotency_key="idempotent_100",
            current_time=now,
        )

    assert "signature verification failed" in str(exc_info.value)


def test_modified_payload_rejected():
    now = datetime.now(timezone.utc)
    token = generate_approval_token(
        decision_id="dec_100",
        opportunity_id="opp_100",
        payment_id="pay_100",
        action_id="act_100",
        action_type="SMART_RETRY",
        idempotency_key="idempotent_100",
        issued_at=now,
    )

    # Tamper with token field without updating signature
    token.payment_id = "pay_hacked_999"

    with pytest.raises(PolicyViolationError) as exc_info:
        verify_approval_token(
            token=token,
            expected_payment_id="pay_hacked_999",
            expected_action_id="act_100",
            expected_action_type="SMART_RETRY",
            expected_idempotency_key="idempotent_100",
            current_time=now,
        )

    assert "signature verification failed" in str(exc_info.value)


def test_expired_token_rejected():
    now = datetime.now(timezone.utc)
    token = generate_approval_token(
        decision_id="dec_100",
        opportunity_id="opp_100",
        payment_id="pay_100",
        action_id="act_100",
        action_type="SMART_RETRY",
        idempotency_key="idempotent_100",
        ttl_seconds=300,
        issued_at=now,
    )

    # Verification attempt 301 seconds later (expired)
    future_time = now + timedelta(seconds=301)

    with pytest.raises(PolicyViolationError) as exc_info:
        verify_approval_token(
            token=token,
            expected_payment_id="pay_100",
            expected_action_id="act_100",
            expected_action_type="SMART_RETRY",
            expected_idempotency_key="idempotent_100",
            current_time=future_time,
        )

    assert "expired" in str(exc_info.value).lower()


def test_wrong_payment_rejected():
    now = datetime.now(timezone.utc)
    token = generate_approval_token(
        decision_id="dec_100",
        opportunity_id="opp_100",
        payment_id="pay_100",
        action_id="act_100",
        action_type="SMART_RETRY",
        idempotency_key="idempotent_100",
        issued_at=now,
    )

    with pytest.raises(PolicyViolationError) as exc_info:
        verify_approval_token(
            token=token,
            expected_payment_id="pay_DIFFERENT",
            expected_action_id="act_100",
            expected_action_type="SMART_RETRY",
            expected_idempotency_key="idempotent_100",
            current_time=now,
        )

    assert "payment_id" in str(exc_info.value)


def test_wrong_action_rejected():
    now = datetime.now(timezone.utc)
    token = generate_approval_token(
        decision_id="dec_100",
        opportunity_id="opp_100",
        payment_id="pay_100",
        action_id="act_100",
        action_type="SMART_RETRY",
        idempotency_key="idempotent_100",
        issued_at=now,
    )

    with pytest.raises(PolicyViolationError) as exc_info:
        verify_approval_token(
            token=token,
            expected_payment_id="pay_100",
            expected_action_id="act_DIFFERENT",
            expected_action_type="SMART_RETRY",
            expected_idempotency_key="idempotent_100",
            current_time=now,
        )

    assert "action_id" in str(exc_info.value)


def test_wrong_action_type_rejected():
    now = datetime.now(timezone.utc)
    token = generate_approval_token(
        decision_id="dec_100",
        opportunity_id="opp_100",
        payment_id="pay_100",
        action_id="act_100",
        action_type="SMART_RETRY",
        idempotency_key="idempotent_100",
        issued_at=now,
    )

    with pytest.raises(PolicyViolationError) as exc_info:
        verify_approval_token(
            token=token,
            expected_payment_id="pay_100",
            expected_action_id="act_100",
            expected_action_type="PAYMENT_LINK_DISPATCH",
            expected_idempotency_key="idempotent_100",
            current_time=now,
        )

    assert "action_type" in str(exc_info.value)


def test_wrong_idempotency_key_rejected():
    now = datetime.now(timezone.utc)
    token = generate_approval_token(
        decision_id="dec_100",
        opportunity_id="opp_100",
        payment_id="pay_100",
        action_id="act_100",
        action_type="SMART_RETRY",
        idempotency_key="idempotent_100",
        issued_at=now,
    )

    with pytest.raises(PolicyViolationError) as exc_info:
        verify_approval_token(
            token=token,
            expected_payment_id="pay_100",
            expected_action_id="act_100",
            expected_action_type="SMART_RETRY",
            expected_idempotency_key="idempotent_DIFFERENT",
            current_time=now,
        )

    assert "idempotency_key" in str(exc_info.value)


def test_wrong_policy_version_rejected():
    now = datetime.now(timezone.utc)
    token = generate_approval_token(
        decision_id="dec_100",
        opportunity_id="opp_100",
        payment_id="pay_100",
        action_id="act_100",
        action_type="SMART_RETRY",
        idempotency_key="idempotent_100",
        policy_version="v0.9_outdated",
        issued_at=now,
    )

    with pytest.raises(PolicyViolationError) as exc_info:
        verify_approval_token(
            token=token,
            expected_payment_id="pay_100",
            expected_action_id="act_100",
            expected_action_type="SMART_RETRY",
            expected_idempotency_key="idempotent_100",
            current_time=now,
        )

    assert "policy_version" in str(exc_info.value)


def test_future_issued_token_rejected():
    now = datetime.now(timezone.utc)
    future_issued = now + timedelta(seconds=120)

    token = generate_approval_token(
        decision_id="dec_100",
        opportunity_id="opp_100",
        payment_id="pay_100",
        action_id="act_100",
        action_type="SMART_RETRY",
        idempotency_key="idempotent_100",
        issued_at=future_issued,
    )

    with pytest.raises(PolicyViolationError) as exc_info:
        verify_approval_token(
            token=token,
            expected_payment_id="pay_100",
            expected_action_id="act_100",
            expected_action_type="SMART_RETRY",
            expected_idempotency_key="idempotent_100",
            current_time=now,
        )

    assert "future" in str(exc_info.value).lower()
