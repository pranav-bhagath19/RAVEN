"""
Razorpay API Client Module

Defines BaseRazorpayClient abstraction, structured exceptions, and MockRazorpayClient implementation for offline testing and demo execution.
"""

from abc import ABC, abstractmethod
from typing import Any


class RazorpayAPIError(Exception):
    """Structured exception for Razorpay REST API errors."""

    def __init__(self, status_code: int, error_code: str, message: str) -> None:
        super().__init__(f"Razorpay API Error ({status_code}) [{error_code}]: {message}")
        self.status_code = status_code
        self.error_code = error_code
        self.message = message


class RazorpayTimeoutError(Exception):
    """Structured exception for Razorpay HTTP timeouts."""

    def __init__(self, endpoint: str, timeout_seconds: float) -> None:
        super().__init__(f"Razorpay request to '{endpoint}' timed out after {timeout_seconds}s")
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds


class BaseRazorpayClient(ABC):
    """Abstract Base Class for Razorpay API Client."""

    @abstractmethod
    def fetch_payment(self, payment_id: str) -> dict[str, Any]:
        """Fetches payment entity from Razorpay API by payment ID."""

    @abstractmethod
    def capture_payment(self, payment_id: str, amount_minor: int, currency: str = "INR") -> dict[str, Any]:
        """Captures an authorized payment."""

    @abstractmethod
    def create_payment_link(
        self,
        payment_id: str,
        amount_minor: int,
        description: str,
        idempotency_key: str,
        currency: str = "INR",
    ) -> dict[str, Any]:
        """Creates payment link with mandatory idempotency key."""

    @abstractmethod
    def get_payment_status(self, payment_id: str) -> str:
        """Returns string status of payment (captured, failed, authorized, refunded)."""


class MockRazorpayClient(BaseRazorpayClient):
    """
    Deterministic Mock Razorpay Client for offline testing and demo runs.
    Does not make external network or API requests.
    """

    def __init__(self, key_id: str = "rzp_test_mock", key_secret: str = "mock_secret") -> None:
        self.key_id = key_id
        self.key_secret = key_secret
        self.payment_links_created: list[dict[str, Any]] = []

    def fetch_payment(self, payment_id: str) -> dict[str, Any]:
        return {
            "id": payment_id,
            "entity": "payment",
            "amount": 150000,
            "currency": "INR",
            "status": "failed",
            "error_code": "GATEWAY_TIMED_OUT",
            "error_description": "Mock payment failure fetch response",
        }

    def capture_payment(self, payment_id: str, amount_minor: int, currency: str = "INR") -> dict[str, Any]:
        return {
            "id": payment_id,
            "entity": "payment",
            "amount": amount_minor,
            "currency": currency,
            "status": "captured",
        }

    def fetch_order(self, order_id: str) -> dict[str, Any]:
        return {
            "id": order_id,
            "entity": "order",
            "amount": 150000,
            "amount_paid": 0,
            "amount_due": 150000,
            "currency": "INR",
            "status": "created",
            "attempts": 1,
        }

    def create_payment_link(
        self,
        payment_id: str,
        amount_minor: int,
        description: str,
        idempotency_key: str,
        currency: str = "INR",
    ) -> dict[str, Any]:
        link_id = f"plink_{idempotency_key[:12]}"
        link_url = f"https://rzp.io/i/{link_id}"
        record = {
            "id": link_id,
            "payment_id": payment_id,
            "amount": amount_minor,
            "currency": currency,
            "short_url": link_url,
            "status": "created",
            "idempotency_key": idempotency_key,
        }
        self.payment_links_created.append(record)
        return record

    def get_payment_status(self, payment_id: str) -> str:
        res = self.fetch_payment(payment_id)
        return res.get("status", "failed")
