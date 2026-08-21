"""
Unit Tests for Evaluation Metrics Engine
"""

from ml.evaluation.metrics import calculate_metrics_for_results
from ml.evaluation.models import EvaluationCase, EvaluationResult


def test_metrics_calculation_accurate():
    case_1 = EvaluationCase(
        case_id="case_1",
        scenario_id="scenario_1",
        payment_id="pay_1",
        amount_minor=100000,  # ₹1,000
        currency="INR",
        ground_truth_root_cause="GATEWAY_TIMED_OUT",
        ground_truth_recoverable=True,
        ground_truth_organic_recovery=False,
        ground_truth_optimal_action="SMART_RETRY",
    )

    case_2 = EvaluationCase(
        case_id="case_2",
        scenario_id="scenario_2",
        payment_id="pay_2",
        amount_minor=200000,  # ₹2,000
        currency="INR",
        ground_truth_root_cause="CARD_EXPIRED",
        ground_truth_recoverable=False,
        ground_truth_organic_recovery=False,
        ground_truth_optimal_action="NONE",
    )

    cases_map = {"case_1": case_1, "case_2": case_2}

    res_1 = EvaluationResult(
        case_id="case_1",
        scenario_id="scenario_1",
        strategy_name="RAVEN",
        decision="APPROVED",
        root_cause_prediction="GATEWAY_TIMED_OUT",
        root_cause_correct=True,
        selected_action="SMART_RETRY",
        optimal_action="SMART_RETRY",
        action_correct=True,
        recovered=True,
        recovery_attributed=True,
        recovered_amount_minor=100000,
        action_cost_minor=0,
        net_recovered_minor=100000,
        policy_violation=False,
        decision_latency_ms=50.0,
    )

    res_2 = EvaluationResult(
        case_id="case_2",
        scenario_id="scenario_2",
        strategy_name="RAVEN",
        decision="BLOCKED",
        root_cause_prediction="CARD_EXPIRED",
        root_cause_correct=True,
        selected_action="NONE",
        optimal_action="NONE",
        action_correct=True,
        recovered=False,
        recovery_attributed=False,
        recovered_amount_minor=0,
        action_cost_minor=0,
        net_recovered_minor=0,
        policy_violation=False,
        decision_latency_ms=40.0,
    )

    metrics = calculate_metrics_for_results([res_1, res_2], cases_map)

    assert metrics.total_cases == 2
    assert metrics.state_reconstruction_accuracy == 1.0
    assert metrics.root_cause_accuracy == 1.0
    assert metrics.action_selection_accuracy == 1.0
    assert metrics.total_revenue_at_risk_minor == 300000
    assert metrics.total_revenue_recovered_minor == 100000
    assert metrics.recovery_rate == round(100000 / 300000, 4)
    assert metrics.policy_violation_rate == 0.0
    assert metrics.attribution_precision == 1.0
    assert metrics.attribution_recall == 1.0
    assert metrics.organic_recovery_misattribution_rate == 0.0
