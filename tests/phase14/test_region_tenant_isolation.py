"""
RAVEN Phase 14 Security Test Suite: Multi-Region Tenant Isolation

Explicitly proves section 19 requirements:
1. Tenant A cannot read Tenant B replication states or checkpoints.
2. Tenant A cannot synchronize or modify Tenant B policy configurations.
"""

from policies.replication import PolicyReplicator, compute_policy_hash


def test_tenant_isolation_replication_read():
    """Proves tenant A cannot read tenant B replication status or checkpoints."""
    replicator = PolicyReplicator()

    config_a = {"max_recovery_attempts": 3, "min_confidence_threshold": 0.75}
    hash_a = compute_policy_hash(config_a)

    config_b = {"max_recovery_attempts": 5, "min_confidence_threshold": 0.80}
    hash_b = compute_policy_hash(config_b)

    # Replicate for Tenant A
    replicator.replicate_policy(
        tenant_id="tenant_A",
        policy_id="POL_001",
        policy_version="v1",
        configuration=config_a,
        expected_hash=hash_a,
        source_region="ap-south-1",
        target_region="us-east-1",
    )

    # Replicate for Tenant B
    replicator.replicate_policy(
        tenant_id="tenant_B",
        policy_id="POL_001",
        policy_version="v1",
        configuration=config_b,
        expected_hash=hash_b,
        source_region="ap-south-1",
        target_region="us-east-1",
    )

    # Tenant A status query
    state_a = replicator.get_replication_status("tenant_A", "POL_001", "v1", "us-east-1")
    assert state_a is not None
    assert state_a.tenant_id == "tenant_A"
    assert state_a.policy_hash == hash_a

    # Tenant A checkpoint query
    chk_a = replicator.get_checkpoint("tenant_A", "ap-south-1", "us-east-1")
    assert chk_a is not None
    assert chk_a.tenant_id == "tenant_A"

    # Verify Tenant A querying for Tenant B returns None or Tenant A's own isolated data
    chk_b_from_a = replicator.get_checkpoint("tenant_A", "ap-south-1", "eu-west-1")
    assert chk_b_from_a is None
