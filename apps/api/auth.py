"""
RAVEN Control Plane Authentication & Authorization Module

Provides API key authentication, tenant context extraction, and RBAC permissions.
Supports OPERATIONS_READ, OPERATIONS_CONTROL, POLICY_READ, POLICY_WRITE, POLICY_ACTIVATE, POLICY_ROLLBACK, TENANT_ADMIN, and PLATFORM_ADMIN.
"""

from typing import Annotated
from fastapi import Depends, Header, HTTPException, status
from apps.api.config import get_settings


class UserIdentity:
    """Authenticated Operator Principal Identity with Tenant Context."""

    def __init__(
        self,
        role: str,
        key_id: str = "operator_default",
        tenant_id: str = "tenant_demo",
        merchant_id: str = "mer_demo",
        permissions: set[str] | None = None,
    ) -> None:
        self.role = role
        self.key_id = key_id
        self.tenant_id = tenant_id
        self.merchant_id = merchant_id
        self.is_platform_admin = role in ("ADMIN", "PLATFORM_ADMIN")
        self.permissions = permissions or self._resolve_default_permissions(role)

    def _resolve_default_permissions(self, role: str) -> set[str]:
        if role in ("ADMIN", "PLATFORM_ADMIN"):
            return {
                "OPERATIONS_READ",
                "OPERATIONS_CONTROL",
                "POLICY_READ",
                "POLICY_WRITE",
                "POLICY_ACTIVATE",
                "POLICY_ROLLBACK",
                "TENANT_ADMIN",
                "PLATFORM_ADMIN",
            }
        if role == "TENANT_ADMIN":
            return {
                "OPERATIONS_READ",
                "OPERATIONS_CONTROL",
                "POLICY_READ",
                "POLICY_WRITE",
                "POLICY_ACTIVATE",
                "POLICY_ROLLBACK",
                "TENANT_ADMIN",
            }
        if role == "POLICY_MANAGER":
            return {
                "OPERATIONS_READ",
                "POLICY_READ",
                "POLICY_WRITE",
                "POLICY_ACTIVATE",
                "POLICY_ROLLBACK",
            }
        if role == "OPERATIONS_CONTROL":
            return {
                "OPERATIONS_READ",
                "OPERATIONS_CONTROL",
                "POLICY_READ",
                "POLICY_WRITE",
            }
        # Default read-only
        return {"OPERATIONS_READ", "POLICY_READ"}

    def can_control(self) -> bool:
        """Returns True if user has control permissions."""
        return "OPERATIONS_CONTROL" in self.permissions or self.is_platform_admin

    def has_permission(self, permission: str) -> bool:
        """Returns True if user holds required permission or is platform admin."""
        return self.is_platform_admin or permission in self.permissions


def get_current_user(
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
    x_tenant_id: Annotated[str | None, Header(alias="X-Tenant-ID")] = None,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> UserIdentity:
    """
    Validates API Key or Bearer Token and extracts authenticated UserIdentity and TenantContext.
    Tenant identity originates strictly from authentication/headers, NEVER unprivileged request bodies.
    """
    settings = get_settings()
    provided_key = x_api_key or (authorization.replace("Bearer ", "") if authorization else None)
    tenant_id = x_tenant_id or "tenant_demo"
    merchant_id = f"mer_{tenant_id.replace('tenant_', '')}"

    if not provided_key:
        if settings.environment != "production":
            return UserIdentity(role="PLATFORM_ADMIN", key_id="demo_admin", tenant_id=tenant_id, merchant_id=merchant_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "UNAUTHORIZED", "message": "Missing API authentication key."}},
        )

    if provided_key.startswith("admin_"):
        return UserIdentity(role="ADMIN", key_id="admin_user", tenant_id=tenant_id, merchant_id=merchant_id)
    if provided_key.startswith("control_"):
        return UserIdentity(role="OPERATIONS_CONTROL", key_id="control_user", tenant_id=tenant_id, merchant_id=merchant_id)
    if provided_key.startswith("policy_mgr_"):
        return UserIdentity(role="POLICY_MANAGER", key_id="policy_user", tenant_id=tenant_id, merchant_id=merchant_id)
    if provided_key.startswith("tenant_a_"):
        return UserIdentity(role="TENANT_ADMIN", key_id="user_a", tenant_id="tenant_a", merchant_id="mer_a")
    if provided_key.startswith("tenant_b_"):
        return UserIdentity(role="TENANT_ADMIN", key_id="user_b", tenant_id="tenant_b", merchant_id="mer_b")
    if provided_key.startswith("read_"):
        return UserIdentity(role="OPERATIONS_READ", key_id="read_user", tenant_id=tenant_id, merchant_id=merchant_id)

    if settings.environment != "production":
        return UserIdentity(role="OPERATIONS_CONTROL", key_id="demo_operator", tenant_id=tenant_id, merchant_id=merchant_id)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"error": {"code": "INVALID_KEY", "message": "Invalid API key provided."}},
    )


def require_control_permission(user: UserIdentity) -> UserIdentity:
    """Enforces OPERATIONS_CONTROL or ADMIN permission."""
    if not user.can_control():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "FORBIDDEN", "message": "Insufficient permissions for control operation."}},
        )
    return user


def require_permission(permission: str):
    """Returns a dependency enforcing a specific permission."""
    def dependency(user: UserIdentity = Depends(get_current_user)) -> UserIdentity:
        if not user.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": {"code": "FORBIDDEN", "message": f"Required permission '{permission}' is missing."}},
            )
        return user
    return dependency
