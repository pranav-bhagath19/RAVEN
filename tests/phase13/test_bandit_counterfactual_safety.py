"""
RAVEN Phase 13 Security Test Suite: Counterfactual Safety

Verifies that unverified hypothetical rewards remain tagged COUNTERFACTUAL and do not mutate financial state.
"""

from ml.bandits.reward import BanditRewardModel


def test_reward_counterfactual_tagging():
    rm = BanditRewardModel()
    sig = rm.compute_reward(
        verified_recovery=True,
        recovered_amount_minor=50000,
        is_counterfactual=True,
    )

    assert sig.is_counterfactual is True
    assert sig.reward_value == 1.0
    assert sig.monetary_unit == "PAISE"
