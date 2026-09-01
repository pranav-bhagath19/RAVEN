"""
RAVEN Phase 13 Security Test Suite: Model Integrity & Hashing

Verifies SHA-256 integrity hash calculation and detection of model state tampering.
"""

from ml.bandits.model import LinUCBBanditModel


def test_bandit_model_artifact_hash():
    model = LinUCBBanditModel(alpha=0.5, seed=42)
    hash1 = model.get_artifact_hash()
    assert len(hash1) == 64  # Valid SHA-256 hex digest

    # Update model parameters
    model.update("RETRY_PAYMENT", [0.1] * 12, reward=1.0)
    hash2 = model.get_artifact_hash()

    assert hash1 != hash2
    assert len(hash2) == 64
