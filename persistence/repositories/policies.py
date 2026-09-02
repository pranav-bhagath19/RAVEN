"""
RAVEN Merchant Policy Database Repository

Firestore-backed repository implementation for multi-tenant merchant policy configurations and audit logs.
"""

from typing import Any
from domain.entities.merchant_policy import MerchantPolicyVersion, PolicyAuditLog
from persistence.firestore_store import FirestoreMerchantPolicyRepository


class MerchantPolicyRepository:
    """Repository managing tenant merchant policy versions and audit logs backed by Firestore."""

    def __init__(self, db: Any = None) -> None:
        self._store = FirestoreMerchantPolicyRepository()

    def get_latest_version_number(self, tenant_id: str) -> int:
        return self._store.get_latest_version_number(tenant_id)

    def get_active_policy(self, tenant_id: str) -> MerchantPolicyVersion | None:
        return self._store.get_active_policy(tenant_id)

    def get_policy_version(self, tenant_id: str, version: int) -> MerchantPolicyVersion | None:
        return self._store.get_policy_version(tenant_id, version)

    def list_policy_versions(self, tenant_id: str) -> list[MerchantPolicyVersion]:
        return self._store.list_policy_versions(tenant_id)

    def create_draft_version(
        self,
        tenant_id: str,
        policy_id: str,
        configuration_json: dict[str, Any],
        actor_id: str = "system",
        request_id: str = "req_unknown",
    ) -> MerchantPolicyVersion:
        return self._store.create_draft_version(
            tenant_id=tenant_id,
            policy_id=policy_id,
            configuration_json=configuration_json,
            actor_id=actor_id,
            request_id=request_id,
        )

    def activate_version(
        self,
        tenant_id: str,
        version: int,
        actor_id: str = "system",
        reason: str = "Policy activation",
        request_id: str = "req_unknown",
    ) -> MerchantPolicyVersion:
        return self._store.activate_version(
            tenant_id=tenant_id,
            version=version,
            actor_id=actor_id,
            reason=reason,
            request_id=request_id,
        )

    def rollback_to_version(
        self,
        tenant_id: str,
        target_version: int,
        actor_id: str = "system",
        reason: str = "Policy rollback",
        request_id: str = "req_unknown",
    ) -> MerchantPolicyVersion:
        return self._store.rollback_to_version(
            tenant_id=tenant_id,
            target_version=target_version,
            actor_id=actor_id,
            reason=reason,
            request_id=request_id,
        )

    def list_audit_logs(self, tenant_id: str) -> list[PolicyAuditLog]:
        return self._store.list_audit_logs(tenant_id)
