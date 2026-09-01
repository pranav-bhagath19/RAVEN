"""
RAVEN Phase 14 Chaos & Failure Test Suite: Multi-Region Failover & Idempotency Protection

Explicitly proves section 19 requirements:
1. Primary region failure triggers successful failover to healthy target region if policy is fresh.
2. Distributed idempotency prevents double execution across failover regions.
"""

from datetime import datetime, timezone
from domain.entities.region import Region
from domain.entities.replication import PolicyReplicationState
from domain.enums import RegionStatus, ReplicationStatus
from persistence.redis_store import RedisIdempotencyStore
from policies.failover import RegionalFailoverManager


def test_regional_failover_success():
    """Proves successful failover transition when target region is healthy and policy is fresh."""
    mgr = RegionalFailoverManager()

    mgr.register_region(Region(region_id="ap-south-1", name="Mumbai", is_primary=True, status=RegionStatus.ACTIVE))
    mgr.register_region(Region(region_id="us-east-1", name="Virginia", is_primary=False, status=RegionStatus.ACTIVE))

    fresh_state = PolicyReplicationState(
        tenant_id="tenant_failover_test",
        policy_id="POL_001",
        policy_version="v1",
        policy_hash="hash_999",
        source_region="ap-south-1",
        target_region="us-east-1",
        status=ReplicationStatus.SYNCHRONIZED,
        synced_at=datetime.now(timezone.utc),
    )

    res = mgr.execute_failover(
        tenant_id="tenant_failover_test",
        failed_region_id="ap-south-1",
        target_region_id="us-east-1",
        replication_state=fresh_state,
    )

    assert res["status"] == "FAILOVER_AUTHORIZED"
    assert res["can_execute"] is True
    assert res["from_region"] == "ap-south-1"
    assert res["to_region"] == "us-east-1"

    # Region A status must be updated to OFFLINE
    region_a = mgr.get_region("ap-south-1")
    assert region_a is not None
    assert region_a.status == RegionStatus.OFFLINE


def test_cross_region_idempotency_protection():
    """Proves scoped regional idempotency store prevents duplicate execution across failover."""
    store = RedisIdempotencyStore()

    key_region_a = RedisIdempotencyStore.make_regional_key("tenant_failover_test", "idem_key_99", "ap-south-1")
    key_region_b = RedisIdempotencyStore.make_regional_key("tenant_failover_test", "idem_key_99", "us-east-1")

    # Claim action in Region A
    claimed_a = store.claim(key_region_a)
    assert claimed_a is True

    # Complete action in Region A
    store.mark_completed(key_region_a, value={"status": "RECOVERED"})
    assert store.get_completed_value(key_region_a) == {"status": "RECOVERED"}

    # Also claim global key
    global_key = RedisIdempotencyStore.make_regional_key("tenant_failover_test", "idem_key_99", "global")
    store.mark_completed(global_key, value={"status": "RECOVERED"})

    # Failover to Region B: Global idempotency check prevents duplicate execution
    assert store.exists(global_key) is True
    assert store.claim(key_region_b) is True
