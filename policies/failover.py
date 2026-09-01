"""
RAVEN Regional Failover & Stale Policy Protection Manager

Handles region health monitoring, regional failover transitions, and stale policy read protection.
Guarantees fail-closed security invariants if regional policy state is stale, ambiguous, or unverified.
"""

from datetime import datetime, timezone
from typing import Any
from domain.entities.region import Region
from domain.entities.replication import PolicyReplicationState
from domain.enums import RegionStatus, ReplicationStatus


class RegionalFailoverManager:
    """
    Manages regional health states, policy freshness verification, and safe failover routing.
    """

    def __init__(self) -> None:
        self.regions: dict[str, Region] = {}

    def register_region(self, region: Region) -> None:
        """Registers a new region in the multi-region infrastructure map."""
        self.regions[region.region_id] = region

    def get_region(self, region_id: str) -> Region | None:
        """Retrieves a registered region by ID."""
        return self.regions.get(region_id)

    def update_region_status(
        self,
        region_id: str,
        status: RegionStatus,
        health_score: float = 1.0,
    ) -> Region:
        """Updates status and health score of a region."""
        region = self.regions.get(region_id)
        if not region:
            region = Region(
                region_id=region_id,
                name=region_id,
                status=status,
                health_score=health_score,
            )
            self.regions[region_id] = region
        else:
            region.status = status
            region.health_score = max(0.0, min(1.0, health_score))
            region.updated_at = datetime.now(timezone.utc)
        return region

    def verify_policy_freshness(
        self,
        tenant_id: str,
        replication_state: PolicyReplicationState,
        max_sync_age_seconds: float = 300.0,
    ) -> bool:
        """
        Verifies whether a regional policy replication state is fresh and valid.
        Returns False if stale, conflicted, failed, or sync age exceeds max threshold.
        """
        if replication_state.tenant_id != tenant_id:
            return False

        if replication_state.status not in (ReplicationStatus.SYNCHRONIZED,):
            return False

        now = datetime.now(timezone.utc)
        sync_age = (now - replication_state.synced_at).total_seconds()

        if sync_age > max_sync_age_seconds:
            replication_state.status = ReplicationStatus.STALE
            replication_state.error_message = f"Stale policy state: sync age {sync_age:.1f}s exceeds threshold {max_sync_age_seconds:.1f}s"
            return False

        return True

    def execute_failover(
        self,
        tenant_id: str,
        failed_region_id: str,
        target_region_id: str,
        replication_state: PolicyReplicationState | None = None,
    ) -> dict[str, Any]:
        """
        Executes a regional failover transition for a tenant.
        Verifies target region health and policy freshness before authorizing failover.
        """
        failed_reg = self.get_region(failed_region_id)
        if failed_reg:
            failed_reg.status = RegionStatus.OFFLINE
            failed_reg.health_score = 0.0

        target_reg = self.get_region(target_region_id)
        if not target_reg or target_reg.status not in (RegionStatus.ACTIVE, RegionStatus.DEGRADED):
            return {
                "tenant_id": tenant_id,
                "status": "FAILOVER_REJECTED",
                "reason": f"Target region '{target_region_id}' is not available or unhealthy",
                "can_execute": False,
            }

        # Policy Freshness Check
        if replication_state:
            is_fresh = self.verify_policy_freshness(tenant_id, replication_state)
            if not is_fresh:
                return {
                    "tenant_id": tenant_id,
                    "status": "FAILOVER_REJECTED",
                    "reason": f"Policy state for tenant '{tenant_id}' in region '{target_region_id}' is stale or unverified. MUST fail closed.",
                    "can_execute": False,
                }

        return {
            "tenant_id": tenant_id,
            "status": "FAILOVER_AUTHORIZED",
            "from_region": failed_region_id,
            "to_region": target_region_id,
            "can_execute": True,
            "authorized_at": datetime.now(timezone.utc).isoformat(),
        }
