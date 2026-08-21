"""
RAVEN Counterfactual Evaluator Module

Evaluates "what if" hypothetical policy scenarios over historical decision logs.
Strictly labels outputs as OBSERVED, SIMULATED, or COUNTERFACTUAL to prevent misleading
financial claims.
"""

from typing import Any
from pydantic import BaseModel, Field
from ml.adaptive.dataset import AdaptiveOutcomeRecord


class CounterfactualEvaluationItem(BaseModel):
    """Single counterfactual decision comparison record."""

    decision_id: str
    tenant_id: str
    observed_action: str
    observed_outcome: int
    counterfactual_action: str
    counterfactual_decision: str = Field(..., description="APPROVED, BLOCKED, ESCALATED")
    label: str = Field("COUNTERFACTUAL", description="OBSERVED, SIMULATED, COUNTERFACTUAL")
    hypothetical_recovered_minor: int = Field(0, ge=0)


class CounterfactualReport(BaseModel):
    """Counterfactual evaluation summary report."""

    total_events_evaluated: int = Field(..., ge=0)
    observed_recovery_rate: float = Field(..., ge=0.0, le=1.0)
    counterfactual_recovery_rate: float = Field(..., ge=0.0, le=1.0)
    observed_gross_recovered_minor: int = Field(..., ge=0)
    counterfactual_hypothetical_recovered_minor: int = Field(..., ge=0)
    items: list[CounterfactualEvaluationItem] = Field(default_factory=list)


class CounterfactualEvaluator:
    """
    Evaluates counterfactual policy hypotheses over historical events.
    """

    def evaluate_counterfactual(
        self,
        candidate_config: dict[str, Any],
        historical_outcomes: list[AdaptiveOutcomeRecord],
    ) -> CounterfactualReport:
        """Evaluates hypothetical outcomes under candidate configuration."""
        n = len(historical_outcomes)
        if n == 0:
            return CounterfactualReport(
                total_events_evaluated=0,
                observed_recovery_rate=0.0,
                counterfactual_recovery_rate=0.0,
                observed_gross_recovered_minor=0,
                counterfactual_hypothetical_recovered_minor=0,
                items=[],
            )

        obs_succ = sum(1 for r in historical_outcomes if r.outcome == 1)
        obs_val = sum(r.amount_minor for r in historical_outcomes if r.outcome == 1)

        max_attempts = candidate_config.get("maximum_retry_attempts", 3)
        cf_succ = 0
        cf_val = 0
        items: list[CounterfactualEvaluationItem] = []

        for r in historical_outcomes:
            is_blocked = r.attempts_count >= max_attempts
            cf_dec = "BLOCKED" if is_blocked else "APPROVED"
            cf_recovered = r.amount_minor if (not is_blocked and r.outcome == 1) else 0

            if not is_blocked and r.outcome == 1:
                cf_succ += 1
                cf_val += r.amount_minor

            items.append(
                CounterfactualEvaluationItem(
                    decision_id=r.decision_id,
                    tenant_id=r.tenant_id,
                    observed_action=r.action_type,
                    observed_outcome=r.outcome,
                    counterfactual_action=r.action_type,
                    counterfactual_decision=cf_dec,
                    label="COUNTERFACTUAL",
                    hypothetical_recovered_minor=cf_recovered,
                )
            )

        return CounterfactualReport(
            total_events_evaluated=n,
            observed_recovery_rate=round(obs_succ / n, 4),
            counterfactual_recovery_rate=round(cf_succ / n, 4),
            observed_gross_recovered_minor=obs_val,
            counterfactual_hypothetical_recovered_minor=cf_val,
            items=items,
        )
