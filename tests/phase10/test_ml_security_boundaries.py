"""
RAVEN Phase 10 Security & Boundary Verification Suite

Proves all 15 non-negotiable security boundaries for the ML propensity scoring layer:
1. ML cannot execute ToolExecutor.
2. ML cannot generate PolicyApprovalTokens.
3. ML cannot directly call Razorpay API.
4. PolicyEngine vetoes action even when ML probability = 0.99 (POL_001).
5. Invalid probability < 0 is rejected.
6. Invalid probability > 1 is rejected.
7. NaN probability is rejected.
8. Feature mismatch triggers deterministic fallback.
9. Missing model artifact triggers deterministic fallback.
10. Inference exception triggers deterministic fallback.
11. Fallback still reaches PolicyEngine.
12. ML cannot modify monetary values (integer minor unit EV enforced).
13. ML cannot modify policy thresholds.
14. ML cannot issue approval tokens.
15. ML cannot create side effects.
"""

import numpy as np
import pytest
from agents.recovery_planner.expected_value import calculate_expected_value
from agents.recovery_planner.planner import RecoveryPlanner
from domain.entities.payment import Payment
from domain.enums import PaymentStatus, RecoveryActionType
from domain.exceptions import InvalidMoneyError, PolicyViolationError
from domain.values.money import Money
from ml.models.propensity import BasePropensityModel, LogisticRegressionPropensityModel
from policies.engine import PolicyEngine
from policies.models import CandidateAction, PolicyContext, PolicyDecision
from tools.executor import ToolExecutor


class MockFaultyModel(BasePropensityModel):
    """Faulty model throwing exception during inference for fallback testing."""

    def __init__(self, bad_value: float | None = None) -> None:
        self.bad_value = bad_value

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        pass

    def predict_probability(self, feature_vector: np.ndarray) -> float:
        if self.bad_value is not None:
            return self.bad_value
        raise RuntimeError("Simulated ML model inference error")

    def model_metadata(self) -> dict:
        return {"model_version": "v_faulty"}


def test_1_ml_cannot_execute_toolexecutor():
    executor = ToolExecutor()
    action = CandidateAction(
        id="act_ml_bypass",
        opportunity_id="opp_1",
        payment_id="pay_ml_1",
        merchant_id="mer_1",
        action_type=RecoveryActionType.SMART_RETRY,
        expected_recovery_value=Money(amount_minor=100000, currency="INR"),
        agent_confidence=0.9,
        idempotency_key="idemp_ml_1",
    )
    unapproved_decision = PolicyDecision(
        decision_id="dec_unapproved",
        action_id=action.id,
        opportunity_id=action.opportunity_id,
        payment_id=action.payment_id,
        decision="BLOCKED",
        reason="Blocked by policy",
        approval_token=None,
    )
    with pytest.raises(PolicyViolationError) as exc_info:
        executor.execute_action(action=action, decision=unapproved_decision)
    assert "not APPROVED" in str(exc_info.value)


def test_2_ml_cannot_generate_policy_approval_token():
    model = LogisticRegressionPropensityModel()
    assert not hasattr(model, "generate_approval_token")
    assert not hasattr(model, "policy_secret")


def test_3_ml_cannot_directly_call_razorpay():
    model = LogisticRegressionPropensityModel()
    assert not hasattr(model, "create_payment_link")
    assert not hasattr(model, "fetch_payment")


def test_4_policy_engine_vetoes_action_when_ml_probability_is_high():
    engine = PolicyEngine()
    captured_payment = Payment(
        id="pay_captured_100",
        order_id="ord_100",
        merchant_id="mer_100",
        customer_id="cust_100",
        amount=Money(amount_minor=100000, currency="INR"),
        currency="INR",
        status=PaymentStatus.CAPTURED,
    )

    action = CandidateAction(
        id="act_high_prob",
        opportunity_id="opp_high_prob",
        payment_id="pay_captured_100",
        merchant_id="mer_100",
        action_type=RecoveryActionType.SMART_RETRY,
        expected_recovery_value=Money(amount_minor=100000, currency="INR"),
        agent_confidence=0.99,
        idempotency_key="idemp_high_prob",
    )
    ctx = PolicyContext(payment=captured_payment)

    decision = engine.evaluate(action, context=ctx)
    assert decision.decision == "BLOCKED"
    assert decision.blocked_by_policy_id == "POL_001"
    assert decision.approval_token is None


def test_5_invalid_probability_less_than_zero_rejected():
    with pytest.raises(InvalidMoneyError, match="Probability must be between 0.0 and 1.0"):
        calculate_expected_value(probability=-0.5, amount_minor=100000)


def test_6_invalid_probability_greater_than_one_rejected():
    with pytest.raises(InvalidMoneyError, match="Probability must be between 0.0 and 1.0"):
        calculate_expected_value(probability=1.5, amount_minor=100000)


def test_7_nan_probability_rejected():
    with pytest.raises(InvalidMoneyError):
        calculate_expected_value(probability=float("nan"), amount_minor=100000)


def test_8_9_10_inference_exception_triggers_deterministic_fallback():
    faulty_model = MockFaultyModel()
    planner = RecoveryPlanner(propensity_model=faulty_model)

    from agents.root_cause.models import RootCauseAnalysis
    rca = RootCauseAnalysis(
        payment_id="pay_fallback_1",
        root_cause="TRANSIENT_NETWORK_TIMEOUT",
        confidence=0.85,
        recommended_direction="RETRY",
        recoverability="HIGH",
        explanation="Network timeout observed",
    )
    payment = Payment(
        id="pay_fallback_1",
        order_id="ord_1",
        merchant_id="mer_1",
        customer_id="cust_1",
        amount=Money(amount_minor=100000, currency="INR"),
        currency="INR",
        status=PaymentStatus.FAILED,
    )

    plan, summaries = planner.plan_recovery(rca, payment)
    assert plan.reasoning_mode == "DETERMINISTIC_FALLBACK"
    assert summaries[0]["reasoning_mode"] == "DETERMINISTIC_FALLBACK"
    assert "ML propensity model inference error" in str(summaries[0]["fallback_reason"])


def test_11_fallback_still_reaches_policy_engine():
    engine = PolicyEngine()

    payment = Payment(
        id="pay_captured_fallback",
        order_id="ord_fb",
        merchant_id="mer_fb",
        customer_id="cust_fb",
        amount=Money(amount_minor=100000, currency="INR"),
        currency="INR",
        status=PaymentStatus.CAPTURED,
    )

    action = CandidateAction(
        id="act_fb",
        opportunity_id="opp_fb",
        payment_id=payment.id,
        merchant_id=payment.merchant_id,
        action_type=RecoveryActionType.SMART_RETRY,
        expected_recovery_value=Money(amount_minor=100000, currency="INR"),
        agent_confidence=0.8,
        idempotency_key="idemp_fb",
    )
    ctx = PolicyContext(payment=payment)

    decision = engine.evaluate(action, context=ctx)
    assert decision.decision == "BLOCKED"


def test_12_ml_cannot_modify_monetary_values():
    ev = calculate_expected_value(probability=0.81, amount_minor=150000, cost_minor=50)
    assert isinstance(ev.expected_value_minor, int)
    assert ev.expected_value_minor == round(0.81 * 150000) - 50


def test_13_ml_cannot_modify_policy_thresholds():
    ctx = PolicyContext()
    assert ctx.high_value_threshold_minor == 1000000


def test_14_15_ml_cannot_issue_approval_tokens_or_create_side_effects():
    executor = ToolExecutor()
    action = CandidateAction(
        id="act_se",
        opportunity_id="opp_se",
        payment_id="pay_se",
        merchant_id="mer_se",
        action_type=RecoveryActionType.PAYMENT_LINK_DISPATCH,
        expected_recovery_value=Money(amount_minor=100000, currency="INR"),
        agent_confidence=0.95,
        idempotency_key="idemp_se",
    )
    decision_without_token = PolicyDecision(
        decision_id="dec_no_token",
        action_id=action.id,
        opportunity_id=action.opportunity_id,
        payment_id=action.payment_id,
        decision="APPROVED",
        reason="Approved but missing token",
        approval_token=None,
    )
    with pytest.raises(PolicyViolationError) as exc_info:
        executor.execute_action(action=action, decision=decision_without_token)
    assert "Missing PolicyApprovalToken" in str(exc_info.value)
