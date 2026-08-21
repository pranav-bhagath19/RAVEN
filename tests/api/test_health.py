"""
Unit Tests for Health Endpoint Router
"""

from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)


def test_get_health_root():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "raven"}


def test_get_health_v1():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "raven"}
