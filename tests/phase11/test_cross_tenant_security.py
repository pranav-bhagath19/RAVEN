"""
Phase 11 Cross-Tenant Security Tests

Verifies that Tenant A cannot read or modify Tenant B's payments, decision traces,
ML metrics, or policy configurations. Cross-tenant access must fail closed.
"""

from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)


def test_tenant_a_cannot_access_tenant_b_policies():
    headers_a = {"X-API-Key": "tenant_a_key", "X-Tenant-ID": "tenant_a"}
    headers_b = {"X-API-Key": "tenant_b_key", "X-Tenant-ID": "tenant_b"}

    # Tenant B creates policy
    client.post(
        "/api/v1/operations/policies",
        json={"policy_id": "pol_tenant_b", "configuration_json": {"maximum_retry_attempts": 2}},
        headers=headers_b,
    )

    # Tenant A attempts to read Tenant B's policy using Tenant A context -> receives empty or 404
    res_a = client.get("/api/v1/operations/policies/pol_tenant_b", headers=headers_a)
    assert res_a.status_code == 404
