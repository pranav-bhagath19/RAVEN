import uuid
from policies.failover import RegionalFailoverManager
from persistence.redis_store import RedisIdempotencyStore
from persistence.database import get_db


def test_disaster_recovery_stale_policy_sync():
    """Verifies failover manager flags stale policy sync age (>300s)."""
    from datetime import datetime, timezone, timedelta
    from domain.entities.replication import PolicyReplicationState
    from domain.enums import ReplicationStatus
    failover = RegionalFailoverManager()
    stale_time = datetime.now(timezone.utc) - timedelta(seconds=3600)
    stale_state = PolicyReplicationState(
        tenant_id="tenant_dr",
        policy_id="POL_001",
        policy_version="v1",
        policy_hash="hash_01",
        source_region="ap-south-1",
        target_region="us-east-1",
        replication_status=ReplicationStatus.SYNCHRONIZED,
        last_synced_at=stale_time,
    )
    is_fresh = failover.verify_policy_freshness("tenant_dr", stale_state, max_sync_age_seconds=300.0)
    assert is_fresh is False


def test_disaster_recovery_redis_fallback():
    """Verifies Redis disconnection triggers local idempotency fallback."""
    redis_store = RedisIdempotencyStore(redis_url="redis://invalid-host:6379/0")
    key = f"dr_test_key_{uuid.uuid4().hex[:8]}"
    claimed = redis_store.claim(key)
    assert claimed is True


def test_disaster_recovery_db_session_health():
    """Verifies database session generator handles sessions safely."""
    gen = get_db()
    session = next(gen)
    assert session is not None
    session.close()
