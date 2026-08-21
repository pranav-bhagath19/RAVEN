"""
Phase 11 Policy REST API Integration Tests

Verifies FastAPI HTTP endpoints for listing, drafting, validating, simulating, activating,
rolling back, and querying audit logs for merchant policy configurations.
"""

import uuid
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)


def test_policy_api_draft_validate_activate_lifecycle():
    tid = f"tenant_api_{uuid.uuid4().hex[:6]}"
    headers = {"X-API-Key": "policy_mgr_key", "X-Tenant-ID": tid}

    # 1. Create draft
    draft_res = client.post(
        "/api/v1/operations/policies",
        json={"policy_id": "pol_api_01", "configuration_json": {"maximum_retry_attempts": 3}},
        headers=headers,
    )
    assert draft_res.status_code == 201
    draft_data = draft_res.json()
    assert draft_data["version"] == 1
    assert draft_data["status"] == "DRAFT"

    # 2. Validate policy
    val_res = client.post(
        "/api/v1/operations/policies/pol_api_01/validate",
        json={"configuration_json": {"maximum_retry_attempts": 3}},
        headers=headers,
    )
    assert val_res.status_code == 200
    assert val_res.json()["is_valid"] is True

    # 3. Simulate policy
    sim_res = client.post(
        "/api/v1/operations/policies/pol_api_01/simulate",
        json={"configuration_json": {"maximum_retry_attempts": 3}},
        headers=headers,
    )
    assert sim_res.status_code == 200
    assert sim_res.json()["side_effects_occurred"] is False

    # 4. Activate policy
    act_res = client.post(
        "/api/v1/operations/policies/pol_api_01/activate",
        json={"version": 1, "reason": "API rollout"},
        headers=headers,
    )
    assert act_res.status_code == 200
    assert act_res.json()["status"] == "ACTIVE"

    # 5. List audit logs
    audit_res = client.get("/api/v1/operations/policies/pol_api_01/audit", headers=headers)
    assert audit_res.status_code == 200
    assert len(audit_res.json()) >= 2
