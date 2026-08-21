"""
RAVEN Phase 12 Security & API Test Suite: Operations Intelligence API Endpoints

Verifies operations intelligence endpoints, RBAC permissions, and dry-run policy optimization.
"""

from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)


def test_intelligence_overview_endpoint() -> None:
    """Verifies GET /api/v1/operations/intelligence/overview returns HTTP 200."""
    response = client.get(
        "/api/v1/operations/intelligence/overview",
        headers={"X-API-Key": "test_api_key"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "recovery_rate" in data
    assert "gross_recovered_amount_minor" in data


def test_intelligence_calibration_endpoint() -> None:
    """Verifies GET /api/v1/operations/intelligence/calibration returns HTTP 200."""
    response = client.get(
        "/api/v1/operations/intelligence/calibration",
        headers={"X-API-Key": "test_api_key"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "brier_score" in data
    assert "expected_calibration_error" in data


def test_intelligence_drift_endpoint() -> None:
    """Verifies GET /api/v1/operations/intelligence/drift returns HTTP 200."""
    response = client.get(
        "/api/v1/operations/intelligence/drift",
        headers={"X-API-Key": "test_api_key"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "status" in data


def test_policy_optimize_endpoint() -> None:
    """Verifies POST /api/v1/operations/intelligence/policy-optimize returns dry-run report."""
    response = client.post(
        "/api/v1/operations/intelligence/policy-optimize",
        headers={"X-API-Key": "test_api_key", "X-User-Role": "ADMIN"},
        json={
            "policy_id": "pol_alpha",
            "candidate_configuration": {"maximum_retry_attempts": 2},
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["side_effects_occurred"] is False
    assert data["is_valid"] is True
