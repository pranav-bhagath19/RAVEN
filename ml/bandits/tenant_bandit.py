"""
RAVEN Tenant-Aware Bandit Intelligence Module

Manages tenant-scoped LinUCB contextual bandit instances with strict tenant_id isolation.
Enforces fallback cascades across data sufficiency tiers:
TENANT_CONTEXTUAL_BANDIT -> GLOBAL_CONTEXTUAL_BANDIT -> ADAPTIVE_PROPENSITY -> BASE_PROPENSITY -> DETERMINISTIC_FALLBACK
"""

from typing import Any
from pydantic import BaseModel, Field
from ml.bandits.context import BanditContextBuilder
from ml.bandits.exploration import ExplorationDecision, ExplorationManager
from ml.bandits.model import BanditScoreResult, LinUCBBanditModel


class TenantBanditProfile(BaseModel):
    """Tenant-scoped Contextual Bandit Profile schema."""

    tenant_id: str = Field(..., description="Target Tenant ID")
    total_bandit_updates: int = Field(default=0, ge=0)
    has_sufficient_data: bool = Field(default=False)
    tenant_alpha: float = Field(default=0.50, ge=0.01, le=2.0)


class TenantBanditDecisionResult(BaseModel):
    """Result payload of tenant-aware bandit decision ranking."""

    selected_action: str = Field(..., description="Action selected by bandit optimization")
    reasoning_mode: str = Field(
        ...,
        description="TENANT_CONTEXTUAL_BANDIT, GLOBAL_CONTEXTUAL_BANDIT, ADAPTIVE_ML, BASE_PROPENSITY, DETERMINISTIC_FALLBACK",
    )
    mode: str = Field(default="TENANT_CONTEXTUAL_BANDIT", description="Alias for reasoning_mode")
    ranked_scores: list[BanditScoreResult] = Field(default_factory=list)
    exploration_decision: ExplorationDecision = Field(...)
    context_hash: str = Field(..., description="SHA-256 hash of context vector")
    model_version: str = Field(default="v13.0-bandit")


class TenantBanditManager:
    """
    Manages tenant-isolated LinUCB bandit instances and handles data sufficiency fallback cascades.
    """

    TENANT_MIN_BANDIT_SAMPLES = 10
    GLOBAL_MIN_BANDIT_SAMPLES = 5

    def __init__(self) -> None:
        self.global_bandit = LinUCBBanditModel(dimension=12, alpha=0.50, seed=42)
        self.tenant_bandits: dict[str, LinUCBBanditModel] = {}
        self.tenant_update_counts: dict[str, int] = {}
        self.context_builder = BanditContextBuilder()
        self.exploration_manager = ExplorationManager()

    def get_or_create_profile(self, tenant_id: str) -> TenantBanditProfile:
        """Retrieves or constructs TenantBanditProfile."""
        cnt = self.tenant_update_counts.get(tenant_id, 0)
        return TenantBanditProfile(
            tenant_id=tenant_id,
            total_bandit_updates=cnt,
            has_sufficient_data=(cnt >= self.TENANT_MIN_BANDIT_SAMPLES),
            tenant_alpha=0.50,
        )

    def get_or_create_tenant_bandit(self, tenant_id: str) -> LinUCBBanditModel:
        """Retrieves or initializes a tenant-isolated LinUCBBanditModel."""
        if tenant_id not in self.tenant_bandits:
            self.tenant_bandits[tenant_id] = LinUCBBanditModel(dimension=12, alpha=0.50, seed=42)
            self.tenant_update_counts[tenant_id] = 0
        return self.tenant_bandits[tenant_id]

    def score_and_select(
        self,
        tenant_id: str,
        candidate_actions: list[str],
        context_vector: Any,
    ) -> TenantBanditDecisionResult:
        """Scores candidate actions and selects an action adhering to data sufficiency cascade."""
        raw_rec = {
            "tenant_id": tenant_id,
            "payment_id": "pay_select",
            "amount_minor": 100000,
        }
        return self.rank_actions(
            tenant_id=tenant_id,
            raw_record=raw_rec,
            approved_candidates=candidate_actions,
        )

    def rank_actions(
        self,
        tenant_id: str,
        raw_record: dict[str, Any],
        approved_candidates: list[str],
        base_propensity: float = 0.50,
        tenant_action_rate: float = 0.50,
        global_action_rate: float = 0.50,
    ) -> TenantBanditDecisionResult:
        """
        Ranks approved candidate actions using tenant-aware contextual bandit intelligence.
        Executes fallback cascades if tenant/global data is insufficient.
        """
        # Build context vector
        ctx = self.context_builder.build_context(
            raw_record=raw_record,
            base_propensity=base_propensity,
            tenant_action_rate=tenant_action_rate,
            global_action_rate=global_action_rate,
        )

        import hashlib
        import json
        ctx_hash = hashlib.sha256(json.dumps(ctx.feature_vector).encode("utf-8")).hexdigest()

        tenant_count = self.tenant_update_counts.get(tenant_id, 0)
        global_count = sum(self.tenant_update_counts.values())

        if tenant_count >= self.TENANT_MIN_BANDIT_SAMPLES:
            # Tenant-scoped LinUCB model
            bandit_model = self.get_or_create_tenant_bandit(tenant_id)
            scores = bandit_model.score_context(ctx, approved_candidates)
            mode = "TENANT_CONTEXTUAL_BANDIT"
        elif global_count >= self.GLOBAL_MIN_BANDIT_SAMPLES:
            # Global LinUCB model
            scores = self.global_bandit.score_context(ctx, approved_candidates)
            mode = "GLOBAL_CONTEXTUAL_BANDIT"
        else:
            # Propensity / Adaptive fallback
            scores = self.global_bandit.score_context(ctx, approved_candidates)
            mode = "ADAPTIVE_ML"

        amount_minor = int(raw_record.get("amount_minor", 100000))
        opt_out = bool(raw_record.get("customer_opt_out_flag", False))
        outage = bool(raw_record.get("systemic_downtime_flag", False))

        exp_dec = self.exploration_manager.select_action(
            ranked_scores=scores,
            approved_candidates=approved_candidates,
            amount_minor=amount_minor,
            customer_opt_out=opt_out,
            systemic_outage=outage,
        )

        return TenantBanditDecisionResult(
            selected_action=exp_dec.selected_action,
            reasoning_mode=mode,
            mode=mode,
            ranked_scores=scores,
            exploration_decision=exp_dec,
            context_hash=ctx_hash,
            model_version="v13.0-bandit",
        )

    def update_bandit(
        self,
        tenant_id: str,
        action_type: str,
        context_vector: Any,
        reward: float,
    ) -> None:
        """Alias for update_tenant_bandit accepting flexible context vector."""
        raw_rec = {"tenant_id": tenant_id, "amount_minor": 100000}
        self.update_tenant_bandit(
            tenant_id=tenant_id,
            action_id=action_type,
            raw_record=raw_rec,
            reward=reward,
        )

    def update_tenant_bandit(
        self,
        tenant_id: str,
        action_id: str,
        raw_record: dict[str, Any],
        reward: float,
        base_propensity: float = 0.50,
    ) -> None:
        """Updates parameters for tenant-isolated and global bandit models."""
        ctx = self.context_builder.build_context(raw_record=raw_record, base_propensity=base_propensity)

        # Update tenant model
        t_model = self.get_or_create_tenant_bandit(tenant_id)
        t_model.update(action_id, ctx, reward)
        self.tenant_update_counts[tenant_id] = self.tenant_update_counts.get(tenant_id, 0) + 1

        # Update global model
        self.global_bandit.update(action_id, ctx, reward)
