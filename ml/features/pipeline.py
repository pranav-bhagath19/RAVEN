"""
RAVEN ML Feature Pipeline Module

Implements deterministic feature transformation pipeline producing stable
numerical vectors for training and inference without dictionaries or unordered hash sets.
"""

from typing import Any
import numpy as np
from ml.features.schema import FeatureSchemaV1


class FeaturePipelineV1:
    """
    Deterministic Feature Transformation Pipeline for FeatureSchemaV1.
    Converts domain attributes and raw inputs into normalized, fixed-length numerical feature vectors.
    """

    CATEGORICAL_MAPS = {
        "currency": {"INR": 0.0, "USD": 1.0, "EUR": 2.0, "OTHER": 3.0},
        "error_code": {
            "GATEWAY_TIMED_OUT": 0.0,
            "AUTHENTICATION_FAILED": 1.0,
            "INSUFFICIENT_FUNDS": 2.0,
            "CARD_EXPIRED": 3.0,
            "NETWORK_ERROR": 4.0,
            "BANK_DOWNTIME": 5.0,
            "UNKNOWN": 6.0,
        },
        "root_cause": {
            "TRANSIENT_NETWORK_TIMEOUT": 0.0,
            "SOFT_DECLINE_RETRYABLE": 1.0,
            "HARD_DECLINE_CARD_EXPIRED": 2.0,
            "HARD_DECLINE_INSUFFICIENT_FUNDS": 3.0,
            "SYSTEMIC_BANK_DOWNTIME": 4.0,
            "ABANDONED_CHECKOUT": 5.0,
            "CUSTOMER_OPT_OUT": 6.0,
            "UNKNOWN": 7.0,
        },
        "action_type": {
            "SMART_RETRY": 0.0,
            "PAYMENT_LINK": 1.0,
            "FALLBACK_NOTIFICATION": 2.0,
            "ESCALATE_TO_HUMAN": 3.0,
            "NO_ACTION": 4.0,
            "UNKNOWN": 5.0,
        },
        "merchant_status": {"active": 0.0, "suspended": 1.0, "unknown": 2.0},
    }

    def __init__(self) -> None:
        self.schema_version = "v1.0"
        self.feature_names = [
            "amount_scaled",
            "attempts_count",
            "currency_code",
            "error_code_encoded",
            "root_cause_encoded",
            "action_type_encoded",
            "merchant_status_encoded",
            "customer_opt_out_flag",
            "is_systemic_downtime_flag",
        ]

    def transform_single(self, input_dict: dict[str, Any]) -> np.ndarray:
        """
        Transforms a single raw feature dictionary into a 1D float64 numpy array.
        """
        validated = FeatureSchemaV1.validate_raw_input(input_dict)

        amount_scaled = float(validated["amount_minor"]) / 1_000_000.0
        attempts_count = float(validated["attempts_count"])

        currency_code = self.CATEGORICAL_MAPS["currency"].get(validated["currency"].upper(), 3.0)
        error_code_encoded = self.CATEGORICAL_MAPS["error_code"].get(validated["error_code"].upper(), 6.0)
        root_cause_encoded = self.CATEGORICAL_MAPS["root_cause"].get(validated["root_cause"].upper(), 7.0)
        action_type_encoded = self.CATEGORICAL_MAPS["action_type"].get(validated["action_type"].upper(), 5.0)
        merchant_status_encoded = self.CATEGORICAL_MAPS["merchant_status"].get(validated["merchant_status"].lower(), 2.0)

        customer_opt_out_flag = 1.0 if validated["customer_opt_out"] else 0.0
        is_systemic_downtime_flag = 1.0 if validated["is_systemic_downtime"] else 0.0

        vec = np.array(
            [
                amount_scaled,
                attempts_count,
                currency_code,
                error_code_encoded,
                root_cause_encoded,
                action_type_encoded,
                merchant_status_encoded,
                customer_opt_out_flag,
                is_systemic_downtime_flag,
            ],
            dtype=np.float64,
        )
        return vec

    def transform_batch(self, batch_inputs: list[dict[str, Any]]) -> np.ndarray:
        """
        Transforms a list of raw feature dictionaries into a 2D float64 numpy array of shape (N, num_features).
        """
        if not batch_inputs:
            return np.empty((0, len(self.feature_names)), dtype=np.float64)

        rows = [self.transform_single(inp) for inp in batch_inputs]
        return np.vstack(rows)
