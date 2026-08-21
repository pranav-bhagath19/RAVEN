"""
RAVEN Phase 12 Security Test Suite: Tenant Isolation

Verifies that tenant recovery intelligence is strictly scoped by tenant_id and prevents cross-tenant contamination.
"""

from ml.adaptive.dataset import AdaptiveOutcomeRecord
from ml.adaptive.tenant_intelligence import TenantIntelligenceManager


def test_tenant_intelligence_cross_tenant_isolation() -> None:
    """Proves TenantIntelligenceManager filters records strictly by tenant_id."""
    records = [
        AdaptiveOutcomeRecord(
            tenant_id="tenant_A",
            payment_id="pay_a1",
            decision_id="dec_a1",
            action_type="SMART_RETRY",
            amount_minor=100000,
            attempts_count=1,
            error_code="TIMEOUT",
            root_cause="NETWORK",
            propensity_score=0.8,
            policy_version=1,
            timestamp="2026-08-22T00:00:00Z",
            outcome=1,
        ),
        AdaptiveOutcomeRecord(
            tenant_id="tenant_B",
            payment_id="pay_b1",
            decision_id="dec_b1",
            action_type="SMART_RETRY",
            amount_minor=200000,
            attempts_count=1,
            error_code="TIMEOUT",
            root_cause="NETWORK",
            propensity_score=0.5,
            policy_version=1,
            timestamp="2026-08-22T00:00:00Z",
            outcome=0,
        ),
    ]

    manager = TenantIntelligenceManager()
    profile_a = manager.build_tenant_profile("tenant_A", records)
    profile_b = manager.build_tenant_profile("tenant_B", records)

    assert profile_a.tenant_id == "tenant_A"
    assert profile_a.total_outcomes_observed == 1
    assert profile_a.total_recovered_minor == 100000

    assert profile_b.tenant_id == "tenant_B"
    assert profile_b.total_outcomes_observed == 1
    assert profile_b.total_recovered_minor == 0
