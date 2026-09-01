"""
RAVEN Policy Reconciliation Subsystem

Deterministically resolves regional policy conflicts by evaluating version lineage trees,
validating SHA-256 configuration hashes, and enforcing fail-closed behavior on ambiguity.
"""

from datetime import datetime, timezone
from domain.entities.replication import PolicyConflictRecord
from domain.enums import ReconciliationStrategy


class PolicyReconciler:
    """
    Executes deterministic policy reconciliation between conflicting regional policy states.
    """

    def reconcile(
        self,
        conflict: PolicyConflictRecord,
        version_lineage: list[dict[str, str]],  # list of {"version": str, "parent": str, "hash": str}
    ) -> PolicyConflictRecord:
        """
        Reconciles a PolicyConflictRecord using version tree lineage evaluation.
        If a safe authoritative descendant is identified, resolves the conflict.
        Otherwise, sets FAIL_CLOSED resolution and raises ValueError.
        """
        if conflict.is_resolved:
            return conflict

        # Build parent map and hash lookup
        parent_map = {item["version"]: item.get("parent") for item in version_lineage}
        hash_map = {item["version"]: item.get("hash") for item in version_lineage}

        v_a = conflict.version_a
        v_b = conflict.version_b

        # Check if v_b is an authoritative descendant of v_a
        curr = v_b
        is_b_descendant_of_a = False
        while curr in parent_map and parent_map[curr] is not None:
            if parent_map[curr] == v_a:
                is_b_descendant_of_a = True
                break
            curr = parent_map[curr]  # type: ignore[assignment]

        # Check if v_a is an authoritative descendant of v_b
        curr = v_a
        is_a_descendant_of_b = False
        while curr in parent_map and parent_map[curr] is not None:
            if parent_map[curr] == v_b:
                is_a_descendant_of_b = True
                break
            curr = parent_map[curr]  # type: ignore[assignment]

        if is_b_descendant_of_a and hash_map.get(v_b) == conflict.hash_b:
            conflict.is_resolved = True
            conflict.resolution_strategy = ReconciliationStrategy.AUTHORITATIVE_DESCENDANT
            conflict.resolved_at = datetime.now(timezone.utc)
            return conflict

        if is_a_descendant_of_b and hash_map.get(v_a) == conflict.hash_a:
            conflict.is_resolved = True
            conflict.resolution_strategy = ReconciliationStrategy.AUTHORITATIVE_DESCENDANT
            conflict.resolved_at = datetime.now(timezone.utc)
            return conflict

        # Cannot establish safe lineage: FAIL CLOSED
        conflict.resolution_strategy = ReconciliationStrategy.FAIL_CLOSED
        raise ValueError(
            f"Policy reconciliation failed for tenant '{conflict.tenant_id}': "
            f"Ambiguous lineage between {conflict.region_a} (v{v_a}) and {conflict.region_b} (v{v_b}). System MUST fail closed."
        )
