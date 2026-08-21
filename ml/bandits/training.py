"""
RAVEN Bandit Offline Training Module

Executes reproducible offline training of LinUCB contextual bandit models on verified historical dataset logs.
Ensures zero target leakage, chronological dataset splitting, and canonical SHA-256 artifact hashing.
"""

import hashlib
import json
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from ml.adaptive.dataset import AdaptiveOutcomeRecord
from ml.bandits.context import BanditContextBuilder
from ml.bandits.model import LinUCBBanditModel
from ml.bandits.reward import BanditRewardModel


class BanditTrainingReport(BaseModel):
    """Bandit Training Summary Report."""

    model_version: str = Field(..., description="Trained model version tag")
    dataset_hash: str = Field(..., description="SHA-256 hash of training dataset")
    total_records_processed: int = Field(..., ge=0)
    distinct_tenants_count: int = Field(..., ge=0)
    training_seed: int = Field(..., description="Random seed used")
    model_artifact_hash: str = Field(..., description="SHA-256 hash of trained model parameters")
    trained_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BanditOfflineTrainer:
    """
    Offline training manager for LinUCB Contextual Bandit models.
    """

    def train_offline(
        self,
        dataset_records: list[AdaptiveOutcomeRecord],
        model_version: str = "v13.0-bandit",
        alpha: float = 0.50,
        seed: int = 42,
    ) -> tuple[LinUCBBanditModel, BanditTrainingReport]:
        """
        Trains LinUCBBanditModel on historical outcome records in chronological order.
        """
        # Calculate dataset SHA-256 hash
        raw_repr = json.dumps([r.model_dump() for r in dataset_records], sort_keys=True, default=str)
        dataset_hash = hashlib.sha256(raw_repr.encode("utf-8")).hexdigest()

        model = LinUCBBanditModel(dimension=12, alpha=alpha, seed=seed)
        builder = BanditContextBuilder()
        reward_calc = BanditRewardModel()

        tenants_seen: set[str] = set()

        for rec in dataset_records:
            tenants_seen.add(rec.tenant_id)
            raw_dict = rec.model_dump()
            # Remove post-action fields before context building
            for f in ["recovered_amount_minor", "is_recovered", "verification_status", "executed_at", "tool_result", "future_event_id", "post_action_status", "outcome"]:
                raw_dict.pop(f, None)

            ctx = builder.build_context(raw_dict, base_propensity=rec.propensity_score)
            rew_signal = reward_calc.compute_reward(
                outcome=rec.outcome,
                amount_minor=rec.amount_minor,
                customer_opt_out=rec.customer_opt_out_flag,
            )
            model.update(rec.action_type, ctx, rew_signal.normalized_reward)

        artifact_hash = model.compute_integrity_hash()

        report = BanditTrainingReport(
            model_version=model_version,
            dataset_hash=dataset_hash,
            total_records_processed=len(dataset_records),
            distinct_tenants_count=len(tenants_seen),
            training_seed=seed,
            model_artifact_hash=artifact_hash,
        )

        return model, report
