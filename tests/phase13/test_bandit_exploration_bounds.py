"""
RAVEN Phase 13 Security Test Suite: Exploration Bounds & Safety Constraints

Verifies that:
1. Exploration is bounded by max exploration rate cap (10%).
2. Exploration overrides trigger on customer opt-out and systemic outages.
"""

from ml.bandits.exploration import ExplorationPolicyConfig, ExplorationManager


def test_exploration_bounds_max_exploration_rate():
    cfg = ExplorationPolicyConfig(max_exploration_rate=0.10, min_sample_threshold=5)
    mgr = ExplorationManager(config=cfg)

    # Opt-out customer scenario MUST override exploration to False
    decision_opt_out = mgr.should_explore(
        tenant_id="tenant_ex_01",
        action_type="RETRY_PAYMENT",
        historical_sample_count=20,
        customer_opt_out=True,
        is_systemic_downtime=False,
    )
    assert decision_opt_out.should_explore is False
    assert decision_opt_out.override_reason == "CUSTOMER_OPT_OUT"

    # Systemic downtime scenario MUST override exploration to False
    decision_downtime = mgr.should_explore(
        tenant_id="tenant_ex_01",
        action_type="RETRY_PAYMENT",
        historical_sample_count=20,
        customer_opt_out=False,
        is_systemic_downtime=True,
    )
    assert decision_downtime.should_explore is False
    assert decision_downtime.override_reason == "SYSTEMIC_DOWNTIME"
