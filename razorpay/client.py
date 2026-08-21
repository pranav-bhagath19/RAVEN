"""
Razorpay API Client Module

Defines BaseRazorpayClient abstraction and MockRazorpayClient implementation for offline testing and demo execution.
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseRazorpayClient(ABC):
    """Abstract Base Class for Razorpay API Client."""

    @abstractmethod
    def fetch_payment(self, payment_id: str) -> dict[str, Any]:
        """Fetches payment entity from Razorpay API."""
        pass

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
        pass


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
