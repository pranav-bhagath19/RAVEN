"""
Unit Tests for Razorpay Webhook Signature Verification
"""

import hashlib
import hmac
from razorpay.signatures import verify_razorpay_webhook_signature


def test_valid_signature():
    secret = "test_webhook_secret_key"
    payload = b'{"event": "payment.failed", "id": "pay_100"}'
    signature = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()

    assert verify_razorpay_webhook_signature(payload, signature, secret) is True


def test_invalid_signature():
    secret = "test_webhook_secret_key"
    payload = b'{"event": "payment.failed", "id": "pay_100"}'
    wrong_sig = "bad_signature_digest_12345"

    assert verify_razorpay_webhook_signature(payload, wrong_sig, secret) is False


def test_modified_payload():
    secret = "test_webhook_secret_key"
    payload_original = b'{"event": "payment.failed", "amount": 1000}'
    signature = hmac.new(secret.encode("utf-8"), payload_original, hashlib.sha256).hexdigest()

    payload_tampered = b'{"event": "payment.failed", "amount": 9000}'
    assert verify_razorpay_webhook_signature(payload_tampered, signature, secret) is False


def test_wrong_secret():
    secret_a = "secret_key_a"
    secret_b = "secret_key_b"
    payload = b'{"event": "payment.failed"}'
    signature = hmac.new(secret_a.encode("utf-8"), payload, hashlib.sha256).hexdigest()

    assert verify_razorpay_webhook_signature(payload, signature, secret_b) is False


def test_missing_or_empty_parameters():
    assert verify_razorpay_webhook_signature(b"", "sig", "secret") is False
    assert verify_razorpay_webhook_signature(b"data", "", "secret") is False
    assert verify_razorpay_webhook_signature(b"data", "sig", "") is False
    assert verify_razorpay_webhook_signature(b"data", None, "secret") is False
