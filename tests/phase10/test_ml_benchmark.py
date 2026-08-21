"""
Tests for RAVEN Phase 10 ML Propensity Comparative Benchmark
"""

from agents.common.provider import MockLLMProvider
from ml.evaluation.baselines import AlwaysRetryStrategy, RuleBasedStrategy
from ml.evaluation.runner import BenchmarkRunner
from ml.evaluation.strategies import RavenMLPropensityStrategy, RavenStrategy


def test_4_strategy_benchmark_execution_and_hashing():
    provider = MockLLMProvider()
    strategies = [
        RavenStrategy(provider=provider),
        RavenMLPropensityStrategy(provider=provider, seed=42),
        AlwaysRetryStrategy(),
        RuleBasedStrategy(),
    ]
    runner = BenchmarkRunner(seed=42, strategies=strategies)
    report = runner.run_benchmark()

    assert len(report.strategies) == 4
    assert "RAVEN" in report.strategies
    assert "RAVEN + ML Propensity" in report.strategies
    assert "Always Retry" in report.strategies
    assert "Rule-Based" in report.strategies

    assert report.benchmark_hash != ""
    assert report.seed == 42

    # Determinism check: running twice with seed 42 produces identical benchmark hash
    runner2 = BenchmarkRunner(seed=42, strategies=strategies)
    report2 = runner2.run_benchmark()
    assert report2.benchmark_hash == report.benchmark_hash
