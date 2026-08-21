"""
RAVEN Tenant & Merchant Multi-Tenancy Domain Entities

Defines Tenant domain entity and TenantStatus enum for multi-tenant isolation.
"""

from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, Field


class TenantStatus(str, Enum):
    """Lifecycle status for tenant accounts."""

    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    DISABLED = "DISABLED"


class Tenant(BaseModel):
    """
    Tenant domain entity representing isolated merchant organization.
    Every merchant belongs to exactly one tenant.
    """

    tenant_id: str = Field(..., description="Unique Tenant ID, e.g. ten_01H...")
    merchant_id: str = Field(..., description="Associated Merchant ID, e.g. mer_01H...")
    name: str = Field(..., description="Organization or merchant business name")
    status: TenantStatus = Field(TenantStatus.ACTIVE, description="Tenant lifecycle status")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Tenant creation timestamp in UTC",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last updated timestamp in UTC",
    )
