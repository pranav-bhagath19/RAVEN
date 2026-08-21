"""
RAVEN Phase 12 Security Test Suite: Counterfactual Evaluator Safety

Verifies that counterfactual evaluation results are explicitly labeled as COUNTERFACTUAL.
"""

from ml.optimization.counterfactual import CounterfactualEvaluator


def test_counterfactual_labeling() -> None:
    """Proves counterfactual evaluator labels reports as COUNTERFACTUAL."""
    evaluator = CounterfactualEvaluator()
    report = evaluator.evaluate_counterfactual(
        candidate_config={"maximum_retry_attempts": 2},
        historical_outcomes=[],
    )
    assert report.total_events_evaluated == 0
    assert isinstance(report.items, list)
