"""
RAVEN Phase 14 Security Test Suite: Replication Idempotency

Explicitly proves section 19 requirements:
Replication event X received N times results in 1 logical state transition.
Does not create duplicate policy versions or corrupt lineage history.
"""

from domain.enums import ReplicationStatus
from policies.replication import PolicyReplicator, compute_policy_hash


def test_replication_idempotent_behavior():
    """Proves repeated replication calls for identical policy version return existing state."""
    replicator = PolicyReplicator()
    config = {"max_recovery_attempts": 3, "min_confidence": 0.75}
    valid_hash = compute_policy_hash(config)

    # First replication call
    state1 = replicator.replicate_policy(
        tenant_id="tenant_idem_test",
        policy_id="POL_001",
        policy_version="v1",
        configuration=config,
        expected_hash=valid_hash,
        source_region="ap-south-1",
        target_region="us-east-1",
    )
    assert state1.status == ReplicationStatus.SYNCHRONIZED

    # Duplicate call 1
    state2 = replicator.replicate_policy(
        tenant_id="tenant_idem_test",
        policy_id="POL_001",
        policy_version="v1",
        configuration=config,
        expected_hash=valid_hash,
        source_region="ap-south-1",
        target_region="us-east-1",
    )

    # Duplicate call 2
    state3 = replicator.replicate_policy(
        tenant_id="tenant_idem_test",
        policy_id="POL_001",
        policy_version="v1",
        configuration=config,
        expected_hash=valid_hash,
        source_region="ap-south-1",
        target_region="us-east-1",
    )

    assert state1.id == state2.id == state3.id
    assert len(replicator.replications) == 1
