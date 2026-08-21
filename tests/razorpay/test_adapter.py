"""
Unit Tests for Razorpay Adapter and Mock Client
"""

from razorpay.adapter import RazorpayAdapter
from razorpay.client import MockRazorpayClient


def test_mock_razorpay_client():
    client = MockRazorpayClient()

    # Fetch Payment
    pmt = client.fetch_payment("pay_test_100")
    assert pmt["id"] == "pay_test_100"
    assert pmt["status"] == "failed"

    # Create Payment Link
    link = client.create_payment_link(
        payment_id="pay_test_100",
        amount_minor=150000,
        description="Payment Link Test",
        idempotency_key="idempotent_test_key_100",
    )
    assert link["payment_id"] == "pay_test_100"
    assert link["amount"] == 150000
    assert link["idempotency_key"] == "idempotent_test_key_100"
    assert len(client.payment_links_created) == 1


def test_razorpay_adapter_delegation():
    adapter = RazorpayAdapter()
    pmt = adapter.fetch_payment("pay_adapter_1")
    assert pmt["id"] == "pay_adapter_1"
