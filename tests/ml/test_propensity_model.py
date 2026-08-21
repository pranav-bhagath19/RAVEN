"""
Unit Tests for RAVEN ML Propensity Model & Artifact Manager
"""

from pathlib import Path
import numpy as np
import pytest
from ml.models.artifact import ModelArtifactManager
from ml.models.propensity import LogisticRegressionPropensityModel


def test_logistic_regression_fit_and_predict():
    model = LogisticRegressionPropensityModel(random_state=42)

    X = np.array([
        [0.1, 0, 0, 0, 0, 0, 0, 0, 0],
        [0.5, 2, 0, 1, 1, 1, 0, 0, 0],
        [0.2, 0, 0, 0, 0, 0, 0, 0, 0],
        [0.8, 3, 0, 2, 2, 2, 1, 1, 1],
    ])
    y = np.array([1, 0, 1, 0])

    model.fit(X, y)
    assert model.is_fitted is True

    prob = model.predict_probability(X[0])
    assert 0.0 <= prob <= 1.0


def test_model_artifact_save_load_and_tamper_detection(tmp_path: Path):
    model = LogisticRegressionPropensityModel(random_state=42)
    X = np.array([[0.1, 0, 0, 0, 0, 0, 0, 0, 0], [0.5, 2, 0, 1, 1, 1, 0, 0, 0]])
    y = np.array([1, 0])
    model.fit(X, y)

    mgr = ModelArtifactManager(artifacts_dir=str(tmp_path))
    art_path, art_hash = mgr.save_artifact(model, artifact_filename="test_model.json")

    assert art_path.exists()
    assert art_hash != ""

    loaded_model, meta = mgr.load_artifact(art_path)
    assert loaded_model.is_fitted is True
    assert meta["artifact_hash"] == art_hash

    # Tampering test: Modify file contents to trigger hash verification error
    with open(art_path, "r", encoding="utf-8") as f:
        content = f.read()
    tampered_content = content.replace("v1.0", "v999.0")
    with open(art_path, "w", encoding="utf-8") as f:
        f.write(tampered_content)

    with pytest.raises(ValueError, match="integrity check failed"):
        mgr.load_artifact(art_path)
