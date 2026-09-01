"""
RAVEN Phase 14 Operational REST API & RBAC Test Suite

Tests REST endpoints under /api/v1/operations/regions and /api/v1/operations/replication:
1. GET /api/v1/operations/regions
2. GET /api/v1/operations/regions/{region_id}
3. GET /api/v1/operations/regions/{region_id}/health
4. POST /api/v1/operations/regions/{region_id}/status
5. GET /api/v1/operations/replication/status
6. GET /api/v1/operations/replication/checkpoints
"""

from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)
API_KEY = "test_dev_key_admin"


def test_api_list_regions():
    """Tests GET /api/v1/operations/regions."""
    response = client.get("/api/v1/operations/regions", headers={"X-API-Key": API_KEY})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 3
    region_ids = [r["region_id"] for r in data]
    assert "ap-south-1" in region_ids
    assert "us-east-1" in region_ids


def test_api_get_region_details():
    """Tests GET /api/v1/operations/regions/{region_id}."""
    response = client.get("/api/v1/operations/regions/ap-south-1", headers={"X-API-Key": API_KEY})
    assert response.status_code == 200
    data = response.json()
    assert data["region_id"] == "ap-south-1"
    assert data["is_primary"] is True


def test_api_get_region_health():
    """Tests GET /api/v1/operations/regions/{region_id}/health."""
    response = client.get("/api/v1/operations/regions/ap-south-1/health", headers={"X-API-Key": API_KEY})
    assert response.status_code == 200
    data = response.json()
    assert data["region_id"] == "ap-south-1"
    assert data["is_healthy"] is True


def test_api_update_region_status():
    """Tests POST /api/v1/operations/regions/{region_id}/status."""
    payload = {"status": "DEGRADED", "health_score": 0.5}
    response = client.post("/api/v1/operations/regions/eu-west-1/status", json=payload, headers={"X-API-Key": API_KEY})
    assert response.status_code == 200
    data = response.json()
    assert data["region_id"] == "eu-west-1"
    assert data["status"] == "DEGRADED"
    assert data["health_score"] == 0.5


def test_api_get_replication_status():
    """Tests GET /api/v1/operations/replication/status."""
    response = client.get("/api/v1/operations/replication/status", headers={"X-API-Key": API_KEY})
    assert response.status_code == 200
    data = response.json()
    assert "tenant_id" in data
    assert "sync_health" in data
    assert data["sync_health"] == "HEALTHY"


def test_api_get_replication_checkpoints():
    """Tests GET /api/v1/operations/replication/checkpoints."""
    response = client.get("/api/v1/operations/replication/checkpoints", headers={"X-API-Key": API_KEY})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
