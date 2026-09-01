"""
RAVEN Phase 14 Security Test Suite: Stale Policy Read Protection & Fail-Closed Behavior

Explicitly proves section 19 requirements:
1. Policy replication states exceeding max sync age (e.g. 300s) are marked STALE.
2. Stale policies fail freshness verification, preventing unauthorized execution.
"""

from datetime import datetime, timedelta, timezone
from domain.entities.replication import PolicyReplicationState
from domain.enums import ReplicationStatus
from policies.failover import RegionalFailoverManager


def test_stale_policy_freshness_check():
    """Proves stale policy state exceeding max sync age fails freshness check."""
    mgr = RegionalFailoverManager()

    stale_time = datetime.now(timezone.utc) - timedelta(seconds=400)
    stale_state = PolicyReplicationState(
        tenant_id="tenant_stale_test",
        policy_id="POL_001",
        policy_version="v1",
        policy_hash="hash_12345",
        source_region="ap-south-1",
        target_region="us-east-1",
        status=ReplicationStatus.SYNCHRONIZED,
        synced_at=stale_time,
    )

    is_fresh = mgr.verify_policy_freshness(
        tenant_id="tenant_stale_test",
        replication_state=stale_state,
        max_sync_age_seconds=300.0,
    )

    assert is_fresh is False
    assert stale_state.status == ReplicationStatus.STALE
    assert "sync age" in stale_state.error_message.lower()


def test_stale_policy_failover_rejection():
    """Proves failover request using stale policy state is rejected."""
    mgr = RegionalFailoverManager()
    mgr.update_region_status("ap-south-1", status="OFFLINE", health_score=0.0)
    mgr.update_region_status("us-east-1", status="ACTIVE", health_score=1.0)

    stale_time = datetime.now(timezone.utc) - timedelta(seconds=500)
    stale_state = PolicyReplicationState(
        tenant_id="tenant_stale_test",
        policy_id="POL_001",
        policy_version="v1",
        policy_hash="hash_12345",
        source_region="ap-south-1",
        target_region="us-east-1",
        status=ReplicationStatus.SYNCHRONIZED,
        synced_at=stale_time,
    )

    res = mgr.execute_failover(
        tenant_id="tenant_stale_test",
        failed_region_id="ap-south-1",
        target_region_id="us-east-1",
        replication_state=stale_state,
    )

    assert res["status"] == "FAILOVER_REJECTED"
    assert res["can_execute"] is False
    assert "stale or unverified" in res["reason"].lower()
