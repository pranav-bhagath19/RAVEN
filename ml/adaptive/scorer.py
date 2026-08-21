"""
RAVEN Adaptive Recovery Scorer Module

Combines base propensity model probability P(model) with global empirical action rates
and tenant-specific historical recovery rates into a deterministic, calibrated adaptive probability.
Enforces strict probability bounds [0.0, 1.0] and data sufficiency fallback modes.
"""

from pydantic import BaseModel, Field
from ml.adaptive.action_statistics import ActionTypeStatistics
from ml.adaptive.tenant_intelligence import TenantRecoveryProfile


class AdaptiveScoreResult(BaseModel):
    """Calibrated probability score result payload."""

    adaptive_probability: float = Field(..., ge=0.0, le=1.0)
    base_propensity_score: float = Field(..., ge=0.0, le=1.0)
    global_action_rate: float | None = Field(None, ge=0.0, le=1.0)
    tenant_action_rate: float | None = Field(None, ge=0.0, le=1.0)
    reasoning_mode: str = Field(..., description="ADAPTIVE_ML, GLOBAL_STATISTICAL_FALLBACK, PROPENSITY_FALLBACK, DETERMINISTIC_FALLBACK")
    intelligence_version: str = Field(default="v12.0", description="Adaptive intelligence version tag")
    fallback_reason: str | None = Field(None, description="Explanation if fallback mode was engaged")


class AdaptiveRecoveryScorer:
    """
    Deterministic adaptive scoring engine.
    Combines model_probability (weight 0.60), tenant_action_rate (weight 0.25), and global_action_rate (weight 0.15).
    """

    W_MODEL: float = 0.60
    W_TENANT: float = 0.25
    W_GLOBAL: float = 0.15

    GLOBAL_MIN_SAMPLES: int = 5
    TENANT_MIN_SAMPLES: int = 10

    def score(
        self,
        base_propensity: float,
        action_type: str,
        global_stats: dict[str, ActionTypeStatistics] | None = None,
        tenant_profile: TenantRecoveryProfile | None = None,
    ) -> AdaptiveScoreResult:
        """Computes calibrated adaptive probability score with deterministic fallback cascades."""
        # Sanitize base propensity
        p_model = max(0.0, min(1.0, float(base_propensity)))

        global_act_stat = global_stats.get(action_type) if global_stats else None
        has_global = global_act_stat is not None and global_act_stat.attempts >= self.GLOBAL_MIN_SAMPLES
        p_global = global_act_stat.empirical_success_rate if has_global and global_act_stat else None

        has_tenant = (
            tenant_profile is not None
            and tenant_profile.has_sufficient_data
            and action_type in tenant_profile.action_statistics
            and tenant_profile.action_statistics[action_type].attempts >= 3
        )
        p_tenant = (
            tenant_profile.action_statistics[action_type].empirical_success_rate
            if has_tenant and tenant_profile
            else None
        )

        if has_tenant and has_global and p_tenant is not None and p_global is not None:
            # Full Adaptive ML mode
            score = (self.W_MODEL * p_model) + (self.W_TENANT * p_tenant) + (self.W_GLOBAL * p_global)
            mode = "ADAPTIVE_ML"
            fb_reason = None
        elif has_global and p_global is not None:
            # Global Statistical Fallback mode
            score = (0.70 * p_model) + (0.30 * p_global)
            mode = "GLOBAL_STATISTICAL_FALLBACK"
            fb_reason = "Insufficient tenant-specific historical outcomes"
        else:
            # Propensity Fallback mode
            score = p_model
            mode = "PROPENSITY_FALLBACK"
            fb_reason = "Insufficient global action statistics"

        calibrated_score = round(max(0.0, min(1.0, score)), 4)

        return AdaptiveScoreResult(
            adaptive_probability=calibrated_score,
            base_propensity_score=round(p_model, 4),
            global_action_rate=p_global,
            tenant_action_rate=p_tenant,
            reasoning_mode=mode,
            intelligence_version="v12.0",
            fallback_reason=fb_reason,
        )
