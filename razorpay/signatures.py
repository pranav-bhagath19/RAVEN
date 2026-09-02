"""
Razorpay Webhook HMAC-SHA256 Signature Verification Module

Provides constant-time HMAC-SHA256 signature verification over raw HTTP request bytes.
Prevents timing attacks and payload tampering.
"""

import hashlib
import hmac
import logging

logger = logging.getLogger(__name__)


def verify_razorpay_webhook_signature(
    raw_body: bytes,
    signature: str | None,
    secret: str | None,
) -> bool:
    """
    Verifies Razorpay webhook X-Razorpay-Signature HTTP header against raw request body using HMAC-SHA256.
    Uses hmac.compare_digest for constant-time comparison.
    Returns True if valid, False otherwise.
    """
    if not raw_body or not signature or not secret:
        return False

    try:
        expected_signature = hmac.new(
            key=secret.encode("utf-8"),
            msg=raw_body,
            digestmod=hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(expected_signature.lower(), signature.strip().lower())
    except Exception as err:
        logger.warning(f"Signature verification failed due to exception: {err!s}")
        return False
