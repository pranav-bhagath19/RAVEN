"""
RAVEN Phase 14 Security Test Suite: Canonical Hash Integrity & Tamper Protection

Explicitly proves section 19 requirements:
1. Valid canonical SHA-256 hash -> accepted as SYNCHRONIZED.
2. Modified/tampered policy payload -> rejected with ValueError and state set to FAILED.
"""

import pytest
from domain.enums import ReplicationStatus
from policies.replication import PolicyReplicator, compute_policy_hash


def test_replication_valid_hash_integrity():
    """Proves valid policy payload hash is accepted and recorded as SYNCHRONIZED."""
    replicator = PolicyReplicator()
    config = {"max_recovery_attempts": 3, "min_confidence": 0.75}
    valid_hash = compute_policy_hash(config)

    state = replicator.replicate_policy(
        tenant_id="tenant_hash_test",
        policy_id="POL_002",
        policy_version="v1",
        configuration=config,
        expected_hash=valid_hash,
        source_region="ap-south-1",
        target_region="us-east-1",
    )

    assert state.status == ReplicationStatus.SYNCHRONIZED
    assert state.policy_hash == valid_hash


def test_replication_tampered_payload_hash_rejection():
    """Proves tampered payload hash triggers immediate failure and exception."""
    replicator = PolicyReplicator()
    config = {"max_recovery_attempts": 3, "min_confidence": 0.75}

    # Tampered expected hash
    fake_hash = "0000000000000000000000000000000000000000000000000000000000000000"

    with pytest.raises(ValueError) as exc_info:
        replicator.replicate_policy(
            tenant_id="tenant_hash_test",
            policy_id="POL_002",
            policy_version="v1",
            configuration=config,
            expected_hash=fake_hash,
            source_region="ap-south-1",
            target_region="us-east-1",
        )

    assert "hash validation failed" in str(exc_info.value).lower()

    state = replicator.get_replication_status("tenant_hash_test", "POL_002", "v1", "us-east-1")
    assert state is not None
    assert state.status == ReplicationStatus.FAILED
    assert "hash mismatch" in state.error_message.lower()
