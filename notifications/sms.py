"""
RAVEN SMS Notification Provider Adapter
"""

import logging
import os
import secrets
from typing import Any
from notifications.base import BaseNotificationProvider, NotificationResult

logger = logging.getLogger("raven.notifications.sms")


class SMSProvider(BaseNotificationProvider):
    """
    SMS notification provider supporting Twilio REST API with fallback to logging.
    """

    def __init__(self, account_sid: str | None = None, auth_token: str | None = None, from_number: str | None = None) -> None:
        super().__init__(provider_name="SMSProvider")
        self.account_sid = account_sid or os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = auth_token or os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = from_number or os.getenv("TWILIO_FROM_NUMBER", "+15005550006")

    def send_notification(
        self,
        recipient: str,
        content: str,
        subject: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> NotificationResult:
        msg_id = f"msg_sms_{secrets.token_hex(6)}"

        if self.account_sid and self.auth_token:
            try:
                import httpx

                url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"
                data = {"To": recipient, "From": self.from_number, "Body": content}
                res = httpx.post(url, data=data, auth=(self.account_sid, self.auth_token), timeout=5.0)
                if res.status_code in (200, 201):
                    return NotificationResult(
                        provider_name=self.provider_name,
                        channel="SMS",
                        recipient=recipient,
                        message_id=res.json().get("sid", msg_id),
                        status="SENT",
                        delivered=True,
                        details={"service": "Twilio_SMS"},
                    )
            except Exception as exc:
                logger.warning(f"Twilio SMS call failed: {exc}. Falling back to logged notification.")

        logger.info(f"[SMS DISPATCHED] To: {recipient} | Body: {content}")
        return NotificationResult(
            provider_name=self.provider_name,
            channel="SMS",
            recipient=recipient,
            message_id=msg_id,
            status="DELIVERED_LOGGED",
            delivered=True,
            details={"mode": "logged_fallback"},
        )
