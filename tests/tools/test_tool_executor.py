"""
Unit and Security Tests for ToolExecutor Infrastructure

Verifies authorization checks, token validation, decision binding, idempotency,
and mandatory policy bypass / token forgery protection.
"""

import pytest
from domain.entities.payment import Payment, PaymentStatus
from domain.enums import RecoveryActionType
from domain.exceptions import PolicyViolationError
from domain.values.money import Money
from policies.engine import PolicyEngine
from policies.models import CandidateAction, PolicyContext, PolicyDecision
from policies.tokens import generate_approval_token
from tools.executor import ToolExecutor
from tools.idempotency import IdempotencyStore


def test_executor_valid_token_executes_tool():
    engine = PolicyEngine()
    executor = ToolExecutor()

    action = CandidateAction(
        opportunity_id="opp_exec_1",
        payment_id="pay_exec_1",
        merchant_id="mer_1",
        action_type=RecoveryActionType.SMART_RETRY,
        expected_recovery_value=Money(amount_minor=50000),
        agent_confidence=0.95,
        idempotency_key="idempotent_exec_1",
    )
    payment = Payment(
        id="pay_exec_1",
        order_id="order_1",
        merchant_id="mer_1",
        customer_id="cust_1",
        amount=Money(amount_minor=50000),
        status=PaymentStatus.FAILED,
    )

    decision = engine.evaluate(action, PolicyContext(payment=payment))

    assert decision.decision == "APPROVED"
    assert decision.approval_token is not None

    result = executor.execute_action(action, decision, decision.approval_token)

    assert result.status == "SIMULATED_SUCCESS"
    assert result.tool_name == "smart_retry"
    assert result.payment_id == "pay_exec_1"


def test_executor_missing_token_rejected():
    executor = ToolExecutor()
    action = CandidateAction(
        opportunity_id="opp_exec_2",
        payment_id="pay_exec_2",
        merchant_id="mer_1",
        action_type=RecoveryActionType.SMART_RETRY,
        expected_recovery_value=Money(amount_minor=50000),
        agent_confidence=0.95,
        idempotency_key="idempotent_exec_2",
    )
    # Manually construct APPROVED decision without approval_token
    decision = PolicyDecision(
        decision_id="dec_fake",
        action_id=action.id,
        opportunity_id=action.opportunity_id,
        payment_id=action.payment_id,
        decision="APPROVED",
        policy_version="v1.0",
        reason="Fake approval",
        approval_token=None,
    )

    with pytest.raises(PolicyViolationError) as exc_info:
        executor.execute_action(action, decision, approval_token=None)

    assert "Missing PolicyApprovalToken" in str(exc_info.value)


def test_executor_unapproved_decision_rejected():
    executor = ToolExecutor()
    action = CandidateAction(
        opportunity_id="opp_exec_3",
        payment_id="pay_exec_3",
        merchant_id="mer_1",
        action_type=RecoveryActionType.SMART_RETRY,
        expected_recovery_value=Money(amount_minor=50000),
        agent_confidence=0.95,
        idempotency_key="idempotent_exec_3",
    )
    decision = PolicyDecision(
        decision_id="dec_blocked",
        action_id=action.id,
        opportunity_id=action.opportunity_id,
        payment_id=action.payment_id,
        decision="BLOCKED",
        policy_version="v1.0",
        reason="Blocked by POL_001",
        approval_token=None,
    )

    with pytest.raises(PolicyViolationError) as exc_info:
        executor.execute_action(action, decision, approval_token=None)

    assert "not APPROVED" in str(exc_info.value)


def test_executor_idempotency_replay_safely():
    engine = PolicyEngine()
    store = IdempotencyStore()
    executor = ToolExecutor(idempotency_store=store)

    action = CandidateAction(
        opportunity_id="opp_exec_4",
        payment_id="pay_exec_4",
        merchant_id="mer_1",
        action_type=RecoveryActionType.SMART_RETRY,
        expected_recovery_value=Money(amount_minor=50000),
        agent_confidence=0.95,
        idempotency_key="idempotent_exec_4",
    )
    payment = Payment(
        id="pay_exec_4",
        order_id="order_4",
        merchant_id="mer_1",
        customer_id="cust_4",
        amount=Money(amount_minor=50000),
        status=PaymentStatus.FAILED,
    )
    decision = engine.evaluate(action, PolicyContext(payment=payment))

    # First execution succeeds
    result1 = executor.execute_action(action, decision)
    assert result1.status == "SIMULATED_SUCCESS"

    # Second execution with same idempotency key returns DUPLICATE status safely
    result2 = executor.execute_action(action, decision)
    assert result2.status == "DUPLICATE"
    assert "already been executed" in result2.payload["message"]


def test_policy_bypass_attack_prevented():
    """
    MANDATORY SECURITY TEST (Section 21):
    Proves that an attacker or future LLM cannot bypass the policy layer.
    A policy-violating action (e.g. on a CAPTURED payment) yields BLOCKED, no token,
    and executor execution attempts raise PolicyViolationError. Zero side-effects occur.
    """
    engine = PolicyEngine()
    executor = ToolExecutor()

    # Attacker proposes retry on a payment that is already CAPTURED
    action_violating_policy = CandidateAction(
        opportunity_id="opp_attack",
        payment_id="pay_captured_attack",
        merchant_id="mer_1",
        action_type=RecoveryActionType.SMART_RETRY,
        expected_recovery_value=Money(amount_minor=50000),
        agent_confidence=0.95,
        idempotency_key="idempotent_attack_1",
    )
    captured_payment = Payment(
        id="pay_captured_attack",
        order_id="order_attack",
        merchant_id="mer_1",
        customer_id="cust_attack",
        amount=Money(amount_minor=50000),
        status=PaymentStatus.CAPTURED,
    )

    decision = engine.evaluate(action_violating_policy, PolicyContext(payment=captured_payment))

    assert decision.decision == "BLOCKED"
    assert decision.approval_token is None

    with pytest.raises(PolicyViolationError) as exc_info:
        executor.execute_action(action_violating_policy, decision, decision.approval_token)

    assert "not APPROVED" in str(exc_info.value)


def test_forged_approval_token_rejected():
    """
    MANDATORY POLICY BYPASS TEST (Section 22):
    Proves that an attacker constructing a fake or copied PolicyApprovalToken is rejected.
    Executor detects invalid signature or context mismatch, tool is NEVER invoked.
    """
    executor = ToolExecutor()

    action = CandidateAction(
        opportunity_id="opp_forged",
        payment_id="pay_forged_target",
        merchant_id="mer_1",
        action_type=RecoveryActionType.SMART_RETRY,
        expected_recovery_value=Money(amount_minor=50000),
        agent_confidence=0.95,
        idempotency_key="idempotent_forged_key",
    )

    # Fake decision constructed by attacker claiming APPROVED
    fake_decision = PolicyDecision(
        decision_id="dec_fake_hacked",
        action_id=action.id,
        opportunity_id=action.opportunity_id,
        payment_id=action.payment_id,
        decision="APPROVED",
        policy_version="v1.0",
        reason="Fake approval claimed by attacker",
        approval_token=None,
    )

    # Forged approval token generated with wrong secret or mismatched fields
    forged_token = generate_approval_token(
        decision_id="dec_fake_hacked",
        opportunity_id=action.opportunity_id,
        payment_id=action.payment_id,
        action_id=action.id,
        action_type=str(action.action_type),
        idempotency_key=action.idempotency_key,
        secret="WRONG_FORGED_SECRET_KEY",  # Incorrect secret
    )

    with pytest.raises(PolicyViolationError) as exc_info:
        executor.execute_action(action, fake_decision, approval_token=forged_token)

    assert "signature verification failed" in str(exc_info.value)
