"""
Tests for Phase 9 Control Plane Authentication & Rate Limiting
"""

import pytest
from fastapi import HTTPException
from apps.api.auth import UserIdentity, require_control_permission
from apps.api.rate_limiter import TokenBucketRateLimiter


def test_rbac_permission_enforcement():
    read_user = UserIdentity(role="OPERATIONS_READ")
    control_user = UserIdentity(role="OPERATIONS_CONTROL")

    assert read_user.can_control() is False
    assert control_user.can_control() is True

    with pytest.raises(HTTPException) as exc_info:
        require_control_permission(read_user)
    assert exc_info.value.status_code == 403

    assert require_control_permission(control_user) == control_user


def test_token_bucket_rate_limiter():
    limiter = TokenBucketRateLimiter(requests_per_minute=2)

    limiter.check_rate_limit("client_100")
    limiter.check_rate_limit("client_100")

    with pytest.raises(HTTPException) as exc_info:
        limiter.check_rate_limit("client_100")
    assert exc_info.value.status_code == 429
