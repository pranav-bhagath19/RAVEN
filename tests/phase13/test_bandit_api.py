"""
RAVEN Phase 13 Security Test Suite: Contextual Bandit API Integration

Verifies API endpoints for Contextual Bandit intelligence.
"""

from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)


def test_get_bandit_overview_api():
    response = client.get("/api/v1/operations/intelligence/bandit")
    assert response.status_code == 200
    data = response.json()
    assert data["algorithm"] == "LinUCB"
    assert data["feature_dimensions"] == 12


def test_get_bandit_actions_api():
    response = client.get("/api/v1/operations/intelligence/bandit/actions")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 5


def test_get_bandit_evaluation_api():
    response = client.get("/api/v1/operations/intelligence/bandit/evaluation")
    assert response.status_code == 200
    data = response.json()
    assert "report_hash" in data
    assert data["raven_contextual_bandit"]["recovery_rate"] > 0.0


def test_simulate_bandit_api():
    response = client.post("/api/v1/operations/intelligence/bandit/simulate")
    assert response.status_code == 200
    data = response.json()
    assert data["side_effects_executed"] == 0
    assert "report_hash" in data
