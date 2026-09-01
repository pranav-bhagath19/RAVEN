"""
RAVEN Policy Conflict Detection Subsystem

Identifies divergent policy versions, hash mismatches, or un-synchronized regional policy configurations.
Enforces explicit conflict recording to prevent silent overwrites or arbitrary region selection.
"""

from domain.entities.replication import PolicyConflictRecord


class PolicyConflictDetector:
    """
    Detects regional policy conflicts across multi-region deployment nodes.
    """

    def __init__(self) -> None:
        self.conflicts: list[PolicyConflictRecord] = []

    def detect_conflict(
        self,
        tenant_id: str,
        policy_id: str,
        region_a: str,
        region_b: str,
        version_a: str,
        version_b: str,
        hash_a: str,
        hash_b: str,
        parent_a: str | None = None,
        parent_b: str | None = None,
    ) -> PolicyConflictRecord | None:
        """
        Evaluates regional policy state snapshots for conflicts.
        Returns a PolicyConflictRecord if a conflict is detected, else None.
        """
        # Condition 1: Same version string with different configuration hashes (Hash Mismatch / State Tamper)
        if version_a == version_b and hash_a != hash_b:
            conflict = PolicyConflictRecord(
                tenant_id=tenant_id,
                policy_id=policy_id,
                region_a=region_a,
                region_b=region_b,
                version_a=version_a,
                version_b=version_b,
                hash_a=hash_a,
                hash_b=hash_b,
                conflict_reason=f"Hash mismatch on version {version_a}: Region {region_a} ({hash_a[:8]}) vs Region {region_b} ({hash_b[:8]})",
            )
            self.conflicts.append(conflict)
            return conflict

        # Condition 2: Version mismatch without valid parent lineage (Divergent History)
        if version_a != version_b and parent_a != version_b and parent_b != version_a:
            conflict = PolicyConflictRecord(
                tenant_id=tenant_id,
                policy_id=policy_id,
                region_a=region_a,
                region_b=region_b,
                version_a=version_a,
                version_b=version_b,
                hash_a=hash_a,
                hash_b=hash_b,
                conflict_reason=f"Divergent policy version lineage without parent relationship: {region_a} (v{version_a}) vs {region_b} (v{version_b})",
            )
            self.conflicts.append(conflict)
            return conflict

        return None

    def list_active_conflicts(self, tenant_id: str | None = None) -> list[PolicyConflictRecord]:
        """Lists active, unresolved policy conflicts."""
        if tenant_id:
            return [c for c in self.conflicts if c.tenant_id == tenant_id and not c.is_resolved]
        return [c for c in self.conflicts if not c.is_resolved]

    def get_conflict(self, conflict_id: str) -> PolicyConflictRecord | None:
        """Retrieves a conflict record by conflict_id."""
        for c in self.conflicts:
            if c.conflict_id == conflict_id:
                return c
        return None
