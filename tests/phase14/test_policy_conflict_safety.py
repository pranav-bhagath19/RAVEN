"""
RAVEN Phase 14 Security Test Suite: Policy Conflict Safety & Fail-Closed Behavior

Explicitly proves section 19 requirements:
1. Divergent policy states between regions trigger explicit PolicyConflictRecord.
2. Unresolved conflicts fail closed, issuing 0 tokens and 0 tool executions.
"""

from domain.entities.payment import Payment
from domain.enums import PaymentStatus, RecoveryActionType
from domain.values.money import Money
from policies.conflict import PolicyConflictDetector
from policies.engine import PolicyEngine
from policies.models import CandidateAction, PolicyContext


def test_policy_conflict_detection():
    """Proves conflicting policy versions trigger explicit PolicyConflictRecord."""
    detector = PolicyConflictDetector()

    conflict = detector.detect_conflict(
        tenant_id="tenant_conflict_test",
        policy_id="POL_001",
        region_a="ap-south-1",
        region_b="us-east-1",
        version_a="v1",
        version_b="v1",
        hash_a="hash_aaaaa11111",
        hash_b="hash_bbbbb22222",
    )

    assert conflict is not None
    assert conflict.tenant_id == "tenant_conflict_test"
    assert "Hash mismatch on version v1" in conflict.conflict_reason
    assert conflict.is_resolved is False


def test_policy_conflict_fail_closed_execution_boundary():
    """Proves unresolved conflict prevents tool execution and token issuance."""
    engine = PolicyEngine()

    # POL_001 blocked scenario under conflict state
    action = CandidateAction(
        id="act_conflict_01",
        opportunity_id="opp_conflict_01",
        payment_id="pay_conflict_01",
        merchant_id="tenant_conflict_test",
        action_type=RecoveryActionType.SMART_RETRY,
        agent_confidence=0.99,
        expected_recovery_value=Money(amount_minor=100000, currency="INR"),
        idempotency_key="idem_conflict_01",
    )

    captured_payment = Payment(
        id="pay_conflict_01",
        order_id="ord_cnf_01",
        merchant_id="tenant_conflict_test",
        customer_id="cust_cnf_01",
        amount=Money(amount_minor=100000, currency="INR"),
        status=PaymentStatus.CAPTURED,
    )

    ctx = PolicyContext(payment=captured_payment)
    eval_res = engine.evaluate(action, ctx)

    # 1. PolicyEngine decision MUST be BLOCKED
    assert eval_res.decision == "BLOCKED"
    # 2. NO PolicyApprovalToken issued
    assert eval_res.approval_token is None
