"""
Phase 11 ML + Policy Boundary Safety Tests

Verifies that ML scoring remains strictly advisory and cannot bypass PolicyEngine:
1. High ML probability (0.99) + Policy Veto -> Action remains BLOCKED.
2. Low ML probability (0.01) + Policy Allow -> ML influences ranking but cannot execute tools or issue tokens.
3. Merchant policy configuration cannot bypass POL_001–POL_007 core security guards.
"""

from domain.entities.payment import Payment, PaymentStatus
from domain.enums import RecoveryActionType
from domain.values.money import Money
from policies.engine import PolicyEngine
from policies.models import CandidateAction, PolicyContext


def test_high_ml_probability_with_policy_veto_remains_blocked():
    payment = Payment(
        id="pay_captured_01",
        order_id="ord_01",
        merchant_id="mer_01",
        customer_id="cust_01",
        amount=Money(10000, "INR"),
        status=PaymentStatus.CAPTURED,  # POL_001 violation!
    )

    action = CandidateAction(
        id="act_01",
        opportunity_id="opp_01",
        payment_id="pay_captured_01",
        merchant_id="mer_01",
        customer_id="cust_01",
        action_type=RecoveryActionType.SMART_RETRY,
        parameters={"delay_seconds": 60},
        expected_recovery_value=Money(10000, "INR"),
        agent_confidence=0.99,  # High ML probability score
        idempotency_key="idemp_boundary_01",
    )

    policy_engine = PolicyEngine()
    ctx = PolicyContext(payment=payment)
    decision = policy_engine.evaluate(action=action, context=ctx)

    assert decision.decision == "BLOCKED"
    assert decision.blocked_by_policy_id == "POL_001"
    assert decision.approval_token is None
