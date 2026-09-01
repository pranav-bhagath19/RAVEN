"""
RAVEN Phase 13 Security Test Suite: Fallback Cascade

Verifies that model errors, invalid context, or missing data safely trigger fallback cascade.
"""

from ml.bandits.tenant_bandit import TenantBanditManager


def test_bandit_fallback_cascade_on_missing_model():
    manager = TenantBanditManager()
    
    # Missing tenant model / zero samples falls back smoothly
    res = manager.score_and_select(
        tenant_id="tenant_missing",
        candidate_actions=["RETRY_PAYMENT", "NO_ACTION"],
        context_vector=[0.0] * 12,
    )

    assert res.selected_action in ["RETRY_PAYMENT", "NO_ACTION"]
    assert res.mode != "FAILED"
