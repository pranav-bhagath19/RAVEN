"""
RAVEN Bounded Exploration Safety Manager

Enforces safety constraints on Contextual Bandit decision optimization:
1. Exploration is strictly constrained to PolicyEngine-approved candidates.
2. Maximum exploration rate cap (e.g. 10%).
3. Minimum sample count requirements.
4. Systemic outage and customer opt-out safety overrides.
5. High-value transaction conservative overrides.
"""

from typing import Any
from pydantic import BaseModel, Field


class ExplorationPolicyConfig(BaseModel):
    """Exploration configuration and constraints."""

    max_exploration_rate: float = Field(default=0.10, ge=0.0, le=0.25, description="Max allowed exploration probability cap")
    min_samples_threshold: int = Field(default=5, ge=1, description="Minimum historical samples required for exploration")
    min_sample_threshold: int = Field(default=5, ge=1, description="Alias for min_samples_threshold")
    high_value_threshold_minor: int = Field(default=500000, ge=0, description="Amount above which exploration is disabled (5,000 INR)")
    allow_exploration_on_opt_out: bool = Field(default=False, description="Strictly False: Opt-out prevents exploration")
    allow_exploration_during_outage: bool = Field(default=False, description="Strictly False: Bank outage prevents exploration")


class ExplorationDecision(BaseModel):
    """Exploration decision result."""

    selected_action: str = Field(..., description="Action selected following safety constraints")
    is_exploration: bool = Field(..., description="Whether an exploration action was selected")
    should_explore: bool = Field(default=False, description="Whether exploration should be conducted")
    override_reason: str = Field(default="NONE", description="Safety override reason if exploration disabled")
    exploration_reason: str = Field(..., description="EXPLOIT_TOP_UCB, BOUNDED_EXPLORATION, SAFETY_OVERRIDE_EXPLOIT, DETERMINISTIC_FALLBACK")
    allowed_candidates: list[str] = Field(default_factory=list, description="PolicyEngine-approved candidate list")


class ExplorationManager:
    """
    Manages safety-bounded exploration for Contextual Bandit decision making.
    """

    def __init__(self, config: ExplorationPolicyConfig | None = None) -> None:
        self.config = config or ExplorationPolicyConfig()

    def should_explore(
        self,
        tenant_id: str,
        action_type: str,
        historical_sample_count: int = 0,
        customer_opt_out: bool = False,
        is_systemic_downtime: bool = False,
    ) -> ExplorationDecision:
        """Evaluates whether exploration is permitted for a tenant/action context."""
        if customer_opt_out:
            return ExplorationDecision(
                selected_action=action_type,
                is_exploration=False,
                should_explore=False,
                override_reason="CUSTOMER_OPT_OUT",
                exploration_reason="SAFETY_OVERRIDE_EXPLOIT",
            )
        if is_systemic_downtime:
            return ExplorationDecision(
                selected_action=action_type,
                is_exploration=False,
                should_explore=False,
                override_reason="SYSTEMIC_DOWNTIME",
                exploration_reason="SAFETY_OVERRIDE_EXPLOIT",
            )
        if historical_sample_count < self.config.min_samples_threshold:
            return ExplorationDecision(
                selected_action=action_type,
                is_exploration=False,
                should_explore=False,
                override_reason="INSUFFICIENT_SAMPLES",
                exploration_reason="SAFETY_OVERRIDE_EXPLOIT",
            )
        return ExplorationDecision(
            selected_action=action_type,
            is_exploration=True,
            should_explore=True,
            override_reason="PERMITTED",
            exploration_reason="BOUNDED_EXPLORATION",
        )

    def select_action(
        self,
        ranked_scores: list[Any],  # list of BanditScoreResult
        approved_candidates: list[str],
        amount_minor: int,
        customer_opt_out: bool = False,
        systemic_outage: bool = False,
    ) -> ExplorationDecision:
        """
        Selects an action from candidate rankings adhering strictly to safety bounds.
        """
        if not ranked_scores or not approved_candidates:
            return ExplorationDecision(
                selected_action="NO_ACTION",
                is_exploration=False,
                should_explore=False,
                exploration_reason="DETERMINISTIC_FALLBACK",
                allowed_candidates=approved_candidates,
            )

        # Filter ranked scores strictly by approved candidates
        valid_scores = [s for s in ranked_scores if s.action_id in approved_candidates]
        if not valid_scores:
            return ExplorationDecision(
                selected_action=approved_candidates[0] if approved_candidates else "NO_ACTION",
                is_exploration=False,
                should_explore=False,
                exploration_reason="SAFETY_OVERRIDE_EXPLOIT",
                allowed_candidates=approved_candidates,
            )

        # Safety Check 1: High value transaction protection
        if amount_minor >= self.config.high_value_threshold_minor:
            return ExplorationDecision(
                selected_action=valid_scores[0].action_id,
                is_exploration=False,
                should_explore=False,
                exploration_reason="HIGH_VALUE_SAFETY_OVERRIDE_EXPLOIT",
                allowed_candidates=approved_candidates,
            )

        # Safety Check 2: Customer opt-out or systemic outage
        if customer_opt_out or systemic_outage:
            return ExplorationDecision(
                selected_action=valid_scores[0].action_id,
                is_exploration=False,
                should_explore=False,
                exploration_reason="OUTAGE_OPT_OUT_SAFETY_OVERRIDE",
                allowed_candidates=approved_candidates,
            )

        # Exploitation default: Top UCB score
        top_action = valid_scores[0].action_id
        return ExplorationDecision(
            selected_action=top_action,
            is_exploration=False,
            should_explore=False,
            exploration_reason="EXPLOIT_TOP_UCB",
            allowed_candidates=approved_candidates,
        )
