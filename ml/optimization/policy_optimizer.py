"""
RAVEN Offline Policy Optimizer Module

Simulates candidate policy configurations against historical outcomes in dry-run mode.
Calculates hypothetical recovery rates, net expected recovery value (paise), and veto rates
without executing real tools, issuing approval tokens, or mutating production policies.
"""

from typing import Any
from pydantic import BaseModel, Field
from ml.adaptive.dataset import AdaptiveOutcomeRecord
from policies.validation import validate_policy_configuration


class PolicyOptimizationReport(BaseModel):
    """Dry-run policy optimization report."""

    policy_id: str
    configuration_hash: str
    is_valid: bool
    decisions_evaluated: int = Field(..., ge=0)
    actions_blocked: int = Field(..., ge=0)
    actions_allowed: int = Field(..., ge=0)
    estimated_recovery_rate: float = Field(..., ge=0.0, le=1.0)
    estimated_recovery_value_minor: int = Field(..., ge=0, description="Paise integer minor units")
    policy_veto_rate: float = Field(..., ge=0.0, le=1.0)
    expected_value_minor: int = Field(..., ge=0)
    safety_violations: int = Field(0, ge=0, description="Must remain strictly 0")
    side_effects_occurred: bool = Field(False, description="Guaranteed False for offline simulation")


class OfflinePolicyOptimizer:
    """
    Dry-run policy optimizer evaluating policy overrides over historical outcome logs.
    """

    def optimize_policy(
        self,
        policy_id: str,
        candidate_config: dict[str, Any],
        historical_outcomes: list[AdaptiveOutcomeRecord],
    ) -> PolicyOptimizationReport:
        """Simulates candidate configuration against historical outcomes."""
        is_valid, errors = validate_policy_configuration(candidate_config)
        if not is_valid:
            return PolicyOptimizationReport(
                policy_id=policy_id,
                configuration_hash="",
                is_valid=False,
                decisions_evaluated=0,
                actions_blocked=0,
                actions_allowed=0,
                estimated_recovery_rate=0.0,
                estimated_recovery_value_minor=0,
                policy_veto_rate=0.0,
                expected_value_minor=0,
                safety_violations=len(errors),
                side_effects_occurred=False,
            )

        n = len(historical_outcomes)
        if n == 0:
            return PolicyOptimizationReport(
                policy_id=policy_id,
                configuration_hash="empty_dataset",
                is_valid=True,
                decisions_evaluated=0,
                actions_blocked=0,
                actions_allowed=0,
                estimated_recovery_rate=0.0,
                estimated_recovery_value_minor=0,
                policy_veto_rate=0.0,
                expected_value_minor=0,
                safety_violations=0,
                side_effects_occurred=False,
            )

        max_attempts = candidate_config.get("maximum_retry_attempts", 3)
        blocked = 0
        allowed = 0
        hypothetical_recovered_minor = 0

        for r in historical_outcomes:
            # POL_002 Check: attempts_count > max_attempts
            if r.attempts_count >= max_attempts:
                blocked += 1
            else:
                allowed += 1
                if r.outcome == 1:
                    hypothetical_recovered_minor += r.amount_minor

        veto_rate = blocked / n if n > 0 else 0.0
        rec_rate = (sum(1 for r in historical_outcomes if r.outcome == 1 and r.attempts_count < max_attempts) / n) if n > 0 else 0.0

        return PolicyOptimizationReport(
            policy_id=policy_id,
            configuration_hash="opt_cfg_hash_v12",
            is_valid=True,
            decisions_evaluated=n,
            actions_blocked=blocked,
            actions_allowed=allowed,
            estimated_recovery_rate=round(rec_rate, 4),
            estimated_recovery_value_minor=hypothetical_recovered_minor,
            policy_veto_rate=round(veto_rate, 4),
            expected_value_minor=hypothetical_recovered_minor,
            safety_violations=0,
            side_effects_occurred=False,
        )
