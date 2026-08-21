"""
RAVEN Phase 12 Security Test Suite: Adaptive Scorer & Security Invariants

Verifies that Adaptive Recovery Scorer cannot execute tools, mint tokens, or bypass PolicyEngine vetoes.
"""

from domain.entities.payment import Payment
from domain.enums import PaymentStatus, RecoveryActionType
from domain.values.money import Money
from ml.adaptive.scorer import AdaptiveRecoveryScorer
from policies.engine import PolicyEngine
from policies.models import CandidateAction, PolicyContext


def test_1_adaptive_scorer_cannot_execute_tools_or_mint_tokens() -> None:
    """Proves AdaptiveRecoveryScorer has no tool execution or token minting methods."""
    scorer = AdaptiveRecoveryScorer()
    assert not hasattr(scorer, "execute_tool")
    assert not hasattr(scorer, "mint_token")
    assert not hasattr(scorer, "issue_token")


def test_2_policy_engine_vetoes_high_probability_action() -> None:
    """Proves PolicyEngine vetoes an action with 0.99 predicted success probability if POL_001 triggers."""
    engine = PolicyEngine()

    action = CandidateAction(
        opportunity_id="opp_high_prob",
        payment_id="pay_captured_high_prob",
        merchant_id="mer_1",
        action_type=RecoveryActionType.SMART_RETRY,
        expected_recovery_value=Money(100000, "INR"),
        agent_confidence=0.99,  # High adaptive probability
        idempotency_key="idempotent_test_01",
    )

    # Payment in CAPTURED status triggers POL_001 (terminal state guard)
    payment = Payment(
        id="pay_captured_high_prob",
        order_id="ord_1",
        merchant_id="mer_1",
        customer_id="cust_1",
        amount=Money(100000, "INR"),
        status=PaymentStatus.CAPTURED,
    )

    ctx = PolicyContext(payment=payment)
    result = engine.evaluate(action, ctx)

    assert result.decision == "BLOCKED"
    assert result.blocked_by_policy_id == "POL_001"
    assert result.approval_token is None
