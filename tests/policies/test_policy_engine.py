"""
Unit and Behavioral Tests for RAVEN Deterministic Policy Engine (POL_001 through POL_007)
"""

from datetime import datetime, timezone
from domain.entities.customer import Customer, CustomerCommunicationPreferences
from domain.entities.payment import Payment, PaymentStatus
from domain.enums import RecoveryActionType
from domain.values.money import Money
from policies.engine import PolicyEngine
from policies.models import CandidateAction, PolicyContext


def test_pol_001_captured_payment_guard_blocks():
    engine = PolicyEngine()
    action = CandidateAction(
        opportunity_id="opp_1",
        payment_id="pay_captured_1",
        merchant_id="mer_1",
        action_type=RecoveryActionType.SMART_RETRY,
        expected_recovery_value=Money(amount_minor=10000),
        agent_confidence=0.90,
        idempotency_key="idempotent_key_1",
    )
    payment = Payment(
        id="pay_captured_1",
        order_id="order_1",
        merchant_id="mer_1",
        customer_id="cust_1",
        amount=Money(amount_minor=10000),
        status=PaymentStatus.CAPTURED,
    )
    context = PolicyContext(payment=payment)

    decision = engine.evaluate(action, context)

    assert decision.decision == "BLOCKED"
    assert decision.blocked_by_policy_id == "POL_001"
    assert decision.approval_token is None


def test_pol_002_ambiguous_state_isolation_escalates():
    engine = PolicyEngine()
    action = CandidateAction(
        opportunity_id="opp_2",
        payment_id="pay_ambig_2",
        merchant_id="mer_1",
        action_type=RecoveryActionType.SMART_RETRY,
        expected_recovery_value=Money(amount_minor=10000),
        agent_confidence=0.90,
        idempotency_key="idempotent_key_2",
    )
    payment = Payment(
        id="pay_ambig_2",
        order_id="order_2",
        merchant_id="mer_1",
        customer_id="cust_2",
        amount=Money(amount_minor=10000),
        status=PaymentStatus.AMBIGUOUS,
    )
    context = PolicyContext(payment=payment)

    decision = engine.evaluate(action, context)

    assert decision.decision == "ESCALATE_TO_HUMAN"
    assert decision.blocked_by_policy_id == "POL_002"
    assert decision.approval_token is None


def test_pol_003_max_recovery_attempt_cap_blocks():
    engine = PolicyEngine()
    action = CandidateAction(
        opportunity_id="opp_3",
        payment_id="pay_failed_3",
        merchant_id="mer_1",
        action_type=RecoveryActionType.SMART_RETRY,
        expected_recovery_value=Money(amount_minor=10000),
        agent_confidence=0.90,
        idempotency_key="idempotent_key_3",
    )
    payment = Payment(
        id="pay_failed_3",
        order_id="order_3",
        merchant_id="mer_1",
        customer_id="cust_3",
        amount=Money(amount_minor=10000),
        status=PaymentStatus.FAILED,
    )
    context = PolicyContext(payment=payment, attempts_count=3, max_recovery_attempts=3)

    decision = engine.evaluate(action, context)

    assert decision.decision == "BLOCKED"
    assert decision.blocked_by_policy_id == "POL_003"
    assert decision.approval_token is None


def test_pol_004_high_value_boundary_escalates():
    engine = PolicyEngine()
    action = CandidateAction(
        opportunity_id="opp_4",
        payment_id="pay_highval_4",
        merchant_id="mer_1",
        action_type=RecoveryActionType.SMART_RETRY,
        expected_recovery_value=Money(amount_minor=1500000),  # ₹15,000 > ₹10,000 threshold
        agent_confidence=0.90,
        idempotency_key="idempotent_key_4",
    )
    payment = Payment(
        id="pay_highval_4",
        order_id="order_4",
        merchant_id="mer_1",
        customer_id="cust_4",
        amount=Money(amount_minor=1500000),
        status=PaymentStatus.FAILED,
    )
    context = PolicyContext(payment=payment, high_value_threshold_minor=1000000)

    decision = engine.evaluate(action, context)

    assert decision.decision == "ESCALATE_TO_HUMAN"
    assert decision.blocked_by_policy_id == "POL_004"
    assert decision.approval_token is None


def test_pol_005_low_confidence_threshold_escalates():
    engine = PolicyEngine()
    action = CandidateAction(
        opportunity_id="opp_5",
        payment_id="pay_lowconf_5",
        merchant_id="mer_1",
        action_type=RecoveryActionType.SMART_RETRY,
        expected_recovery_value=Money(amount_minor=10000),
        agent_confidence=0.60,  # 0.60 < 0.75 threshold
        idempotency_key="idempotent_key_5",
    )
    payment = Payment(
        id="pay_lowconf_5",
        order_id="order_5",
        merchant_id="mer_1",
        customer_id="cust_5",
        amount=Money(amount_minor=10000),
        status=PaymentStatus.FAILED,
    )
    context = PolicyContext(payment=payment, min_confidence_threshold=0.75)

    decision = engine.evaluate(action, context)

    assert decision.decision == "ESCALATE_TO_HUMAN"
    assert decision.blocked_by_policy_id == "POL_005"
    assert decision.approval_token is None


def test_pol_006_customer_opt_out_and_message_cap_blocks():
    engine = PolicyEngine()
    action = CandidateAction(
        opportunity_id="opp_6",
        payment_id="pay_optout_6",
        merchant_id="mer_1",
        customer_id="cust_6",
        action_type=RecoveryActionType.PAYMENT_LINK_DISPATCH,
        expected_recovery_value=Money(amount_minor=10000),
        agent_confidence=0.90,
        idempotency_key="idempotent_key_6",
    )
    payment = Payment(
        id="pay_optout_6",
        order_id="order_6",
        merchant_id="mer_1",
        customer_id="cust_6",
        amount=Money(amount_minor=10000),
        status=PaymentStatus.FAILED,
    )
    customer = Customer(
        id="cust_6",
        merchant_id="mer_1",
        email="test@domain.com",
        phone="+919876543210",
        name="Test OptOut",
        communication_preferences=CustomerCommunicationPreferences(opt_out=True),
    )
    context = PolicyContext(payment=payment, customer=customer)

    decision = engine.evaluate(action, context)

    assert decision.decision == "BLOCKED"
    assert decision.blocked_by_policy_id == "POL_006"
    assert decision.approval_token is None


def test_pol_007_systemic_bank_downtime_blocks():
    engine = PolicyEngine()
    action = CandidateAction(
        opportunity_id="opp_7",
        payment_id="pay_downtime_7",
        merchant_id="mer_1",
        action_type=RecoveryActionType.SMART_RETRY,
        expected_recovery_value=Money(amount_minor=10000),
        agent_confidence=0.90,
        idempotency_key="idempotent_key_7",
    )
    payment = Payment(
        id="pay_downtime_7",
        order_id="order_7",
        merchant_id="mer_1",
        customer_id="cust_7",
        amount=Money(amount_minor=10000),
        status=PaymentStatus.FAILED,
    )
    context = PolicyContext(payment=payment, bank_downtime_rate=0.50)  # 50% > 40% threshold

    decision = engine.evaluate(action, context)

    assert decision.decision == "BLOCKED"
    assert decision.blocked_by_policy_id == "POL_007"
    assert decision.approval_token is None


def test_valid_action_approved_generates_token():
    engine = PolicyEngine()
    action = CandidateAction(
        opportunity_id="opp_valid",
        payment_id="pay_valid_100",
        merchant_id="mer_1",
        action_type=RecoveryActionType.SMART_RETRY,
        expected_recovery_value=Money(amount_minor=50000),
        agent_confidence=0.95,
        idempotency_key="idempotent_valid_100",
    )
    payment = Payment(
        id="pay_valid_100",
        order_id="order_100",
        merchant_id="mer_1",
        customer_id="cust_100",
        amount=Money(amount_minor=50000),
        status=PaymentStatus.FAILED,
    )
    context = PolicyContext(payment=payment)

    decision = engine.evaluate(action, context)

    assert decision.decision == "APPROVED"
    assert decision.blocked_by_policy_id is None
    assert decision.approval_token is not None
    assert decision.approval_token.payment_id == "pay_valid_100"
    assert decision.approval_token.action_id == action.id


def test_policy_engine_determinism():
    engine = PolicyEngine()
    action = CandidateAction(
        opportunity_id="opp_det",
        payment_id="pay_det",
        merchant_id="mer_1",
        action_type=RecoveryActionType.SMART_RETRY,
        expected_recovery_value=Money(amount_minor=50000),
        agent_confidence=0.95,
        idempotency_key="idempotent_det",
    )
    payment = Payment(
        id="pay_det",
        order_id="order_det",
        merchant_id="mer_1",
        customer_id="cust_det",
        amount=Money(amount_minor=50000),
        status=PaymentStatus.FAILED,
    )
    context = PolicyContext(payment=payment)
    eval_time = datetime(2026, 8, 21, 12, 0, 0, tzinfo=timezone.utc)

    decision1 = engine.evaluate(action, context, evaluated_at=eval_time)
    decision2 = engine.evaluate(action, context, evaluated_at=eval_time)

    assert decision1.decision == decision2.decision == "APPROVED"
    assert decision1.reason == decision2.reason
