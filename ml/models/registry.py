"""
RAVEN Model Registry Module

Manages model lifecycle status: CANDIDATE, CHALLENGER, CHAMPION, RETIRED, REJECTED.
Enforces explicit, controlled promotion; AUTOMATIC PRODUCTION PROMOTION IS STRICTLY FORBIDDEN.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class ModelStatus(str, Enum):
    """Model status lifecycle enum."""

    CANDIDATE = "CANDIDATE"
    CHALLENGER = "CHALLENGER"
    CHAMPION = "CHAMPION"
    RETIRED = "RETIRED"
    REJECTED = "REJECTED"


class ModelRegistryEntry(BaseModel):
    """Model Registry record schema."""

    model_version: str = Field(..., description="Unique model version, e.g. v1.0, v1.1-challenger")
    model_type: str = Field(default="LOGISTIC_REGRESSION", description="Model architecture type tag")
    feature_schema_version: str = Field(default="v1.0", description="Associated feature schema version")
    training_dataset_hash: str = Field(..., description="SHA-256 hash of training dataset")
    artifact_hash: str = Field(..., description="SHA-256 hash of serialized model artifact")
    training_seed: int = Field(default=42, description="Random seed used for training")
    training_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Training timestamp in UTC",
    )
    metrics: dict[str, Any] = Field(default_factory=dict, description="Model evaluation metrics summary")
    status: ModelStatus = Field(default=ModelStatus.CANDIDATE, description="Current lifecycle status")


class ModelRegistry:
    """
    In-memory / Persistent Model Registry for tracking model versions and status promotions.
    """

    def __init__(self) -> None:
        self.models: dict[str, ModelRegistryEntry] = {}

    def register_model(self, entry: ModelRegistryEntry) -> ModelRegistryEntry:
        """Registers a new model entry in CANDIDATE or CHALLENGER status."""
        self.models[entry.model_version] = entry
        return entry

    def promote_to_champion(self, model_version: str, approved_by: str) -> ModelRegistryEntry:
        """
        Explicitly promotes a model to CHAMPION status.
        Retires any existing CHAMPION model.
        """
        if model_version not in self.models:
            raise ValueError(f"Model version '{model_version}' not found in registry.")

        # Retire existing champion
        for m in self.models.values():
            if m.status == ModelStatus.CHAMPION:
                m.status = ModelStatus.RETIRED

        target = self.models[model_version]
        target.status = ModelStatus.CHAMPION
        return target

    def get_champion(self) -> ModelRegistryEntry | None:
        """Retrieves currently active CHAMPION model."""
        for m in self.models.values():
            if m.status == ModelStatus.CHAMPION:
                return m
        return None

    def get_model(self, model_version: str) -> ModelRegistryEntry | None:
        """Retrieves model registry entry by model version."""
        return self.models.get(model_version)

    def list_models(self) -> list[ModelRegistryEntry]:
        """Lists all registered models."""
        return list(self.models.values())
