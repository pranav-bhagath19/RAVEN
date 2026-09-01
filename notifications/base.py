"""
RAVEN Notification Provider Interfaces

Defines provider-independent interfaces for dispatching Email, SMS, and WhatsApp notifications.
"""

from abc import ABC, abstractmethod
from typing import Any
from pydantic import BaseModel


class NotificationResult(BaseModel):
    """Notification dispatch outcome metadata."""

    provider_name: str
    channel: str
    recipient: str
    message_id: str
    status: str
    delivered: bool
    details: dict[str, Any] = {}


class BaseNotificationProvider(ABC):
    """Abstract Base Notification Provider."""

    def __init__(self, provider_name: str) -> None:
        self.provider_name = provider_name

    @abstractmethod
    def send_notification(
        self,
        recipient: str,
        content: str,
        subject: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> NotificationResult:
        """Dispatches notification to recipient."""
        pass
