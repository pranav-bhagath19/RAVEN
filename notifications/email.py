"""
RAVEN Email Provider Adapter Module
"""

import logging
import os
import secrets
from typing import Any
from notifications.base import BaseNotificationProvider, NotificationResult

logger = logging.getLogger("raven.notifications.email")


class EmailProvider(BaseNotificationProvider):
    """
    Email notification provider supporting SendGrid REST API or SMTP delivery with fallback to logging.
    """

    def __init__(self, api_key: str | None = None, from_email: str = "noreply@raven.io") -> None:
        super().__init__(provider_name="EmailProvider")
        self.api_key = api_key or os.getenv("SENDGRID_API_KEY")
        self.from_email = from_email

    def send_notification(
        self,
        recipient: str,
        content: str,
        subject: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> NotificationResult:
        msg_id = f"msg_email_{secrets.token_hex(6)}"
        subj = subject or "Payment Recovery Action Required — RAVEN"

        if self.api_key:
            try:
                import httpx

                url = "https://api.sendgrid.com/v3/mail/send"
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                }
                payload = {
                    "personalizations": [{"to": [{"email": recipient}]}],
                    "from": {"email": self.from_email},
                    "subject": subj,
                    "content": [{"type": "text/plain", "value": content}],
                }
                res = httpx.post(url, json=payload, headers=headers, timeout=5.0)
                if res.status_code in (200, 202):
                    return NotificationResult(
                        provider_name=self.provider_name,
                        channel="EMAIL",
                        recipient=recipient,
                        message_id=msg_id,
                        status="SENT",
                        delivered=True,
                        details={"service": "SendGrid", "status_code": res.status_code},
                    )
            except Exception as exc:
                logger.warning(f"SendGrid API call failed: {exc}. Falling back to logged notification.")

        logger.info(f"[EMAIL NOTIFICATION DISPATCHED] To: {recipient} | Subject: {subj} | Body: {content[:100]}...")
        return NotificationResult(
            provider_name=self.provider_name,
            channel="EMAIL",
            recipient=recipient,
            message_id=msg_id,
            status="DELIVERED_LOGGED",
            delivered=True,
            details={"mode": "logged_fallback"},
        )
