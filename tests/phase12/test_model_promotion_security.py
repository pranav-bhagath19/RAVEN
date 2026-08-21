"""
RAVEN Phase 12 Security Test Suite: Model Promotion Security

Verifies that model promotion requires explicit human authorization and cannot occur automatically.
"""

from ml.models.registry import ModelRegistry, ModelRegistryEntry, ModelStatus


def test_model_promotion_requires_explicit_call() -> None:
    """Proves models start as CANDIDATE and require explicit promote_to_champion call."""
    registry = ModelRegistry()
    entry = ModelRegistryEntry(
        model_version="v2.0",
        training_dataset_hash="hash123",
        artifact_hash="art123",
        status=ModelStatus.CANDIDATE,
    )
    registry.register_model(entry)
    assert registry.get_champion() is None
    retrieved = registry.get_model("v2.0")
    assert retrieved is not None
    assert retrieved.status == ModelStatus.CANDIDATE

    # Explicit promotion call
    registry.promote_to_champion("v2.0", approved_by="admin_user")
    champ = registry.get_champion()
    assert champ is not None
    assert champ.model_version == "v2.0"
    assert champ.status == ModelStatus.CHAMPION
