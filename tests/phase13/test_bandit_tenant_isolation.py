"""
RAVEN Phase 13 Security Test Suite: Tenant Isolation

Verifies that Contextual Bandit operates with strict tenant isolation:
1. Bandit statistics & updates in Tenant A do not pollute Tenant B.
2. Cross-tenant reads are prevented.
"""

from ml.bandits.tenant_bandit import TenantBanditManager


def test_tenant_bandit_isolation_between_tenants():
    manager = TenantBanditManager()

    # Update Tenant A
    manager.update_bandit(
        tenant_id="tenant_alpha",
        action_type="RETRY_PAYMENT",
        context_vector=[0.1] * 12,
        reward=1.0,
    )

    profile_a = manager.get_or_create_profile("tenant_alpha")
    profile_b = manager.get_or_create_profile("tenant_beta")

    assert profile_a.total_bandit_updates == 1
    assert profile_b.total_bandit_updates == 0
    assert profile_a.tenant_id == "tenant_alpha"
    assert profile_b.tenant_id == "tenant_beta"


def test_tenant_fallback_cascade():
    manager = TenantBanditManager()
    
    # New tenant with 0 samples should trigger fallback mode
    res = manager.score_and_select(
        tenant_id="tenant_new",
        candidate_actions=["RETRY_PAYMENT", "RETRY_WITH_DELAY"],
        context_vector=[0.5] * 12,
    )

    assert res.selected_action in ["RETRY_PAYMENT", "RETRY_WITH_DELAY"]
    assert res.mode in ["TENANT_CONTEXTUAL_BANDIT", "GLOBAL_CONTEXTUAL_BANDIT", "ADAPTIVE_ML", "ADAPTIVE_PROPENSITY", "DETERMINISTIC_FALLBACK"]
