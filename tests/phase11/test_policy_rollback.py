"""
Phase 11 Policy Rollback Tests

Verifies lineage-preserving rollback mechanism:
Current v2 -> Rollback to v1 -> Creates new v3 containing v1 config with rollback_source_version = 1.
Historical versions remain 100% immutable.
"""

import uuid
from persistence.database import Base, engine, SessionLocal
from apps.api.policy_service import PolicyService

Base.metadata.create_all(bind=engine)


def test_lineage_preserving_rollback():
    db = SessionLocal()
    try:
        svc = PolicyService(db)
        tenant_id = f"tenant_rb_{uuid.uuid4().hex[:6]}"

        # 1. Create and activate v1
        svc.create_draft(tenant_id, "pol_001", {"maximum_retry_attempts": 2})
        svc.activate(tenant_id, 1)

        # 2. Create and activate v2
        svc.create_draft(tenant_id, "pol_001", {"maximum_retry_attempts": 5})
        svc.activate(tenant_id, 2)

        active_v2 = svc.get_active(tenant_id)
        assert active_v2 is not None
        assert active_v2.version == 2
        assert active_v2.configuration_json == {"maximum_retry_attempts": 5}

        # 3. Rollback to v1
        v3 = svc.rollback(tenant_id, target_version=1, actor_id="operator_1", reason="Emergency rollback")

        # Rollback must create a NEW version v3
        assert v3.version == 3
        assert v3.status == "ACTIVE"
        assert v3.rollback_source_version == 1
        assert v3.configuration_json == {"maximum_retry_attempts": 2}

        # Historical v1 and v2 must remain unchanged
        hist_v1 = svc.get_version(tenant_id, 1)
        hist_v2 = svc.get_version(tenant_id, 2)
        assert hist_v1 is not None and hist_v1.configuration_json == {"maximum_retry_attempts": 2}
        assert hist_v2 is not None and hist_v2.status == "SUPERSEDED"
    finally:
        db.close()
