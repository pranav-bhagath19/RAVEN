"""
Tests for RAVEN Phase 10 Control Plane ML Endpoints
"""

from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)
AUTH_HEADERS = {"X-API-Key": "test_operations_key"}


def test_get_ml_models_list():
    response = client.get("/api/v1/operations/ml/models", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["model_version"] == "v1.0"


def test_get_ml_model_detail_success():
    response = client.get("/api/v1/operations/ml/models/v1.0", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["model_version"] == "v1.0"
    assert data["model_type"] == "LogisticRegression"


def test_get_ml_model_detail_not_found():
    response = client.get("/api/v1/operations/ml/models/v99.0", headers=AUTH_HEADERS)
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"


def test_get_ml_metrics():
    response = client.get("/api/v1/operations/ml/metrics", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert "roc_auc" in data
    assert "accuracy" in data
    assert "confusion_matrix" in data
