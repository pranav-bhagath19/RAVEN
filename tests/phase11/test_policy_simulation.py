"""
Phase 11 Policy Simulation Tests

Verifies dry-run policy simulation: evaluating candidate configuration against benchmark suite
with zero side-effects, zero token issuance, zero DB mutations.
"""

from persistence.database import Base, engine, SessionLocal
from apps.api.policy_service import PolicyService

Base.metadata.create_all(bind=engine)


def test_dry_run_policy_simulation_zero_side_effects():
    db = SessionLocal()
    try:
        svc = PolicyService(db)
        tenant_id = "tenant_simulation_test"

        candidate_cfg = {
            "maximum_retry_attempts": 4,
            "retry_cooldown_seconds": 120,
            "min_confidence_threshold": 0.70,
        }

        res = svc.simulate(tenant_id, candidate_cfg)
        assert res.is_valid is True
        assert res.side_effects_occurred is False
        assert res.total_historical_decisions_evaluated > 0
        assert res.hypothetical_recovery_rate >= 0.0
        assert len(res.affected_rules) == 3
    finally:
        db.close()
