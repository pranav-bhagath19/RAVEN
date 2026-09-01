"""
RAVEN Phase 13 Security Test Suite: Offline Simulation Safety

Verifies that BanditSimulator executes dry-run simulation with zero side effects.
"""

from ml.optimization.bandit_simulator import BanditSimulator


def test_bandit_simulation_zero_side_effects():
    sim = BanditSimulator(seed=42)
    report = sim.simulate(scenarios=[{"amount_minor": 100000, "error_code": "TIMEOUT"}])

    assert report.side_effects_executed == 0
    assert report.tokens_issued == 0
    assert report.unsafe_action_attempts == 0
    assert len(report.report_hash) == 64
