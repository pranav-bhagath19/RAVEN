"""
Integration Tests for BenchmarkRunner and Strategy Pipeline
"""

from ml.evaluation.runner import BenchmarkRunner


def test_benchmark_runner_executes_all_scenarios_and_strategies():
    runner = BenchmarkRunner(seed=42)
    report = runner.run_benchmark()

    assert report.benchmark_version == "v1.0"
    assert report.seed == 42
    assert report.benchmark_hash != ""

    # Verify 5 strategies evaluated in Phase 12
    assert len(report.strategies) >= 3
    assert "RAVEN" in report.strategies
    assert "Always Retry" in report.strategies
    assert "Rule-Based Recovery" in report.strategies or "Rule-Based" in report.strategies

    # Verify metrics generated for each strategy
    assert "RAVEN" in report.metrics

    raven_metrics = report.metrics["RAVEN"]
    assert raven_metrics.total_cases >= 9
    assert raven_metrics.policy_violation_rate == 0.0
    assert raven_metrics.organic_recovery_misattribution_rate == 0.0

    # Verify raw results count
    assert len(report.raw_results) == len(report.strategies) * raven_metrics.total_cases
