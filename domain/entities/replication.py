"""
RAVEN Replication Domain Entities

Defines domain models for PolicyReplicationState, ReplicationCheckpoint, PolicyConflictRecord,
and ReplicationEventRecord for multi-region policy synchronization.
"""

from datetime import datetime, timezone
import uuid
from typing import Any
from pydantic import BaseModel, Field
from domain.enums import ReconciliationStrategy, ReplicationStatus


class PolicyReplicationState(BaseModel):
    """
    State tracking policy replication status for a specific tenant and region.
    """

    id: str = Field(default_factory=lambda: f"repl_{uuid.uuid4().hex[:12]}", description="Unique replication state ID")
    tenant_id: str = Field(..., description="Target Tenant / Merchant ID")
    policy_id: str = Field(..., description="Target Policy Rule ID")
    policy_version: str = Field(..., description="Replicated policy version string")
    policy_hash: str = Field(..., description="SHA-256 canonical configuration hash")
    parent_version: str | None = Field(default=None, description="Parent version node string")
    source_region: str = Field(..., description="Source origin region ID")
    target_region: str = Field(..., description="Target destination region ID")
    status: ReplicationStatus = Field(default=ReplicationStatus.PENDING, description="Replication status")
    synced_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Synchronization timestamp in UTC",
    )
    error_message: str | None = Field(default=None, description="Detailed failure or error description")


class ReplicationCheckpoint(BaseModel):
    """
    Checkpoint record tracking restartable synchronization progress across regions.
    """

    checkpoint_id: str = Field(default_factory=lambda: f"chk_{uuid.uuid4().hex[:12]}", description="Unique checkpoint ID")
    tenant_id: str = Field(..., description="Tenant / Merchant ID scope")
    source_region: str = Field(..., description="Source origin region ID")
    target_region: str = Field(..., description="Target destination region ID")
    last_synced_version: str = Field(..., description="Last successfully synchronized version string")
    sequence_number: int = Field(default=0, ge=0, description="Monotonically increasing sequence number")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Checkpoint creation timestamp in UTC",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Checkpoint last updated timestamp in UTC",
    )


class PolicyConflictRecord(BaseModel):
    """
    Audit record for detected regional policy state conflicts.
    """

    conflict_id: str = Field(default_factory=lambda: f"cnf_{uuid.uuid4().hex[:12]}", description="Unique conflict ID")
    tenant_id: str = Field(..., description="Tenant / Merchant ID scope")
    policy_id: str = Field(..., description="Policy rule ID in conflict")
    region_a: str = Field(..., description="First conflicting region")
    region_b: str = Field(..., description="Second conflicting region")
    version_a: str = Field(..., description="Policy version in Region A")
    version_b: str = Field(..., description="Policy version in Region B")
    hash_a: str = Field(..., description="SHA-256 hash in Region A")
    hash_b: str = Field(..., description="SHA-256 hash in Region B")
    conflict_reason: str = Field(..., description="Detailed explanation of conflict")
    is_resolved: bool = Field(default=False, description="Whether conflict has been resolved")
    resolution_strategy: ReconciliationStrategy | None = Field(default=None, description="Applied reconciliation strategy")
    resolved_at: datetime | None = Field(default=None, description="Resolution timestamp in UTC")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Conflict detection timestamp in UTC",
    )


class ReplicationEventRecord(BaseModel):
    """
    Immutable replication event representation for event/state replication.
    """

    event_id: str = Field(default_factory=lambda: f"repevt_{uuid.uuid4().hex[:12]}", description="Unique replication event ID")
    tenant_id: str = Field(..., description="Tenant / Merchant ID scope")
    policy_id: str = Field(..., description="Associated policy ID")
    policy_version: str = Field(..., description="Associated policy version")
    policy_hash: str = Field(..., description="SHA-256 hash")
    source_region: str = Field(..., description="Originating source region")
    target_region: str = Field(..., description="Destination target region")
    sequence_number: int = Field(..., ge=0, description="Sequence number for replay protection")
    payload: dict[str, Any] = Field(default_factory=dict, description="Replication payload contents")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Event creation timestamp in UTC",
    )
