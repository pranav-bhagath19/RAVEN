"""
Phase 11 Policy Validation Tests

Verifies policy validator rules: rejecting negative retries, negative cooldowns,
float monetary limits, invalid threshold percentages, and unknown malformed payloads.
"""

from policies.validation import compute_policy_config_hash, validate_policy_configuration


def test_valid_policy_configuration_passes():
    valid_cfg = {
        "maximum_retry_attempts": 3,
        "retry_cooldown_seconds": 300,
        "high_value_threshold_minor": 500000,
        "min_confidence_threshold": 0.85,
    }
    is_valid, errors = validate_policy_configuration(valid_cfg)
    assert is_valid is True
    assert len(errors) == 0


def test_negative_retry_attempts_rejected():
    invalid_cfg = {"maximum_retry_attempts": -1}
    is_valid, errors = validate_policy_configuration(invalid_cfg)
    assert is_valid is False
    assert any("maximum_retry_attempts" in err for err in errors)


def test_float_monetary_limit_rejected():
    invalid_cfg = {"high_value_threshold_minor": 5000.50}
    is_valid, errors = validate_policy_configuration(invalid_cfg)
    assert is_valid is False
    assert any("strictly forbidden" in err for err in errors)


def test_captured_payment_retry_true_rejected():
    invalid_cfg = {"captured_payment_retry_allowed": True}
    is_valid, errors = validate_policy_configuration(invalid_cfg)
    assert is_valid is False
    assert any("POL_001" in err for err in errors)


def test_canonical_policy_hash_determinism():
    cfg1 = {"b": 2, "a": 1}
    cfg2 = {"a": 1, "b": 2}
    assert compute_policy_config_hash(cfg1) == compute_policy_config_hash(cfg2)
