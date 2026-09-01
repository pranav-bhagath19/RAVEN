"""
RAVEN Policy Replication & Canonical Hash Integrity Subsystem

Implements multi-region policy version replication, canonical SHA-256 hash verification,
checkpoint tracking, and immutable policy history preservation.
"""

from datetime import datetime, timezone
import hashlib
import json
from typing import Any
from domain.entities.replication import PolicyReplicationState, ReplicationCheckpoint, ReplicationEventRecord
from domain.enums import ReplicationStatus


def compute_policy_hash(configuration: dict[str, Any]) -> str:
    """
    Computes a canonical SHA-256 hash of a policy configuration dictionary.
    Keys are sorted to ensure deterministic hashing across regions.
    """
    canonical_json = json.dumps(configuration, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


class PolicyReplicator:
    """
    Manages tenant-isolated, idempotent policy replication and SHA-256 hash integrity checks across regions.
    """

    def __init__(self) -> None:
        # In-memory stores for multi-region replication state
        self.replications: dict[str, PolicyReplicationState] = {}
        self.checkpoints: dict[str, ReplicationCheckpoint] = {}
        self.events: list[ReplicationEventRecord] = []

    def _checkpoint_key(self, tenant_id: str, source_region: str, target_region: str) -> str:
        return f"{tenant_id}:{source_region}:{target_region}"

    def replicate_policy(
        self,
        tenant_id: str,
        policy_id: str,
        policy_version: str,
        configuration: dict[str, Any],
        expected_hash: str,
        source_region: str,
        target_region: str,
        parent_version: str | None = None,
        sequence_number: int = 1,
    ) -> PolicyReplicationState:
        """
        Replicates a policy configuration payload from source_region to target_region.
        Enforces canonical SHA-256 hash verification and idempotent state tracking.
        """
        repl_key = f"{tenant_id}:{policy_id}:{policy_version}:{source_region}:{target_region}"

        # 1. Check idempotency: If already replicated with same parameters, return existing state
        if repl_key in self.replications:
            existing = self.replications[repl_key]
            if existing.status == ReplicationStatus.SYNCHRONIZED:
                return existing

        # 2. Canonical SHA-256 Hash Verification
        computed_hash = compute_policy_hash(configuration)
        if computed_hash != expected_hash:
            fail_state = PolicyReplicationState(
                tenant_id=tenant_id,
                policy_id=policy_id,
                policy_version=policy_version,
                policy_hash=computed_hash,
                parent_version=parent_version,
                source_region=source_region,
                target_region=target_region,
                status=ReplicationStatus.FAILED,
                error_message=f"Canonical hash mismatch: expected {expected_hash}, computed {computed_hash}",
            )
            self.replications[repl_key] = fail_state
            raise ValueError(f"Policy replication hash validation failed: {fail_state.error_message}")

        # 3. Create replication event record (immutable append-only)
        event = ReplicationEventRecord(
            tenant_id=tenant_id,
            policy_id=policy_id,
            policy_version=policy_version,
            policy_hash=computed_hash,
            source_region=source_region,
            target_region=target_region,
            sequence_number=sequence_number,
            payload=configuration,
        )
        self.events.append(event)

        # 4. Create successful replication state
        sync_state = PolicyReplicationState(
            tenant_id=tenant_id,
            policy_id=policy_id,
            policy_version=policy_version,
            policy_hash=computed_hash,
            parent_version=parent_version,
            source_region=source_region,
            target_region=target_region,
            status=ReplicationStatus.SYNCHRONIZED,
            synced_at=datetime.now(timezone.utc),
        )
        self.replications[repl_key] = sync_state

        # 5. Update checkpoint
        chk_key = self._checkpoint_key(tenant_id, source_region, target_region)
        self.checkpoints[chk_key] = ReplicationCheckpoint(
            tenant_id=tenant_id,
            source_region=source_region,
            target_region=target_region,
            last_synced_version=policy_version,
            sequence_number=sequence_number,
        )

        return sync_state

    def get_replication_status(
        self,
        tenant_id: str,
        policy_id: str,
        policy_version: str,
        target_region: str,
    ) -> PolicyReplicationState | None:
        """Retrieves replication status for a specific tenant policy in a region."""
        for state in self.replications.values():
            if (
                state.tenant_id == tenant_id
                and state.policy_id == policy_id
                and state.policy_version == policy_version
                and state.target_region == target_region
            ):
                return state
        return None

    def get_checkpoint(
        self,
        tenant_id: str,
        source_region: str,
        target_region: str,
    ) -> ReplicationCheckpoint | None:
        """Retrieves replication checkpoint for a tenant between source and target regions."""
        chk_key = self._checkpoint_key(tenant_id, source_region, target_region)
        return self.checkpoints.get(chk_key)
