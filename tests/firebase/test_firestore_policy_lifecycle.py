"""
Unit Tests for Firestore Merchant Policy Lifecycle, Atomic Rollbacks, and Audit Logging
"""

import uuid
import pytest
from domain.entities.merchant_policy import PolicyAuditAction, PolicyVersionStatus
from persistence.firebase import reset_firestore_emulator
from persistence.firestore_store import FirestoreMerchantPolicyRepository


@pytest.fixture(autouse=True)
def setup_firestore():
    reset_firestore_emulator()


def test_firestore_policy_versioning_and_activation():
    repo = FirestoreMerchantPolicyRepository()
    tenant_id = f"tenant_pol_{uuid.uuid4().hex[:8]}"

    # 1. Create v1 draft
    v1 = repo.create_draft_version(
        tenant_id=tenant_id,
        policy_id="pol_main",
        configuration_json={"max_retry_attempts": 3, "pause_threshold_pause": 500000},
        actor_id="admin_1",
    )
    assert v1.version == 1
    assert v1.status == PolicyVersionStatus.DRAFT

    # 2. Activate v1
    v1_active = repo.activate_version(tenant_id=tenant_id, version=1, actor_id="admin_1")
    assert v1_active.status == PolicyVersionStatus.ACTIVE

    active = repo.get_active_policy(tenant_id)
    assert active is not None
    assert active.version == 1

    # 3. Create v2 draft & activate
    v2 = repo.create_draft_version(
        tenant_id=tenant_id,
        policy_id="pol_main",
        configuration_json={"max_retry_attempts": 5, "pause_threshold_pause": 1000000},
        actor_id="admin_2",
    )
    assert v2.version == 2

    v2_active = repo.activate_version(tenant_id=tenant_id, version=2, actor_id="admin_2")
    assert v2_active.status == PolicyVersionStatus.ACTIVE

    # v1 must be SUPERSEDED
    v1_old = repo.get_policy_version(tenant_id, 1)
    assert v1_old is not None
    assert v1_old.status == PolicyVersionStatus.SUPERSEDED

    # 4. Rollback to v1 (creates v3 with v1 config)
    v3 = repo.rollback_to_version(tenant_id=tenant_id, target_version=1, actor_id="admin_3")
    assert v3.version == 3
    assert v3.status == PolicyVersionStatus.ACTIVE
    assert v3.rollback_source_version == 1
    assert v3.configuration_json == v1.configuration_json

    # Audit log check
    logs = repo.list_audit_logs(tenant_id)
    assert len(logs) >= 4
    actions = [log.action for log in logs]
    assert PolicyAuditAction.ROLLED_BACK in actions
    assert PolicyAuditAction.ACTIVATED in actions
