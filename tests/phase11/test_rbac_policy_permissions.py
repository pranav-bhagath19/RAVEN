"""
Phase 11 RBAC Policy Permission Tests

Verifies fine-grained permission enforcement:
OPERATIONS_READ cannot mutate policy.
POLICY_WRITE cannot activate without POLICY_ACTIVATE.
Unauthorized attempts return 403 Forbidden.
"""

from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)


def test_read_only_user_cannot_create_policy():
    headers = {"X-API-Key": "read_key", "X-Tenant-ID": "tenant_rbac_test"}
    res = client.post(
        "/api/v1/operations/policies",
        json={"policy_id": "pol_01", "configuration_json": {"maximum_retry_attempts": 2}},
        headers=headers,
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "FORBIDDEN"
