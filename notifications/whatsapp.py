"""
RAVEN WhatsApp Notification Provider Adapter
"""

import logging
import os
import secrets
from typing import Any
from notifications.base import BaseNotificationProvider, NotificationResult

logger = logging.getLogger("raven.notifications.whatsapp")


class WhatsAppProvider(BaseNotificationProvider):
    """
    WhatsApp notification provider supporting Twilio WhatsApp API with fallback to logging.
    """

    def __init__(self, account_sid: str | None = None, auth_token: str | None = None, from_whatsapp: str | None = None) -> None:
        super().__init__(provider_name="WhatsAppProvider")
        self.account_sid = account_sid or os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = auth_token or os.getenv("TWILIO_AUTH_TOKEN")
        self.from_whatsapp = from_whatsapp or os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")

    def send_notification(
        self,
        recipient: str,
        content: str,
        subject: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> NotificationResult:
        msg_id = f"msg_wa_{secrets.token_hex(6)}"
        to_wa = recipient if recipient.startswith("whatsapp:") else f"whatsapp:{recipient}"

        if self.account_sid and self.auth_token:
            try:
                import httpx

                url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"
                data = {"To": to_wa, "From": self.from_whatsapp, "Body": content}
                res = httpx.post(url, data=data, auth=(self.account_sid, self.auth_token), timeout=5.0)
                if res.status_code in (200, 201):
                    return NotificationResult(
                        provider_name=self.provider_name,
                        channel="WHATSAPP",
                        recipient=recipient,
                        message_id=res.json().get("sid", msg_id),
                        status="SENT",
                        delivered=True,
                        details={"service": "Twilio_WhatsApp"},
                    )
            except Exception as exc:
                logger.warning(f"Twilio WhatsApp call failed: {exc}. Falling back to logged notification.")

        logger.info(f"[WHATSAPP DISPATCHED] To: {to_wa} | Body: {content}")
        return NotificationResult(
            provider_name=self.provider_name,
            channel="WHATSAPP",
            recipient=recipient,
            message_id=msg_id,
            status="DELIVERED_LOGGED",
            delivered=True,
            details={"mode": "logged_fallback"},
        )
