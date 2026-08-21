"""
RAVEN Merchant Policy & Audit Trail Domain Entities

Defines MerchantPolicyVersion, PolicyVersionStatus, PolicyAuditAction, and PolicyAuditLog.
Enforces immutable versioning, canonical configuration hashing, and audit lineage.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any
import uuid
from pydantic import BaseModel, Field


class PolicyVersionStatus(str, Enum):
    """Lifecycle status for a policy version."""

    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    ROLLED_BACK = "ROLLED_BACK"


class PolicyAuditAction(str, Enum):
    """Audit action category for policy updates."""

    CREATED = "CREATED"
    VALIDATED = "VALIDATED"
    ACTIVATED = "ACTIVATED"
    DEACTIVATED = "DEACTIVATED"
    ROLLED_BACK = "ROLLED_BACK"
    REJECTED = "REJECTED"


class MerchantPolicyVersion(BaseModel):
    """
    Immutable versioned policy configuration for a tenant.
    HISTORICAL VERSIONS ARE STRICTLY IMMUTABLE.
    """

    policy_id: str = Field(..., description="Parent Policy Identifier, e.g. pol_mer_01H...")
    tenant_id: str = Field(..., description="Associated Tenant ID")
    version: int = Field(..., ge=1, description="Sequential integer version number (1, 2, 3...)")
    status: PolicyVersionStatus = Field(PolicyVersionStatus.DRAFT, description="Version lifecycle status")
    configuration_json: dict[str, Any] = Field(default_factory=dict, description="Policy rule parameter overrides")
    configuration_hash: str = Field(..., description="Canonical SHA-256 hex digest of configuration payload")
    created_by: str = Field("system", description="Actor ID who created this version")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Version creation timestamp in UTC",
    )
    activated_at: datetime | None = Field(None, description="Activation timestamp in UTC if ACTIVE/SUPERSEDED")
    deactivated_at: datetime | None = Field(None, description="Deactivation timestamp in UTC if SUPERSEDED")
    parent_version: int | None = Field(None, description="Preceding version number")
    rollback_source_version: int | None = Field(None, description="Original version number if created via rollback")


class PolicyAuditLog(BaseModel):
    """
    Audit log entry for policy configuration mutations.
    NEVER LOGS SENSITIVE SECRETS, API KEYS, OR PII.
    """

    audit_id: str = Field(default_factory=lambda: f"aud_{uuid.uuid4().hex[:12]}", description="Unique Audit Entry ID")
    tenant_id: str = Field(..., description="Associated Tenant ID")
    policy_id: str = Field(..., description="Associated Policy ID")
    policy_version: int = Field(..., description="Target Policy Version Number")
    action: PolicyAuditAction = Field(..., description="Audit action performed")
    actor_id: str = Field(..., description="User or system actor ID")
    previous_version: int | None = Field(None, description="Previous version number if applicable")
    new_version: int | None = Field(None, description="New version number if applicable")
    configuration_hash: str = Field(..., description="SHA-256 hash of configuration at action time")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Audit entry timestamp in UTC",
    )
    reason: str = Field(..., description="Human-readable explanation of action")
    request_id: str = Field("req_unknown", description="Associated API request ID")
