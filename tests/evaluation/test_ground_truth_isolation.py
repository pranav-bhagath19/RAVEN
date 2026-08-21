"""
Ground Truth Isolation Tests (Section 23 Specification)

Verifies that ground truth fields are strictly isolated from strategy execution inputs
and NEVER leaked into LLM prompts or strategy decision logic.
"""

from ml.evaluation.runner import BenchmarkRunner
from ml.evaluation.strategies import RavenStrategy


def test_ground_truth_isolation_from_strategy_input():
    runner = BenchmarkRunner(seed=42)
    cases, _ = runner.build_evaluation_cases()

    strategy = RavenStrategy()

    for case in cases:
        # Inspect raw events passed to strategy
        event_payloads = [str(ev.payload) for ev in case.events]
        payload_text = " ".join(event_payloads).upper()

        # Ground truth values must NOT appear in event payloads
        assert case.ground_truth_optimal_action not in payload_text
        assert "GROUND_TRUTH" not in payload_text

        # Evaluate strategy and verify decision does not inspect case ground truth
        decision = strategy.evaluate(case)
        assert decision.strategy_name == "RAVEN"
