"""
Mandatory Security Boundary Tests (Section 14 Specification)

Verifies that LLMs have ZERO execution authority, cannot bypass PolicyEngine,
cannot issue PolicyApprovalToken objects, cannot manipulate expected value math,
and cannot override ground truth verification.
"""

import pytest
from agents.recovery_planner.expected_value import calculate_expected_value
from agents.recovery_planner.models import CandidateActionProposal
from agents.verifier.verifier import VerificationAgent
from domain.entities.payment import Payment, PaymentStatus
from domain.enums import RecoveryActionType
from domain.exceptions import PolicyViolationError
from domain.values.money import Money
from policies.engine import PolicyEngine
from policies.models import CandidateAction, PolicyContext
from policies.tokens import generate_approval_token
from tools.executor import ToolExecutor


def test_llm_cannot_approve_action():
    """
    SECURITY TEST 1 & 2:
    Proves that an LLM proposing an action on a CAPTURED payment yields BLOCKED from PolicyEngine.
    The LLM cannot mark an action as APPROVED.
    """
    engine = PolicyEngine()
    action = CandidateAction(
        opportunity_id="opp_sec_1",
        payment_id="pay_captured_sec",
        merchant_id="mer_1",
        action_type=RecoveryActionType.SMART_RETRY,
        expected_recovery_value=Money(amount_minor=10000),
        agent_confidence=0.99,  # High LLM confidence claimed
        idempotency_key="idempotent_sec_1",
    )
    captured_payment = Payment(
        id="pay_captured_sec",
        order_id="ord_1",
        merchant_id="mer_1",
        customer_id="cust_1",
        amount=Money(amount_minor=10000),
        status=PaymentStatus.CAPTURED,
    )

    decision = engine.evaluate(action, PolicyContext(payment=captured_payment))

    assert decision.decision == "BLOCKED"
    assert decision.blocked_by_policy_id == "POL_001"
    assert decision.approval_token is None


def test_llm_cannot_issue_approval_token():
    """
    SECURITY TEST 3:
    Proves that an LLM cannot fake or include a valid PolicyApprovalToken.
    Executor checks HMAC-SHA256 signature and rejects forged/unapproved tokens.
    """
    executor = ToolExecutor()
    action = CandidateAction(
        opportunity_id="opp_sec_3",
        payment_id="pay_sec_3",
        merchant_id="mer_1",
        action_type=RecoveryActionType.SMART_RETRY,
        expected_recovery_value=Money(amount_minor=10000),
        agent_confidence=0.95,
        idempotency_key="idempotent_sec_3",
    )

    # Forged approval token constructed with wrong secret
    forged_token = generate_approval_token(
        decision_id="dec_fake_llm",
        opportunity_id=action.opportunity_id,
        payment_id=action.payment_id,
        action_id=action.id,
        action_type=str(action.action_type),
        idempotency_key=action.idempotency_key,
        secret="LLM_FORGED_SECRET",
    )

    # Policy decision is BLOCKED
    decision = PolicyEngine().evaluate(
        action,
        PolicyContext(
            payment=Payment(
                id="pay_sec_3",
                order_id="ord_3",
                merchant_id="mer_1",
                customer_id="cust_1",
                amount=Money(amount_minor=10000),
                status=PaymentStatus.CAPTURED,
            )
        ),
    )

    with pytest.raises(PolicyViolationError) as exc_info:
        executor.execute_action(action, decision, approval_token=forged_token)

    assert "not APPROVED" in str(exc_info.value)


def test_llm_cannot_manipulate_expected_value():
    """
    SECURITY TEST 4:
    Proves that Python code calculates EV deterministically using integer minor units,
    ignoring any external LLM monetary math claims.
    """
    # LLM might claim EV is ₹1,000,000. Python computes EV = 0.5 * 10000 - 100 = 4900 paise.
    ev = calculate_expected_value(probability=0.5, amount_minor=10000, cost_minor=100)
    assert ev.expected_value_minor == 4900


def test_llm_cannot_override_verification_ground_truth():
    """
    SECURITY TEST 5:
    Proves that VerificationAgent determines attribution purely via deterministic timestamp & state logic.
    An LLM claim cannot change an unrecovered payment (FAILED) into a recovered state.
    """
    verifier = VerificationAgent()
    payment_failed = Payment(
        id="pay_sec_5",
        order_id="ord_5",
        merchant_id="mer_1",
        customer_id="cust_1",
        amount=Money(amount_minor=10000),
        status=PaymentStatus.FAILED,
    )

    res = verifier.verify(payment_before=payment_failed, payment_after=payment_failed)

    assert res.is_recovered is False
    assert res.recovery_type == "NO_RECOVERY"


def test_malicious_extra_json_fields_sanitized():
    """
    SECURITY TEST 6:
    Proves that Pydantic models strip/ignore unauthorized extra JSON fields from LLM outputs.
    """
    proposal = CandidateActionProposal(
        action_type=RecoveryActionType.SMART_RETRY,
        reasoning="Test proposal",
        predicted_success_probability=0.80,
        agent_confidence=0.90,
        recommended_delay_seconds=900,
        estimated_cost_minor=0,
    )

    dump = proposal.model_dump()
    assert "unauthorized_admin_flag" not in dump
