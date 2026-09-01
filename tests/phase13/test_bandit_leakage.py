"""
RAVEN Phase 13 Security Test Suite: Target Leakage Protection

Verifies that ContextBuilder strictly rejects post-action fields and raises ValueError.
"""

import pytest
from ml.bandits.context import BanditContextBuilder, FORBIDDEN_LEAKAGE_FIELDS


def test_target_leakage_protection_raises_value_error():
    builder = BanditContextBuilder()

    valid_record = {
        "tenant_id": "tenant_01",
        "payment_id": "pay_01",
        "amount_minor": 50000,
        "attempts_count": 1,
        "error_code": "TIMEOUT",
        "root_cause": "TRANSIENT_NETWORK_TIMEOUT",
        "action_type": "RETRY_PAYMENT",
    }

    # Clean context creation works
    ctx = builder.build_context(valid_record)
    assert len(ctx.feature_vector) == 12

    # Injecting any post-action leakage field MUST raise ValueError
    for forbidden_field in FORBIDDEN_LEAKAGE_FIELDS:
        leaky_record = dict(valid_record)
        leaky_record[forbidden_field] = "LEAKED_VALUE"

        with pytest.raises(ValueError) as exc_info:
            builder.build_context(leaky_record)

        assert "Target leakage violation" in str(exc_info.value)
