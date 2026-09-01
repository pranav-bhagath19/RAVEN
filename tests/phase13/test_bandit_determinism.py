"""
RAVEN Phase 13 Security Test Suite: Determinism & Hash Reproducibility

Verifies that identical inputs, context, and seed produce identical scores, context vectors, and artifact hashes.
"""

from ml.bandits.context import BanditContextBuilder
from ml.bandits.model import LinUCBBanditModel


def test_bandit_scoring_determinism():
    builder = BanditContextBuilder()
    m1 = LinUCBBanditModel(alpha=0.5, seed=42)
    m2 = LinUCBBanditModel(alpha=0.5, seed=42)

    raw_record = {
        "tenant_id": "tenant_det",
        "payment_id": "pay_det_01",
        "amount_minor": 150000,
        "attempts_count": 2,
        "error_code": "TIMEOUT",
        "root_cause": "TRANSIENT_NETWORK_TIMEOUT",
        "action_type": "RETRY_PAYMENT",
    }

    ctx1 = builder.build_context(raw_record)
    ctx2 = builder.build_context(raw_record)

    assert ctx1.feature_vector == ctx2.feature_vector

    res1 = m1.score_action("RETRY_PAYMENT", ctx1.feature_vector)
    res2 = m2.score_action("RETRY_PAYMENT", ctx2.feature_vector)

    assert res1.predicted_reward == res2.predicted_reward
    assert res1.ucb_score == res2.ucb_score
    assert m1.get_artifact_hash() == m2.get_artifact_hash()
