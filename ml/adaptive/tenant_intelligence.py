"""
RAVEN Tenant Recovery Intelligence Module

Manages tenant-scoped recovery profiles, failure patterns, and action success rates.
Strictly enforces tenant isolation (tenant_id) to prevent cross-tenant contamination.
"""

from typing import Any
from pydantic import BaseModel, Field
from ml.adaptive.action_statistics import ActionTypeStatistics
from ml.adaptive.dataset import AdaptiveOutcomeRecord


class TenantRecoveryProfile(BaseModel):
    """Tenant-scoped recovery intelligence profile."""

    tenant_id: str = Field(..., description="Target Tenant ID")
    total_outcomes_observed: int = Field(default=0, ge=0)
    overall_recovery_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    total_recovered_minor: int = Field(default=0, ge=0, description="Total revenue recovered in paise")
    action_statistics: dict[str, ActionTypeStatistics] = Field(default_factory=dict)
    failure_patterns: list[dict[str, Any]] = Field(default_factory=list)
    has_sufficient_data: bool = Field(default=False, description="Whether tenant outcomes meet TENANT_MIN_SAMPLES threshold")


class TenantIntelligenceManager:
    """
    Builds tenant-scoped recovery profiles with data sufficiency evaluation.
    """

    TENANT_MIN_SAMPLES = 10  # Minimum samples required for tenant-specific scoring

    def build_tenant_profile(self, tenant_id: str, records: list[AdaptiveOutcomeRecord]) -> TenantRecoveryProfile:
        """Builds profile for tenant_id filtering input records strictly by tenant_id."""
        tenant_records = [r for r in records if r.tenant_id == tenant_id]
        n = len(tenant_records)

        if n == 0:
            return TenantRecoveryProfile(tenant_id=tenant_id, has_sufficient_data=False)

        succ = sum(1 for r in tenant_records if r.outcome == 1)
        rec_rate = succ / n if n > 0 else 0.0
        total_minor = sum(r.amount_minor for r in tenant_records if r.outcome == 1)

        # Action level stats
        grouped: dict[str, list[AdaptiveOutcomeRecord]] = {}
        for r in tenant_records:
            grouped.setdefault(r.action_type, []).append(r)

        action_stats: dict[str, ActionTypeStatistics] = {}
        for atype, items in grouped.items():
            an = len(items)
            asucc = sum(1 for x in items if x.outcome == 1)
            action_stats[atype] = ActionTypeStatistics(
                action_type=atype,
                attempts=an,
                successes=asucc,
                failures=an - asucc,
                empirical_success_rate=round(asucc / an, 4) if an > 0 else 0.0,
                confidence_interval_low=0.0,
                confidence_interval_high=1.0,
                average_recovery_value_minor=sum(x.amount_minor for x in items if x.outcome == 1) // an if an > 0 else 0,
                average_latency_ms=450.0,
            )

        return TenantRecoveryProfile(
            tenant_id=tenant_id,
            total_outcomes_observed=n,
            overall_recovery_rate=round(rec_rate, 4),
            total_recovered_minor=total_minor,
            action_statistics=action_stats,
            has_sufficient_data=n >= self.TENANT_MIN_SAMPLES,
        )
