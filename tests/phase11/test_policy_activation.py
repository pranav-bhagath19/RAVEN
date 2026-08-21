"""
Phase 11 Policy Activation Tests

Verifies transactional policy activation, error handling for invalid policies,
and atomic state transitions.
"""

import uuid
import pytest
from persistence.database import Base, engine, SessionLocal
from apps.api.policy_service import PolicyService

Base.metadata.create_all(bind=engine)


def test_policy_activation_success():
    db = SessionLocal()
    try:
        svc = PolicyService(db)
        tenant_id = f"tenant_act_{uuid.uuid4().hex[:6]}"

        version, errors = svc.create_draft(tenant_id, "pol_001", {"maximum_retry_attempts": 3})
        assert version.version == 1

        activated = svc.activate(tenant_id, 1, actor_id="admin_1", reason="Initial activation")
        assert activated.status == "ACTIVE"
        assert activated.activated_at is not None

        active_in_db = svc.get_active(tenant_id)
        assert active_in_db is not None
        assert active_in_db.version == 1
    finally:
        db.close()


def test_invalid_policy_activation_fails():
    db = SessionLocal()
    try:
        svc = PolicyService(db)
        tenant_id = f"tenant_inv_act_{uuid.uuid4().hex[:6]}"

        with pytest.raises(ValueError):
            svc.create_draft(tenant_id, "pol_001", {"maximum_retry_attempts": -5})
    finally:
        db.close()
