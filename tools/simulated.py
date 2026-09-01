"""
RAVEN Simulated Side-Effect Tools

Implements offline, deterministic simulated tool handlers for:
- Smart Retry
- Payment Link Dispatch
- Fallback Channel Notification
- Human Escalation
"""

from typing import Any
from domain.enums import RecoveryActionType
from tools.base import BaseTool, ToolResult


class SmartRetryTool(BaseTool):
    """
    Simulates scheduling or triggering a gateway payment retry.
    """

    name: str = "Smart Retry Tool"
    action_type: RecoveryActionType = RecoveryActionType.SMART_RETRY

    def execute(self, action_id: str, payment_id: str, parameters: dict[str, Any]) -> ToolResult:
        delay = parameters.get("delay_seconds", 900)
        return ToolResult(
            tool_name="smart_retry",
            action_id=action_id,
            payment_id=payment_id,
            status="SIMULATED_SUCCESS",
            payload={
                "message": f"Payment retry scheduled after {delay} seconds delay.",
                "delay_seconds": delay,
                "target_gateway": "RAZORPAY_GATEWAY",
            },
        )


class PaymentLinkDispatchTool(BaseTool):
    """
    Generates and dispatches a WhatsApp/Email payment link via Notification Adapters.
    """

    name: str = "Payment Link Dispatch Tool"
    action_type: RecoveryActionType = RecoveryActionType.PAYMENT_LINK_DISPATCH

    def execute(self, action_id: str, payment_id: str, parameters: dict[str, Any]) -> ToolResult:
        channel = parameters.get("channel", "WHATSAPP").upper()
        recipient = parameters.get("recipient", "+919876543210")
        amount_minor = parameters.get("amount_minor", 100000)
        link = f"https://rzp.io/i/link_{payment_id[:8]}"
        content = f"Your payment of ₹{amount_minor / 100:.2f} requires authorization. Pay securely here: {link}"

        if channel == "WHATSAPP":
            from notifications.whatsapp import WhatsAppProvider

            res = WhatsAppProvider().send_notification(recipient=recipient, content=content)
        elif channel == "EMAIL":
            from notifications.email import EmailProvider

            res = EmailProvider().send_notification(recipient=recipient, content=content, subject="Payment Recovery Link")
        else:
            from notifications.sms import SMSProvider

            res = SMSProvider().send_notification(recipient=recipient, content=content)

        return ToolResult(
            tool_name="payment_link_dispatch",
            action_id=action_id,
            payment_id=payment_id,
            status="SIMULATED_SUCCESS",
            payload={
                "message": f"Payment link dispatched via {channel}.",
                "channel": channel,
                "payment_link_url": link,
                "notification": res.model_dump(),
            },
        )


class FallbackChannelNotifyTool(BaseTool):
    """
    Dispatches fallback notification to customer via SMS/Email Provider.
    """

    name: str = "Fallback Channel Notify Tool"
    action_type: RecoveryActionType = RecoveryActionType.FALLBACK_CHANNEL_NOTIFY

    def execute(self, action_id: str, payment_id: str, parameters: dict[str, Any]) -> ToolResult:
        channel = parameters.get("channel", "SMS").upper()
        recipient = parameters.get("recipient", "+919876543210")
        content = f"Notice: Payment attempt for reference '{payment_id[:8]}' failed. Please check your banking app."

        if channel == "EMAIL":
            from notifications.email import EmailProvider

            res = EmailProvider().send_notification(recipient=recipient, content=content, subject="Payment Status Alert")
        else:
            from notifications.sms import SMSProvider

            res = SMSProvider().send_notification(recipient=recipient, content=content)

        return ToolResult(
            tool_name="fallback_channel_notify",
            action_id=action_id,
            payment_id=payment_id,
            status="SIMULATED_SUCCESS",
            payload={
                "message": f"Fallback notification dispatched via {channel}.",
                "channel": channel,
                "notification": res.model_dump(),
            },
        )


class EscalateToHumanTool(BaseTool):
    """
    Simulates escalating transaction and action proposal to merchant operations queue.
    """

    name: str = "Escalate To Human Tool"
    action_type: RecoveryActionType = RecoveryActionType.ESCALATE_TO_HUMAN

    def execute(self, action_id: str, payment_id: str, parameters: dict[str, Any]) -> ToolResult:
        reason = parameters.get("reason", "Policy escalation")
        return ToolResult(
            tool_name="escalate_to_human",
            action_id=action_id,
            payment_id=payment_id,
            status="SIMULATED_SUCCESS",
            payload={
                "message": f"Escalated to merchant operations queue. Reason: {reason}",
                "escalation_reason": reason,
                "ticket_id": f"tkt_{action_id[:8]}",
            },
        )
