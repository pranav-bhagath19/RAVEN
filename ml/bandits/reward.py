"""
RAVEN Bandit Reward Model

Maps verified historical recovery outcomes to numerical reward signals.
Preserves integer minor-unit monetary calculations (paise) and tags counterfactual estimates as COUNTERFACTUAL.
Zero financial state mutation authority.
"""

from pydantic import BaseModel, Field


class BanditRewardSignal(BaseModel):
    """Bandit Reward Signal payload."""

    action_type: str = Field(..., description="Action evaluated")
    outcome: int = Field(..., ge=0, le=1, description="0 = unsuccessful, 1 = successful recovery")
    gross_recovered_minor: int = Field(..., ge=0, description="Gross recovered amount in paise")
    action_cost_minor: int = Field(..., ge=0, description="Action execution cost in paise")
    net_reward_minor: int = Field(..., description="Net recovered value in paise (gross - cost)")
    normalized_reward: float = Field(..., description="Normalized reward signal in [-1.0, +1.0]")
    monetary_unit: str = Field(default="PAISE", description="Monetary unit representation")
    is_counterfactual: bool = Field(default=False, description="Flag indicating counterfactual simulation")
    label: str = Field(default="OBSERVED", description="OBSERVED or COUNTERFACTUAL")

    @property
    def reward_value(self) -> float:
        """Alias returning normalized_reward."""
        return self.normalized_reward


class BanditRewardModel:
    """
    Computes normalized reward signals for Contextual Bandit updates.
    """

    REWARD_SUCCESS = 1.0
    REWARD_FAILURE = 0.0
    REWARD_OPT_OUT = -0.5
    REWARD_BLOCKED = 0.0

    def compute_reward(
        self,
        outcome: int = 0,
        amount_minor: int = 0,
        action_cost_minor: int = 10,
        customer_opt_out: bool = False,
        is_counterfactual: bool = False,
        verified_recovery: bool | None = None,
        recovered_amount_minor: int = 0,
        reward_value: float | None = None,
        monetary_unit: str = "minor_units",
    ) -> BanditRewardSignal:
        """
        Computes deterministic reward signal from verified outcome data.
        """
        if verified_recovery is not None:
            outcome = 1 if verified_recovery else 0
            amount_minor = recovered_amount_minor or amount_minor

        label = "COUNTERFACTUAL" if is_counterfactual else "OBSERVED"

        if reward_value is not None:
            norm_reward = reward_value
            gross_rec = amount_minor
        elif customer_opt_out:
            norm_reward = self.REWARD_OPT_OUT
            gross_rec = 0
        elif outcome == 1:
            gross_rec = amount_minor
            norm_reward = self.REWARD_SUCCESS
        else:
            gross_rec = 0
            norm_reward = self.REWARD_FAILURE

        net_minor = gross_rec - action_cost_minor

        return BanditRewardSignal(
            action_type="SMART_RETRY",
            outcome=outcome,
            gross_recovered_minor=gross_rec,
            action_cost_minor=action_cost_minor,
            net_reward_minor=net_minor,
            normalized_reward=round(norm_reward, 4),
            is_counterfactual=is_counterfactual,
            label=label,
        )
