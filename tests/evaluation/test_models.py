"""
Unit Tests for Evaluation Framework Data Models
"""

from ml.evaluation.models import (
    BenchmarkMetrics,
    BenchmarkReport,
    EvaluationCase,
    EvaluationResult,
    StrategyDecision,
)


def test_evaluation_case_model():
    case = EvaluationCase(
        case_id="case_001",
        scenario_id="scenario_1",
        payment_id="pay_100",
        amount_minor=10000,
        currency="INR",
        ground_truth_root_cause="GATEWAY_TIMED_OUT",
        ground_truth_recoverable=True,
        ground_truth_organic_recovery=False,
        ground_truth_optimal_action="SMART_RETRY",
        ground_truth_optimal_delay_seconds=900,
    )

    assert case.case_id == "case_001"
    assert case.amount_minor == 10000
    assert case.ground_truth_recoverable is True


def test_strategy_decision_model():
    decision = StrategyDecision(
        strategy_name="RAVEN",
        action_type="SMART_RETRY",
        decision="APPROVED",
        predicted_recovery_probability=0.85,
        expected_value_minor=10000,
    )

    assert decision.strategy_name == "RAVEN"
    assert decision.decision == "APPROVED"


def test_evaluation_result_model():
    res = EvaluationResult(
        case_id="case_001",
        scenario_id="scenario_1",
        strategy_name="RAVEN",
        decision="APPROVED",
        selected_action="SMART_RETRY",
        optimal_action="SMART_RETRY",
        action_correct=True,
        recovered=True,
        recovery_attributed=True,
        recovered_amount_minor=10000,
        action_cost_minor=0,
        net_recovered_minor=10000,
    )

    assert res.action_correct is True
    assert res.net_recovered_minor == 10000


def test_benchmark_metrics_model():
    metrics = BenchmarkMetrics(
        total_cases=9,
        recovery_rate=0.88,
        recovery_net_rate=88.0,
    )

    assert metrics.total_cases == 9
    assert metrics.recovery_net_rate == 88.0


def test_benchmark_report_model():
    report = BenchmarkReport(
        benchmark_version="v1.0",
        seed=42,
        benchmark_hash="hash123",
        strategies=["RAVEN", "Always Retry", "Rule-Based"],
    )

    assert len(report.strategies) == 3
    assert report.seed == 42
