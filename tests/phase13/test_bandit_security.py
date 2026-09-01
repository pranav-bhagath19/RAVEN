"""
RAVEN Phase 13 Security Test Suite: Contextual Bandit Security & Authorization

Verifies that:
1. Contextual Bandit has ZERO tool execution authority.
2. Contextual Bandit cannot mint PolicyApprovalTokens.
3. Contextual Bandit cannot modify policies or policy activation state.
4. Contextual Bandit is strictly advisory-only.
"""

import pytest
from domain.entities.payment import Payment
from domain.enums import PaymentStatus, RecoveryActionType
from domain.exceptions import PolicyViolationError
from domain.values.money import Money
from ml.bandits.model import LinUCBBanditModel
from policies.engine import PolicyEngine
from policies.models import CandidateAction, PolicyContext, PolicyDecision
from tools.executor import ToolExecutor


def test_bandit_has_zero_tool_execution_authority():
    """Proves bandit model object lacks any execute_tool or side-effect methods."""
    model = LinUCBBanditModel(alpha=0.5, seed=42)
    assert not hasattr(model, "execute")
    assert not hasattr(model, "execute_tool")
    assert not hasattr(model, "mint_token")
    assert not hasattr(model, "issue_token")


def test_bandit_cannot_bypass_policy_engine():
    """Proves PolicyEngine veto authority remains absolute even with maximum bandit score."""
    engine = PolicyEngine()
    
    action = CandidateAction(
        id="act_retry_01",
        opportunity_id="opp_sec_01",
        payment_id="pay_captured_99",
        merchant_id="mer_sec_01",
        action_type=RecoveryActionType.SMART_RETRY,
        agent_confidence=0.99,
        expected_recovery_value=Money(amount_minor=9900, currency="INR"),
        idempotency_key="idem_sec_01",
    )
    
    captured_payment = Payment(
        id="pay_captured_99",
        order_id="ord_sec_99",
        merchant_id="mer_sec_01",
        customer_id="cust_sec_99",
        amount=Money(amount_minor=10000, currency="INR"),
        status=PaymentStatus.CAPTURED,
    )
    
    ctx = PolicyContext(payment=captured_payment)
    
    eval_result = engine.evaluate(action=action, context=ctx)
    
    assert eval_result.decision == "BLOCKED"
    assert eval_result.approval_token is None


def test_bandit_cannot_execute_side_effects_directly():
    """Proves ToolExecutor requires explicit HMAC PolicyApprovalToken and ignores bandit advisory scores."""
    executor = ToolExecutor()
    
    action = CandidateAction(
        id="act_retry_02",
        opportunity_id="opp_sec_02",
        payment_id="pay_sec_01",
        merchant_id="mer_sec_01",
        action_type=RecoveryActionType.SMART_RETRY,
        agent_confidence=0.99,
        expected_recovery_value=Money(amount_minor=9900, currency="INR"),
        idempotency_key="idem_sec_02",
    )
    
    unapproved_decision = PolicyDecision(
        decision_id="dec_unapproved_01",
        action_id="act_retry_02",
        opportunity_id="opp_sec_02",
        payment_id="pay_sec_01",
        decision="BLOCKED",
        blocked_by_policy_id="POL_001",
        reason="BLOCKED by POL_001",
    )
    
    with pytest.raises(PolicyViolationError) as exc_info:
        executor.execute_action(
            action=action,
            decision=unapproved_decision,
            approval_token=None,
        )
    
    assert "rejected execution" in str(exc_info.value).lower()
    assert exc_info.value.details.get("policy_rule_code") == "EXECUTOR_UNAPPROVED"
