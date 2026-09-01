"""
RAVEN Operations Policy Replication Router Module

Exposes operational telemetry, checkpoint discovery, conflict audit, and deterministic policy reconciliation endpoints:
GET  /api/v1/operations/replication/status
GET  /api/v1/operations/replication/checkpoints
GET  /api/v1/operations/policies/{policy_id}/replication
GET  /api/v1/operations/policies/{policy_id}/conflicts
POST /api/v1/operations/policies/{policy_id}/reconcile
"""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from apps.api.auth import UserIdentity, require_permission
from policies.conflict import PolicyConflictDetector
from policies.reconciliation import PolicyReconciler
from policies.replication import PolicyReplicator

router = APIRouter(prefix="/api/v1/operations", tags=["Distributed Policy Synchronization"])

# Shared in-memory instances for API operations
_shared_replicator = PolicyReplicator()
_shared_conflict_detector = PolicyConflictDetector()
_shared_reconciler = PolicyReconciler()


class ReconcileRequestPayload(BaseModel):
    conflict_id: str = Field(..., description="Target Policy Conflict ID to reconcile")
    version_lineage: list[dict[str, str]] = Field(
        default_factory=list,
        description="Version lineage tree array [{'version': 'v2', 'parent': 'v1', 'hash': '...'}]",
    )


@router.get("/replication/status", response_model=dict[str, Any])
def get_replication_status(
    user: UserIdentity = Depends(require_permission("REPLICATION_READ")),
) -> dict[str, Any]:
    """Returns general multi-region replication status summary."""
    active_conflicts = _shared_conflict_detector.list_active_conflicts(tenant_id=user.tenant_id)
    return {
        "tenant_id": user.tenant_id,
        "total_replications": len(_shared_replicator.replications),
        "total_checkpoints": len(_shared_replicator.checkpoints),
        "active_conflicts_count": len(active_conflicts),
        "sync_health": "HEALTHY" if len(active_conflicts) == 0 else "DEGRADED_CONFLICT",
    }


@router.get("/replication/checkpoints", response_model=list[dict[str, Any]])
def list_replication_checkpoints(
    user: UserIdentity = Depends(require_permission("REPLICATION_READ")),
) -> list[dict[str, Any]]:
    """Lists replication checkpoints scoped to authenticated tenant."""
    res = []
    for chk in _shared_replicator.checkpoints.values():
        if chk.tenant_id == user.tenant_id:
            res.append(chk.model_dump(mode="json"))
    return res


@router.get("/policies/{policy_id}/replication", response_model=list[dict[str, Any]])
def get_policy_replication_history(
    policy_id: str,
    user: UserIdentity = Depends(require_permission("REPLICATION_READ")),
) -> list[dict[str, Any]]:
    """Retrieves policy replication history for a specific policy ID."""
    res = []
    for state in _shared_replicator.replications.values():
        if state.tenant_id == user.tenant_id and state.policy_id == policy_id:
            res.append(state.model_dump(mode="json"))
    return res


@router.get("/policies/{policy_id}/conflicts", response_model=list[dict[str, Any]])
def get_policy_conflicts(
    policy_id: str,
    user: UserIdentity = Depends(require_permission("REPLICATION_READ")),
) -> list[dict[str, Any]]:
    """Lists policy conflicts for a specific policy ID."""
    res = []
    for c in _shared_conflict_detector.conflicts:
        if c.tenant_id == user.tenant_id and c.policy_id == policy_id:
            res.append(c.model_dump(mode="json"))
    return res


@router.post("/policies/{policy_id}/reconcile", response_model=dict[str, Any])
def reconcile_policy_conflict(
    policy_id: str,
    payload: ReconcileRequestPayload,
    user: UserIdentity = Depends(require_permission("RECONCILIATION_CONTROL")),
) -> dict[str, Any]:
    """Executes deterministic reconciliation on a policy conflict."""
    conflict = _shared_conflict_detector.get_conflict(payload.conflict_id)
    if not conflict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND", "message": f"Conflict '{payload.conflict_id}' not found."}},
        )

    if conflict.tenant_id != user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "FORBIDDEN", "message": "Cross-tenant conflict reconciliation forbidden."}},
        )

    try:
        resolved = _shared_reconciler.reconcile(conflict, payload.version_lineage)
        return resolved.model_dump(mode="json")
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "RECONCILIATION_FAILED", "message": str(exc)}},
        )
