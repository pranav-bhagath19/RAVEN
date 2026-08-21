"""
Unit Tests for RAVEN ML Feature Pipeline & Leakage Prevention
"""

import pytest
from ml.features.pipeline import FeaturePipelineV1
from ml.features.schema import FeatureSchemaV1


def test_feature_schema_leakage_prevention():
    valid_input = {
        "amount_minor": 100000,
        "currency": "INR",
        "error_code": "GATEWAY_TIMED_OUT",
        "root_cause": "TRANSIENT_NETWORK_TIMEOUT",
        "action_type": "SMART_RETRY",
    }
    validated = FeatureSchemaV1.validate_raw_input(valid_input)
    assert validated["amount_minor"] == 100000

    # Leakage Attempt with Target Field
    leaky_input = dict(valid_input)
    leaky_input["is_recovered"] = True

    with pytest.raises(ValueError, match="Target leakage detected"):
        FeatureSchemaV1.validate_raw_input(leaky_input)


def test_feature_pipeline_transformation_shape_and_values():
    pipeline = FeaturePipelineV1()
    sample = {
        "amount_minor": 250000,
        "attempts_count": 1,
        "currency": "INR",
        "error_code": "GATEWAY_TIMED_OUT",
        "root_cause": "TRANSIENT_NETWORK_TIMEOUT",
        "action_type": "SMART_RETRY",
        "merchant_status": "active",
        "customer_opt_out": False,
        "is_systemic_downtime": False,
    }

    vec = pipeline.transform_single(sample)
    assert vec.ndim == 1
    assert len(vec) == len(pipeline.feature_names)
    assert vec[0] == pytest.approx(0.25)
    assert vec[1] == 1.0

    batch = pipeline.transform_batch([sample, sample])
    assert batch.shape == (2, len(pipeline.feature_names))
