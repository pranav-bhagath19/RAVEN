"""
Unit Tests for Razorpay Webhook Mapper
"""

from razorpay.mapper import RazorpayWebhookMapper


def test_mapper_payment_failed_event():
    raw_payload = {
        "entity": "event",
        "account_id": "acc_mer_test",
        "event": "payment.failed",
        "contains": ["payment"],
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_test_failed_100",
                    "entity": "payment",
                    "amount": 150000,
                    "currency": "INR",
                    "status": "failed",
                    "order_id": "order_test_100",
                    "error_code": "GATEWAY_TIMED_OUT",
                    "error_description": "Gateway timed out",
                    "created_at": 1755777600,
                }
            }
        },
        "created_at": 1755777600,
    }

    event = RazorpayWebhookMapper.map_to_canonical_event(raw_payload)

    assert event.entity_id == "pay_test_failed_100"
    assert event.event_type == "payment.failed"
    assert event.amount is not None
    assert event.amount.amount_minor == 150000
    assert event.payload["error_code"] == "GATEWAY_TIMED_OUT"
    assert event.event_hash != ""


def test_mapper_payment_captured_event():
    raw_payload = {
        "entity": "event",
        "account_id": "acc_mer_test",
        "event": "payment.captured",
        "contains": ["payment"],
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_test_cap_200",
                    "entity": "payment",
                    "amount": 250000,
                    "currency": "INR",
                    "status": "captured",
                    "captured": True,
                    "created_at": 1755777600,
                }
            }
        },
        "created_at": 1755777600,
    }

    event = RazorpayWebhookMapper.map_to_canonical_event(raw_payload)

    assert event.entity_id == "pay_test_cap_200"
    assert event.event_type == "payment.captured"
    assert event.amount is not None
    assert event.amount.amount_minor == 250000
