"""
Phase 11 Tenant Isolation Tests

Verifies that domain entities, repositories, and context maintain strict tenant isolation.
Cross-tenant access attempts must fail closed.
"""

from apps.api.tenant_context import TenantContext
from domain.entities.tenant import Tenant, TenantStatus


def test_tenant_entity_creation():
    tenant = Tenant(tenant_id="tenant_a", merchant_id="mer_a", name="Acme Corp", status=TenantStatus.ACTIVE)
    assert tenant.tenant_id == "tenant_a"
    assert tenant.status == TenantStatus.ACTIVE


def test_tenant_context_isolation_check():
    ctx_a = TenantContext(tenant_id="tenant_a", merchant_id="mer_a", permissions={"OPERATIONS_READ"})
    ctx_admin = TenantContext(tenant_id="tenant_admin", merchant_id="mer_admin", permissions={"PLATFORM_ADMIN"}, is_platform_admin=True)

    assert ctx_a.has_access_to("tenant_a") is True
    assert ctx_a.has_access_to("tenant_b") is False
    assert ctx_admin.has_access_to("tenant_b") is True
