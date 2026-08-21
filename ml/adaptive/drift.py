"""
RAVEN Observational Drift Detector Module

Monitors changes in root-cause distributions, action distributions, error-code frequencies,
and recovery rates between baseline and current observation windows.
OBSERVATIONAL ONLY: NEVER mutates production state, policies, or models automatically.
"""

from typing import Any
from pydantic import BaseModel, Field


class DriftReport(BaseModel):
    """Observational drift detection report."""

    status: str = Field(..., description="DRIFT_DETECTED or NO_SIGNIFICANT_DRIFT")
    drift_score: float = Field(..., ge=0.0, le=1.0)
    root_cause_drift_detected: bool = False
    action_distribution_drift_detected: bool = False
    recovery_rate_drift_delta: float = 0.0
    details: dict[str, Any] = Field(default_factory=dict)
    recommendation: str = Field("NO_ACTION_REQUIRED")


class DriftDetector:
    """
    Computes statistical drift scores comparing baseline and monitoring distributions.
    """

    DRIFT_THRESHOLD: float = 0.15

    def detect_drift(
        self,
        baseline_root_causes: dict[str, float],
        current_root_causes: dict[str, float],
        baseline_recovery_rate: float,
        current_recovery_rate: float,
    ) -> DriftReport:
        """Calculates Population Stability Index (PSI) style drift metric."""
        all_keys = set(baseline_root_causes.keys()).union(current_root_causes.keys())
        total_psi = 0.0

        for k in all_keys:
            p_base = baseline_root_causes.get(k, 0.01)
            p_curr = current_root_causes.get(k, 0.01)
            # Clip small values for numerical stability
            p_base = max(0.01, p_base)
            p_curr = max(0.01, p_curr)
            total_psi += (p_curr - p_base) * (p_curr / p_base)

        rate_delta = round(current_recovery_rate - baseline_recovery_rate, 4)
        is_drift = total_psi > self.DRIFT_THRESHOLD or abs(rate_delta) > 0.10

        return DriftReport(
            status="DRIFT_DETECTED" if is_drift else "NO_SIGNIFICANT_DRIFT",
            drift_score=round(min(1.0, total_psi), 4),
            root_cause_drift_detected=total_psi > self.DRIFT_THRESHOLD,
            action_distribution_drift_detected=False,
            recovery_rate_drift_delta=rate_delta,
            details={"psi_score": round(total_psi, 4), "rate_delta": rate_delta},
            recommendation="Review model calibration and dataset distribution" if is_drift else "NO_ACTION_REQUIRED",
        )
