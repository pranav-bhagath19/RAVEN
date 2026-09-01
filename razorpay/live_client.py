"""
RAVEN Live Razorpay API Gateway Client

Implements production API integration with Razorpay REST endpoints.
Safely falls back to Mock client when placeholder keys or demo mode is active.
"""

import logging
from typing import Any
import httpx
from razorpay.client import BaseRazorpayClient, MockRazorpayClient, RazorpayAPIError, RazorpayTimeoutError

logger = logging.getLogger("raven.razorpay.live_client")


class LiveRazorpayClient(BaseRazorpayClient):
    """
    Live Razorpay API Gateway Client communicating with official Razorpay HTTPS REST endpoints.
    Requires valid key_id and key_secret from configuration.
    """

    def __init__(
        self,
        key_id: str,
        key_secret: str,
        base_url: str = "https://api.razorpay.com/v1",
        timeout_seconds: float = 10.0,
    ) -> None:
        self.key_id = key_id
        self.key_secret = key_secret
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout_seconds
        self._mock_fallback = MockRazorpayClient()

    def _is_placeholder(self) -> bool:
        """Returns True if credentials are test placeholders."""
        return (
            not self.key_id
            or "placeholder" in self.key_id.lower()
            or not self.key_secret
            or "placeholder" in self.key_secret.lower()
        )

    def fetch_payment(self, payment_id: str) -> dict[str, Any]:
        """Fetches payment entity by ID from Razorpay REST API."""
        if self._is_placeholder():
            return self._mock_fallback.fetch_payment(payment_id)

        url = f"{self.base_url}/payments/{payment_id}"
        headers = {"X-Request-Correlation-ID": f"corr_rzp_{payment_id[:8]}"}
        try:
            response = httpx.get(url, auth=(self.key_id, self.key_secret), headers=headers, timeout=self.timeout)
            if response.status_code != 200:
                err_json = response.json().get("error", {})
                raise RazorpayAPIError(
                    status_code=response.status_code,
                    error_code=err_json.get("code", "BAD_REQUEST"),
                    message=err_json.get("description", "Razorpay API error"),
                )
            res_dict: dict[str, Any] = response.json()
            return res_dict
        except httpx.TimeoutException as exc:
            logger.warning(f"Razorpay timeout fetching payment {payment_id}: {exc}")
            raise RazorpayTimeoutError(endpoint=url, timeout_seconds=self.timeout) from exc

    def fetch_order(self, order_id: str) -> dict[str, Any]:
        """Fetches order entity by ID from Razorpay REST API."""
        if self._is_placeholder():
            return self._mock_fallback.fetch_order(order_id)

        url = f"{self.base_url}/orders/{order_id}"
        headers = {"X-Request-Correlation-ID": f"corr_rzp_ord_{order_id[:8]}"}
        try:
            response = httpx.get(url, auth=(self.key_id, self.key_secret), headers=headers, timeout=self.timeout)
            if response.status_code != 200:
                err_json = response.json().get("error", {})
                raise RazorpayAPIError(
                    status_code=response.status_code,
                    error_code=err_json.get("code", "BAD_REQUEST"),
                    message=err_json.get("description", "Razorpay API error"),
                )
            res_dict: dict[str, Any] = response.json()
            return res_dict
        except httpx.TimeoutException as exc:
            logger.warning(f"Razorpay timeout fetching order {order_id}: {exc}")
            raise RazorpayTimeoutError(endpoint=url, timeout_seconds=self.timeout) from exc

    def create_payment_link(
        self,
        payment_id: str,
        amount_minor: int,
        description: str,
        idempotency_key: str,
        currency: str = "INR",
    ) -> dict[str, Any]:
        """Creates a Razorpay Payment Link entity via REST API."""
        if self._is_placeholder():
            return self._mock_fallback.create_payment_link(
                payment_id=payment_id,
                amount_minor=amount_minor,
                description=description,
                idempotency_key=idempotency_key,
                currency=currency,
            )

        url = f"{self.base_url}/payment_links"
        payload = {
            "amount": amount_minor,
            "currency": currency,
            "description": description,
            "reference_id": payment_id,
        }
        headers = {
            "X-Razorpay-Idempotency-Key": idempotency_key,
            "X-Request-Correlation-ID": f"corr_link_{payment_id[:8]}",
        }
        try:
            response = httpx.post(url, auth=(self.key_id, self.key_secret), json=payload, headers=headers, timeout=self.timeout)
            if response.status_code not in (200, 201):
                err_json = response.json().get("error", {})
                raise RazorpayAPIError(
                    status_code=response.status_code,
                    error_code=err_json.get("code", "BAD_REQUEST"),
                    message=err_json.get("description", "Razorpay API error"),
                )
            res_dict: dict[str, Any] = response.json()
            return res_dict
        except httpx.TimeoutException as exc:
            logger.warning(f"Razorpay timeout creating payment link for {payment_id}: {exc}")
            raise RazorpayTimeoutError(endpoint=url, timeout_seconds=self.timeout) from exc

    def get_payment_status(self, payment_id: str) -> str:
        """Queries payment status from Razorpay API."""
        res = self.fetch_payment(payment_id)
        return res.get("status", "failed")
