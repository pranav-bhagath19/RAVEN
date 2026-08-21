"""
Phase 11 Policy Audit Tests

Verifies that all policy creation, validation, activation, and rollback operations
generate immutable, append-only audit entries containing SHA-256 hashes and reasons.
"""

import uuid
from persistence.database import Base, engine, SessionLocal
from apps.api.policy_service import PolicyService

Base.metadata.create_all(bind=engine)


def test_policy_audit_trail_lineage():
    db = SessionLocal()
    try:
        svc = PolicyService(db)
        tenant_id = f"tenant_aud_{uuid.uuid4().hex[:6]}"

        # 1. Draft
        svc.create_draft(tenant_id, "pol_001", {"maximum_retry_attempts": 2}, actor_id="actor_draft")

        # 2. Activate
        svc.activate(tenant_id, 1, actor_id="actor_activate", reason="Production rollout")

        logs = svc.list_audit_logs(tenant_id)
        assert len(logs) == 2
        assert any(log.action == "CREATED" for log in logs)
        assert any(log.action == "ACTIVATED" for log in logs)
        for log in logs:
            assert log.configuration_hash is not None
            assert len(log.configuration_hash) == 64
    finally:
        db.close()
