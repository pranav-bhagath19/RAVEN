"""
RAVEN Tenant Context Module

Provides strongly-typed TenantContext container derived strictly from authenticated user identity.
Prevents unprivileged request body tenant override attacks.
"""

from pydantic import BaseModel, Field


class TenantContext(BaseModel):
    """
    Strongly typed Tenant Context provided to operations, repositories, and services.
    Tenant identity originates strictly from authenticated credentials.
    """

    tenant_id: str = Field(..., description="Authenticated Tenant ID")
    merchant_id: str = Field(..., description="Authenticated Merchant ID")
    permissions: set[str] = Field(default_factory=set, description="Granted permission scope tags")
    is_platform_admin: bool = Field(False, description="Flag indicating cross-tenant system admin access")

    def has_access_to(self, target_tenant_id: str) -> bool:
        """Returns True if context matches target tenant or holds platform admin authority."""
        if self.is_platform_admin:
            return True
        return self.tenant_id == target_tenant_id
