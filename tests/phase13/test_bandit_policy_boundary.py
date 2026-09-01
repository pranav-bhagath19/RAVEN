"""
RAVEN Phase 13 Security Test Suite: Policy Boundary & Invariance Test

Explicitly proves section 13 requirement:
P(success) = 0.99 AND bandit_score = extremely high AND action = POL_001 blocked action
MUST result in:
decision = BLOCKED
AND no PolicyApprovalToken
AND no ToolExecutor execution
AND no external side effect.
"""

import pytest
from domain.entities.payment import Payment
from domain.enums import PaymentStatus, RecoveryActionType
from domain.exceptions import PolicyViolationError
from domain.values.money import Money
from policies.engine import PolicyEngine
from policies.models import CandidateAction, PolicyContext
from tools.executor import ToolExecutor


def test_bandit_policy_boundary_absolute_veto():
    """
    Mandatory Section 13 security test.
    """
    engine = PolicyEngine()
    executor = ToolExecutor()

    # POL_001 blocked scenario: Payment already captured
    action = CandidateAction(
        id="act_high_score_01",
        opportunity_id="opp_boundary_01",
        payment_id="pay_captured_already",
        merchant_id="mer_boundary_01",
        action_type=RecoveryActionType.SMART_RETRY,
        agent_confidence=0.99,
        expected_recovery_value=Money(amount_minor=198000, currency="INR"),
        idempotency_key="idem_boundary_01",
    )

    captured_payment = Payment(
        id="pay_captured_already",
        order_id="ord_b1",
        merchant_id="mer_boundary_01",
        customer_id="cust_b1",
        amount=Money(amount_minor=200000, currency="INR"),
        status=PaymentStatus.CAPTURED,
    )

    ctx = PolicyContext(payment=captured_payment)

    # Evaluate action with PolicyEngine
    policy_decision = engine.evaluate(action=action, context=ctx)

    # ASSERTIONS:
    # 1. Decision MUST be BLOCKED
    assert policy_decision.decision == "BLOCKED"

    # 2. NO PolicyApprovalToken issued
    assert policy_decision.approval_token is None

    # 3. ToolExecutor execution MUST raise PolicyViolationError if attempted on unapproved decision
    with pytest.raises(PolicyViolationError) as exc_info:
        executor.execute_action(
            action=action,
            decision=policy_decision,
            approval_token=policy_decision.approval_token,
        )

    assert "rejected execution" in str(exc_info.value).lower()
    assert exc_info.value.details.get("policy_rule_code") == "EXECUTOR_UNAPPROVED"
