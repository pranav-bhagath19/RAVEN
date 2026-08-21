"""
Unit and Deterministic Expected Value Tests for Recovery Planner Agent
"""

import pytest
from agents.common.provider import MockLLMProvider
from agents.recovery_planner.expected_value import ExpectedValue, calculate_expected_value
from agents.recovery_planner.models import CandidateActionProposal, RecoveryPlan
from agents.recovery_planner.planner import RecoveryPlanner
from agents.root_cause.models import RootCauseAnalysis
from domain.entities.payment import Payment, PaymentStatus
from domain.enums import RecoveryActionType
from domain.exceptions import InvalidMoneyError
from domain.values.money import Money


def test_deterministic_ev_calculation():
    # p = 0.8, amount = 10,000 paise (₹100), cost = 50 paise
    ev = calculate_expected_value(probability=0.8, amount_minor=10000, cost_minor=50)

    assert isinstance(ev, ExpectedValue)
    assert ev.probability == 0.8
    assert ev.amount_minor == 10000
    assert ev.cost_minor == 50
    assert ev.expected_recovery_minor == 8000
    assert ev.expected_value_minor == 7950


def test_ev_zero_probability():
    ev = calculate_expected_value(probability=0.0, amount_minor=10000, cost_minor=50)
    assert ev.expected_recovery_minor == 0
    assert ev.expected_value_minor == -50


def test_ev_prob_one():
    ev = calculate_expected_value(probability=1.0, amount_minor=10000, cost_minor=0)
    assert ev.expected_recovery_minor == 10000
    assert ev.expected_value_minor == 10000


def test_ev_invalid_probability_rejected():
    with pytest.raises(InvalidMoneyError):
        calculate_expected_value(probability=1.5, amount_minor=10000)

    with pytest.raises(InvalidMoneyError):
        calculate_expected_value(probability=-0.1, amount_minor=10000)


def test_ev_integer_minor_units_only():
    with pytest.raises(InvalidMoneyError):
        calculate_expected_value(probability=0.5, amount_minor=100.5)  # float not allowed


def test_proposal_ranking_by_ev():
    planner = RecoveryPlanner()
    rca = RootCauseAnalysis(
        payment_id="pay_rank_1",
        root_cause="INSUFFICIENT_FUNDS",
        explanation="Test",
        recoverability="HIGH",
        confidence=0.90,
        recommended_direction="Test",
    )

    def mock_generator(prompt, model):
        return RecoveryPlan(
            payment_id="pay_rank_1",
            proposals=[
                CandidateActionProposal(
                    action_type=RecoveryActionType.FALLBACK_CHANNEL_NOTIFY,
                    reasoning="SMS reminder",
                    predicted_success_probability=0.40,
                    agent_confidence=0.80,
                    estimated_cost_minor=20,
                ),
                CandidateActionProposal(
                    action_type=RecoveryActionType.PAYMENT_LINK_DISPATCH,
                    reasoning="WhatsApp link",
                    predicted_success_probability=0.80,
                    agent_confidence=0.90,
                    estimated_cost_minor=50,
                ),
            ],
            reasoning_mode="LLM",
        )

    provider = MockLLMProvider(mock_response_generator=mock_generator)
    payment = Payment(
        id="pay_rank_1",
        order_id="ord_1",
        merchant_id="mer_1",
        customer_id="cust_1",
        amount=Money(amount_minor=10000),
        status=PaymentStatus.FAILED,
    )

    plan, summaries = planner.plan_recovery(rca=rca, payment=payment, provider=provider)

    # Top proposal should be PAYMENT_LINK_DISPATCH due to higher EV (80% of 10000 - 50 = 7950 > 40% of 10000 - 20 = 3980)
    assert plan.proposals[0].action_type == RecoveryActionType.PAYMENT_LINK_DISPATCH
    assert summaries[0]["expected_value_minor"] > summaries[1]["expected_value_minor"]


def test_planner_llm_failure_fallback():
    planner = RecoveryPlanner()
    provider = MockLLMProvider(force_failure=True)
    rca = RootCauseAnalysis(
        payment_id="pay_fall_1",
        root_cause="GATEWAY_TIMED_OUT",
        explanation="Timeout",
        recoverability="HIGH",
        confidence=0.90,
        recommended_direction="Retry",
    )
    payment = Payment(
        id="pay_fall_1",
        order_id="ord_1",
        merchant_id="mer_1",
        customer_id="cust_1",
        amount=Money(amount_minor=5000),
        status=PaymentStatus.FAILED,
    )

    plan, _ = planner.plan_recovery(rca=rca, payment=payment, provider=provider)

    assert plan.reasoning_mode == "DETERMINISTIC_FALLBACK"
    assert plan.proposals[0].action_type == RecoveryActionType.SMART_RETRY
