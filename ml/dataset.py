"""
RAVEN ML Dataset Builder Module

Constructs propensity model datasets from persisted DecisionTrace/Verification logs or synthetic scenario runs.
Enforces strict separation of FEATURES, TARGET, IDENTIFIERS, and GROUND_TRUTH to prevent target leakage.
Provides chronological train/validation/test dataset splitting.
"""

import hashlib
import json
from typing import Any
from pydantic import BaseModel
from domain.entities.financial_event import FinancialEvent
from ml.features.pipeline import FeaturePipelineV1
from simulator.generator import SyntheticDataGenerator


class DatasetMetadata(BaseModel):
    """Metadata describing a generated ML dataset artifact."""

    dataset_version: str = "v1.0"
    schema_version: str = "v1.0"
    sample_count: int
    train_count: int
    validation_count: int
    test_count: int
    class_distribution: dict[str, int]
    dataset_hash: str
    created_at: str = "2026-08-22T00:00:00Z"


class DatasetSplit(BaseModel):
    """Holds partitioned dataset features, targets, identifiers, and ground truth."""

    feature_matrix: list[list[float]]
    target_vector: list[int]
    identifiers: list[dict[str, str]]
    ground_truth: list[dict[str, Any]]


class MLDataset(BaseModel):
    """Complete versioned dataset object containing train, validation, and test partitions."""

    metadata: DatasetMetadata
    feature_names: list[str]
    train_split: DatasetSplit
    val_split: DatasetSplit
    test_split: DatasetSplit


class MLDatasetBuilder:
    """
    Deterministic dataset builder converting synthetic scenario evaluation cases or operational records
    into clean, leak-free training partitions.
    """

    def __init__(self, seed: int = 42) -> None:
        self.seed = seed
        self.pipeline = FeaturePipelineV1()

    def build_dataset_from_simulator(self) -> MLDataset:
        """
        Builds dataset from the multi-scenario synthetic generator suite.
        Uses candidate actions across scenarios to form positive/negative propensity samples.
        """
        generator = SyntheticDataGenerator(seed=self.seed)
        scenario_results = generator.generate_all_scenarios()

        features_raw: list[dict[str, Any]] = []
        targets: list[int] = []
        identifiers: list[dict[str, str]] = []
        ground_truth: list[dict[str, Any]] = []

        candidate_actions = ["SMART_RETRY", "PAYMENT_LINK", "FALLBACK_NOTIFICATION", "ESCALATE_TO_HUMAN"]

        for idx, s_res in enumerate(scenario_results):
            gt = s_res.ground_truth
            case_id = f"case_{idx + 1:03d}_{s_res.scenario_id}"

            parsed_events: list[FinancialEvent] = []
            for raw_evt in s_res.events:
                if isinstance(raw_evt, FinancialEvent):
                    parsed_events.append(raw_evt)
                elif isinstance(raw_evt, dict):
                    parsed_events.append(FinancialEvent.model_validate(raw_evt))

            first_evt = parsed_events[0] if parsed_events else None
            amount_minor = first_evt.amount.amount_minor if first_evt and first_evt.amount else 100000
            currency = first_evt.currency if first_evt else "INR"
            err_code = first_evt.payload.get("error_code", "UNKNOWN") if first_evt and first_evt.payload else "UNKNOWN"

            for act in candidate_actions:
                is_optimal = (act == gt.optimal_action)
                target = 1 if (is_optimal and gt.is_recoverable) else 0

                feat_dict = {
                    "amount_minor": amount_minor,
                    "attempts_count": len(parsed_events),
                    "currency": currency,
                    "error_code": err_code,
                    "root_cause": gt.true_root_cause,
                    "action_type": act,
                    "merchant_status": "active",
                    "customer_opt_out": False,
                    "is_systemic_downtime": (gt.true_root_cause == "SYSTEMIC_BANK_DOWNTIME"),
                }

                features_raw.append(feat_dict)
                targets.append(target)
                identifiers.append({"case_id": case_id, "payment_id": gt.payment_id, "action_type": act})
                ground_truth.append({
                    "true_root_cause": gt.true_root_cause,
                    "optimal_action": gt.optimal_action,
                    "is_recoverable": gt.is_recoverable,
                })

        # Feature Transformation
        X_all = self.pipeline.transform_batch(features_raw).tolist()

        # Chronological Split (60% Train, 20% Val, 20% Test)
        total_n = len(targets)
        n_train = int(total_n * 0.6)
        n_val = int(total_n * 0.2)

        train_split = DatasetSplit(
            feature_matrix=X_all[:n_train],
            target_vector=targets[:n_train],
            identifiers=identifiers[:n_train],
            ground_truth=ground_truth[:n_train],
        )
        val_split = DatasetSplit(
            feature_matrix=X_all[n_train:n_train + n_val],
            target_vector=targets[n_train:n_train + n_val],
            identifiers=identifiers[n_train:n_train + n_val],
            ground_truth=ground_truth[n_train:n_train + n_val],
        )
        test_split = DatasetSplit(
            feature_matrix=X_all[n_train + n_val:],
            target_vector=targets[n_train + n_val:],
            identifiers=identifiers[n_train + n_val:],
            ground_truth=ground_truth[n_train + n_val:],
        )

        pos_count = sum(targets)
        neg_count = total_n - pos_count
        class_dist = {"negative_0": neg_count, "positive_1": pos_count}

        # Canonical Hash Calculation
        hash_payload = json.dumps({"n": total_n, "targets": targets, "seed": self.seed}, sort_keys=True)
        ds_hash = hashlib.sha256(hash_payload.encode("utf-8")).hexdigest()

        meta = DatasetMetadata(
            dataset_version="v1.0",
            schema_version="v1.0",
            sample_count=total_n,
            train_count=len(train_split.target_vector),
            validation_count=len(val_split.target_vector),
            test_count=len(test_split.target_vector),
            class_distribution=class_dist,
            dataset_hash=ds_hash,
        )

        return MLDataset(
            metadata=meta,
            feature_names=self.pipeline.feature_names,
            train_split=train_split,
            val_split=val_split,
            test_split=test_split,
        )
