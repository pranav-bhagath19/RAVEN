"""
RAVEN Merchant Policy Repository Module

Provides persistent CRUD operations, immutable versioning, transactional activation,
atomic rollback, and audit log tracking for multi-tenant merchant policy configurations.
"""

from datetime import datetime, timezone
from typing import Any, cast
from sqlalchemy.orm import Session
from domain.entities.merchant_policy import (
    MerchantPolicyVersion,
    PolicyAuditAction,
    PolicyAuditLog,
    PolicyVersionStatus,
)
from persistence.models import MerchantPolicyRecord, PolicyAuditLogRecord
from policies.validation import compute_policy_config_hash


class MerchantPolicyRepository:
    """
    Repository managing tenant merchant policy versions and audit logs.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_latest_version_number(self, tenant_id: str) -> int:
        """Returns the highest version number for a tenant, defaulting to 0 if none exists."""
        rec = (
            self.db.query(MerchantPolicyRecord)
            .filter(MerchantPolicyRecord.tenant_id == tenant_id)
            .order_by(MerchantPolicyRecord.version.desc())
            .first()
        )
        return int(rec.version) if rec else 0

    def get_active_policy(self, tenant_id: str) -> MerchantPolicyVersion | None:
        """Retrieves the currently ACTIVE policy version for a tenant."""
        rec = (
            self.db.query(MerchantPolicyRecord)
            .filter(
                MerchantPolicyRecord.tenant_id == tenant_id,
                MerchantPolicyRecord.status == PolicyVersionStatus.ACTIVE.value,
            )
            .first()
        )
        if not rec:
            return None

        return MerchantPolicyVersion(
            policy_id=str(rec.policy_id),
            tenant_id=str(rec.tenant_id),
            version=int(rec.version),
            status=PolicyVersionStatus(str(rec.status)),
            configuration_json=cast(dict[str, Any], rec.configuration_json),
            configuration_hash=str(rec.configuration_hash),
            created_by=str(rec.created_by),
            created_at=cast(datetime, rec.created_at),
            activated_at=cast(datetime | None, rec.activated_at),
            deactivated_at=cast(datetime | None, rec.deactivated_at),
            parent_version=cast(int | None, rec.parent_version),
            rollback_source_version=cast(int | None, rec.rollback_source_version),
        )

    def get_policy_version(self, tenant_id: str, version: int) -> MerchantPolicyVersion | None:
        """Retrieves a specific policy version for a tenant."""
        rec = (
            self.db.query(MerchantPolicyRecord)
            .filter(
                MerchantPolicyRecord.tenant_id == tenant_id,
                MerchantPolicyRecord.version == version,
            )
            .first()
        )
        if not rec:
            return None

        return MerchantPolicyVersion(
            policy_id=str(rec.policy_id),
            tenant_id=str(rec.tenant_id),
            version=int(rec.version),
            status=PolicyVersionStatus(str(rec.status)),
            configuration_json=cast(dict[str, Any], rec.configuration_json),
            configuration_hash=str(rec.configuration_hash),
            created_by=str(rec.created_by),
            created_at=cast(datetime, rec.created_at),
            activated_at=cast(datetime | None, rec.activated_at),
            deactivated_at=cast(datetime | None, rec.deactivated_at),
            parent_version=cast(int | None, rec.parent_version),
            rollback_source_version=cast(int | None, rec.rollback_source_version),
        )

    def list_policy_versions(self, tenant_id: str) -> list[MerchantPolicyVersion]:
        """Lists all policy versions for a tenant sorted by version descending."""
        records = (
            self.db.query(MerchantPolicyRecord)
            .filter(MerchantPolicyRecord.tenant_id == tenant_id)
            .order_by(MerchantPolicyRecord.version.desc())
            .all()
        )
        return [
            MerchantPolicyVersion(
                policy_id=str(r.policy_id),
                tenant_id=str(r.tenant_id),
                version=int(r.version),
                status=PolicyVersionStatus(str(r.status)),
                configuration_json=cast(dict[str, Any], r.configuration_json),
                configuration_hash=str(r.configuration_hash),
                created_by=str(r.created_by),
                created_at=cast(datetime, r.created_at),
                activated_at=cast(datetime | None, r.activated_at),
                deactivated_at=cast(datetime | None, r.deactivated_at),
                parent_version=cast(int | None, r.parent_version),
                rollback_source_version=cast(int | None, r.rollback_source_version),
            )
            for r in records
        ]

    def create_draft_version(
        self,
        tenant_id: str,
        policy_id: str,
        configuration_json: dict[str, Any],
        actor_id: str = "system",
        request_id: str = "req_unknown",
    ) -> MerchantPolicyVersion:
        """Creates a new DRAFT policy version for a tenant."""
        latest = self.get_latest_version_number(tenant_id)
        new_version_num = latest + 1
        cfg_hash = compute_policy_config_hash(configuration_json)
        now = datetime.now(timezone.utc)

        rec = MerchantPolicyRecord(
            policy_id=policy_id,
            tenant_id=tenant_id,
            version=new_version_num,
            status=PolicyVersionStatus.DRAFT.value,
            configuration_json=configuration_json,
            configuration_hash=cfg_hash,
            created_by=actor_id,
            created_at=now,
            parent_version=latest if latest > 0 else None,
        )
        self.db.add(rec)

        # Audit Entry
        audit = PolicyAuditLogRecord(
            audit_id=f"aud_{new_version_num}_{now.timestamp()}",
            tenant_id=tenant_id,
            policy_id=policy_id,
            policy_version=new_version_num,
            action=PolicyAuditAction.CREATED.value,
            actor_id=actor_id,
            previous_version=latest if latest > 0 else None,
            new_version=new_version_num,
            configuration_hash=cfg_hash,
            timestamp=now,
            reason=f"Created draft policy version {new_version_num}",
            request_id=request_id,
        )
        self.db.add(audit)
        self.db.commit()

        return self.get_policy_version(tenant_id, new_version_num)  # type: ignore[return-value]

    def activate_version(
        self,
        tenant_id: str,
        version: int,
        actor_id: str = "system",
        reason: str = "Policy activation",
        request_id: str = "req_unknown",
    ) -> MerchantPolicyVersion:
        """
        Transactionally activates a policy version, setting any existing ACTIVE version to SUPERSEDED.
        Race-safe: uses atomic database transaction.
        """
        now = datetime.now(timezone.utc)

        target_rec = (
            self.db.query(MerchantPolicyRecord)
            .filter(
                MerchantPolicyRecord.tenant_id == tenant_id,
                MerchantPolicyRecord.version == version,
            )
            .with_for_update()
            .first()
        )
        if not target_rec:
            raise ValueError(f"Policy version {version} not found for tenant '{tenant_id}'")

        if str(target_rec.status) == PolicyVersionStatus.ACTIVE.value:
            return self.get_policy_version(tenant_id, version)  # type: ignore[return-value]

        # Get previous active version number if any
        prev_rec = (
            self.db.query(MerchantPolicyRecord)
            .filter(
                MerchantPolicyRecord.tenant_id == tenant_id,
                MerchantPolicyRecord.status == PolicyVersionStatus.ACTIVE.value,
                MerchantPolicyRecord.version != version,
            )
            .first()
        )
        prev_version_num: int | None = int(prev_rec.version) if prev_rec else None

        target_rec.status = PolicyVersionStatus.ACTIVE.value  # type: ignore[assignment]
        target_rec.activated_at = now  # type: ignore[assignment]

        # Atomically supersede ALL other active versions for this tenant
        self.db.query(MerchantPolicyRecord).filter(
            MerchantPolicyRecord.tenant_id == tenant_id,
            MerchantPolicyRecord.status == PolicyVersionStatus.ACTIVE.value,
            MerchantPolicyRecord.version != version,
        ).update(
            {"status": PolicyVersionStatus.SUPERSEDED.value, "deactivated_at": now},
            synchronize_session=False,
        )

        # Audit Entry
        audit = PolicyAuditLogRecord(
            audit_id=f"aud_act_{version}_{now.timestamp()}",
            tenant_id=tenant_id,
            policy_id=str(target_rec.policy_id),
            policy_version=version,
            action=PolicyAuditAction.ACTIVATED.value,
            actor_id=actor_id,
            previous_version=prev_version_num,
            new_version=version,
            configuration_hash=str(target_rec.configuration_hash),
            timestamp=now,
            reason=reason,
            request_id=request_id,
        )
        self.db.add(audit)
        self.db.commit()

        return self.get_policy_version(tenant_id, version)  # type: ignore[return-value]

    def rollback_to_version(
        self,
        tenant_id: str,
        target_version: int,
        actor_id: str = "system",
        reason: str = "Policy rollback",
        request_id: str = "req_unknown",
    ) -> MerchantPolicyVersion:
        """
        Performs lineage-preserving rollback to a target historical version.
        NEVER MUTATES HISTORICAL RECORDS.
        Creates a NEW version referencing target_version configuration and sets it ACTIVE.
        """
        historical_target = self.get_policy_version(tenant_id, target_version)
        if not historical_target:
            raise ValueError(f"Rollback failed: Historical version {target_version} does not exist for tenant '{tenant_id}'")

        latest = self.get_latest_version_number(tenant_id)
        new_version_num = latest + 1
        now = datetime.now(timezone.utc)
        cfg_hash = historical_target.configuration_hash

        # Create new version with copied configuration
        rec = MerchantPolicyRecord(
            policy_id=historical_target.policy_id,
            tenant_id=tenant_id,
            version=new_version_num,
            status=PolicyVersionStatus.ACTIVE.value,
            configuration_json=historical_target.configuration_json,
            configuration_hash=cfg_hash,
            created_by=actor_id,
            created_at=now,
            activated_at=now,
            parent_version=latest,
            rollback_source_version=target_version,
        )
        self.db.add(rec)

        # Supersede current ACTIVE version
        active_recs = (
            self.db.query(MerchantPolicyRecord)
            .filter(
                MerchantPolicyRecord.tenant_id == tenant_id,
                MerchantPolicyRecord.status == PolicyVersionStatus.ACTIVE.value,
                MerchantPolicyRecord.version != new_version_num,
            )
            .all()
        )
        prev_version_num: int | None = int(active_recs[0].version) if active_recs else None
        for a_rec in active_recs:
            a_rec.status = PolicyVersionStatus.SUPERSEDED.value  # type: ignore[assignment]
            a_rec.deactivated_at = now  # type: ignore[assignment]

        # Audit Entry
        audit = PolicyAuditLogRecord(
            audit_id=f"aud_rb_{new_version_num}_{now.timestamp()}",
            tenant_id=tenant_id,
            policy_id=historical_target.policy_id,
            policy_version=new_version_num,
            action=PolicyAuditAction.ROLLED_BACK.value,
            actor_id=actor_id,
            previous_version=prev_version_num,
            new_version=new_version_num,
            configuration_hash=cfg_hash,
            timestamp=now,
            reason=f"{reason} (rolled back to version {target_version})",
            request_id=request_id,
        )
        self.db.add(audit)
        self.db.commit()

        return self.get_policy_version(tenant_id, new_version_num)  # type: ignore[return-value]

    def list_audit_logs(self, tenant_id: str) -> list[PolicyAuditLog]:
        """Lists all policy audit logs for a tenant sorted by timestamp descending."""
        records = (
            self.db.query(PolicyAuditLogRecord)
            .filter(PolicyAuditLogRecord.tenant_id == tenant_id)
            .order_by(PolicyAuditLogRecord.timestamp.desc())
            .all()
        )
        return [
            PolicyAuditLog(
                audit_id=str(r.audit_id),
                tenant_id=str(r.tenant_id),
                policy_id=str(r.policy_id),
                policy_version=int(r.policy_version),
                action=PolicyAuditAction(str(r.action)),
                actor_id=str(r.actor_id),
                previous_version=cast(int | None, r.previous_version),
                new_version=cast(int | None, r.new_version),
                configuration_hash=str(r.configuration_hash),
                timestamp=cast(datetime, r.timestamp),
                reason=str(r.reason),
                request_id=str(r.request_id),
            )
            for r in records
        ]
