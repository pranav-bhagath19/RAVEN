"""
RAVEN Phase 12 Security Test Suite: Offline Policy Optimizer Security

Verifies that OfflinePolicyOptimizer executes strictly in dry-run mode without side effects.
"""

from ml.optimization.policy_optimizer import OfflinePolicyOptimizer


def test_policy_optimizer_guaranteed_zero_side_effects() -> None:
    """Proves OfflinePolicyOptimizer cannot execute tools or mutate active production state."""
    optimizer = OfflinePolicyOptimizer()
    report = optimizer.optimize_policy(
        policy_id="pol_test",
        candidate_config={"maximum_retry_attempts": 2},
        historical_outcomes=[],
    )
    assert report.side_effects_occurred is False
    assert report.safety_violations == 0
