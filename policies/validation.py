"""
RAVEN Policy Configuration Validation & Canonical Hashing Module

Implements deterministic SHA-256 policy configuration hashing and strict validation
for merchant policy rule parameters. Enforces integer minor-unit monetary limits
and bounds checking to prevent unsafe policy activations.
"""

import hashlib
import json
from typing import Any


def compute_policy_config_hash(config: dict[str, Any]) -> str:
    """
    Computes a canonical, deterministic SHA-256 hex digest over policy configuration dictionary.
    Equivalent configuration dictionaries with different key insertion order produce identical hashes.
    """
    serialized = json.dumps(config, sort_keys=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def validate_policy_configuration(config: dict[str, Any]) -> tuple[bool, list[str]]:
    """
    Validates candidate policy configuration parameters.
    Returns tuple of (is_valid, list_of_validation_error_messages).
    """
    errors: list[str] = []

    if not isinstance(config, dict):
        return False, ["Policy configuration must be a JSON object dictionary."]

    # POL_001 Parameter Validation
    if "captured_payment_retry_allowed" in config:
        val = config["captured_payment_retry_allowed"]
        if not isinstance(val, bool):
            errors.append("POL_001 'captured_payment_retry_allowed' must be a boolean.")
        elif val is True:
            errors.append("POL_001 'captured_payment_retry_allowed' cannot be set to True (violates core payment protection).")

    # POL_002 Parameter Validation
    if "maximum_retry_attempts" in config:
        val = config["maximum_retry_attempts"]
        if not isinstance(val, int) or isinstance(val, bool) or val < 0:
            errors.append("POL_002 'maximum_retry_attempts' must be a non-negative integer.")

    # POL_003 Parameter Validation
    if "retry_cooldown_seconds" in config:
        val = config["retry_cooldown_seconds"]
        if not isinstance(val, int) or isinstance(val, bool) or val < 0:
            errors.append("POL_003 'retry_cooldown_seconds' must be a non-negative integer.")

    # POL_004 Parameter Validation (High-value threshold in minor units)
    if "high_value_threshold_minor" in config:
        val = config["high_value_threshold_minor"]
        if isinstance(val, float):
            errors.append("POL_004 'high_value_threshold_minor' must be an integer minor unit (paise), float values are strictly forbidden.")
        elif not isinstance(val, int) or isinstance(val, bool) or val < 0:
            errors.append("POL_004 'high_value_threshold_minor' must be a non-negative integer.")

    # POL_005 Parameter Validation (Agent confidence threshold)
    if "min_confidence_threshold" in config:
        val = config["min_confidence_threshold"]
        if not isinstance(val, (int, float)) or isinstance(val, bool) or not (0.0 <= float(val) <= 1.0):
            errors.append("POL_005 'min_confidence_threshold' must be a float between 0.0 and 1.0 inclusive.")

    # POL_006 Parameter Validation (Daily message cap)
    if "max_daily_messages" in config:
        val = config["max_daily_messages"]
        if not isinstance(val, int) or isinstance(val, bool) or val < 0:
            errors.append("POL_006 'max_daily_messages' must be a non-negative integer.")

    if "customer_opt_out_required" in config:
        val = config["customer_opt_out_required"]
        if not isinstance(val, bool):
            errors.append("POL_006 'customer_opt_out_required' must be a boolean.")

    # POL_007 Parameter Validation (Bank downtime failure rate threshold)
    if "bank_downtime_failure_threshold" in config:
        val = config["bank_downtime_failure_threshold"]
        if not isinstance(val, (int, float)) or isinstance(val, bool) or not (0.0 <= float(val) <= 1.0):
            errors.append("POL_007 'bank_downtime_failure_threshold' must be a float between 0.0 and 1.0 inclusive.")

    is_valid = len(errors) == 0
    return is_valid, errors
