"""
RAVEN Phase 13 Security Test Suite: Model Promotion Safety

Verifies that Contextual Bandit models cannot automatically promote themselves to CHAMPION status.
"""

from ml.models.registry import ModelRegistry, ModelRegistryEntry, ModelStatus


def test_bandit_model_requires_explicit_promotion():
    reg = ModelRegistry()
    entry = ModelRegistryEntry(
        model_version="v13.0-bandit",
        model_type="CONTEXTUAL_BANDIT",
        feature_schema_version="v13.0",
        training_dataset_hash="hash_data",
        artifact_hash="hash_art",
        status=ModelStatus.CANDIDATE,
    )
    reg.register_model(entry)

    # Initial status MUST be CANDIDATE
    assert reg.get_model("v13.0-bandit").status == ModelStatus.CANDIDATE
    assert reg.get_champion() is None

    # Explicit human promotion required
    reg.promote_to_champion("v13.0-bandit", approved_by="admin_sec_01")
    assert reg.get_champion().model_version == "v13.0-bandit"
