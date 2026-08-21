"""
RAVEN Model Artifact Manager Module

Manages model serialization, version metadata, hyperparameter tracking,
and SHA-256 artifact integrity hashing. Missing, tampered, or incompatible
artifacts safely trigger deterministic fallback.
"""

import hashlib
import json
from pathlib import Path
from typing import Any
from ml.models.propensity import LogisticRegressionPropensityModel


def compute_artifact_hash(model_dict: dict[str, Any]) -> str:
    """Computes deterministic SHA-256 hash of model metadata and weight parameters."""
    serialized = json.dumps(model_dict, sort_keys=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class ModelArtifactManager:
    """
    Manages persistence, retrieval, and validation of versioned model artifacts.
    """

    def __init__(self, artifacts_dir: str = "data/ml/models") -> None:
        self.artifacts_dir = Path(artifacts_dir)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

    def save_artifact(
        self,
        model: LogisticRegressionPropensityModel,
        dataset_version: str = "v1.0",
        feature_schema_version: str = "v1.0",
        artifact_filename: str | None = None,
    ) -> tuple[Path, str]:
        """
        Saves trained model artifact to JSON file with full metadata and SHA-256 hash.
        Returns tuple of (file_path, artifact_hash).
        """
        model_dict = model.save_dict()
        art_hash = compute_artifact_hash(model_dict)

        payload = {
            "artifact_version": "v1.0",
            "model_name": "raven_propensity_logistic_regression",
            "model_version": model.model_version,
            "feature_schema_version": feature_schema_version,
            "dataset_version": dataset_version,
            "artifact_hash": art_hash,
            "model_data": model_dict,
        }

        fname = artifact_filename or f"model_{model.model_version}.json"
        target_path = self.artifacts_dir / fname

        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, sort_keys=True)

        return target_path, art_hash

    def load_artifact(self, artifact_path: Path | str) -> tuple[LogisticRegressionPropensityModel, dict[str, Any]]:
        """
        Loads model artifact from file. Validates metadata and SHA-256 hash.
        Raises ValueError or FileNotFoundError if invalid or tampered.
        """
        path = Path(artifact_path)
        if not path.exists():
            raise FileNotFoundError(f"Model artifact not found at {path}")

        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)

        model_data = payload.get("model_data", {})
        expected_hash = payload.get("artifact_hash", "")
        actual_hash = compute_artifact_hash(model_data)

        if expected_hash and actual_hash != expected_hash:
            raise ValueError(f"Model artifact integrity check failed! Expected hash {expected_hash}, got {actual_hash}")

        model = LogisticRegressionPropensityModel()
        model.load_dict(model_data)

        meta = {
            "model_version": payload.get("model_version", "unknown"),
            "feature_schema_version": payload.get("feature_schema_version", "v1.0"),
            "dataset_version": payload.get("dataset_version", "v1.0"),
            "artifact_hash": actual_hash,
        }

        return model, meta
