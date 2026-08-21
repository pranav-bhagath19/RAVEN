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
    Simulates generating and dispatching a WhatsApp/Email payment link.
    """

    name: str = "Payment Link Dispatch Tool"
    action_type: RecoveryActionType = RecoveryActionType.PAYMENT_LINK_DISPATCH

    def execute(self, action_id: str, payment_id: str, parameters: dict[str, Any]) -> ToolResult:
        channel = parameters.get("channel", "WHATSAPP")
        link = f"https://rzp.io/i/simulated_{payment_id[:8]}"
        return ToolResult(
            tool_name="payment_link_dispatch",
            action_id=action_id,
            payment_id=payment_id,
            status="SIMULATED_SUCCESS",
            payload={
                "message": f"Payment link dispatched via {channel}.",
                "channel": channel,
                "payment_link_url": link,
            },
        )


class FallbackChannelNotifyTool(BaseTool):
    """
    Simulates dispatching fallback SMS notification to customer.
    """

    name: str = "Fallback Channel Notify Tool"
    action_type: RecoveryActionType = RecoveryActionType.FALLBACK_CHANNEL_NOTIFY

    def execute(self, action_id: str, payment_id: str, parameters: dict[str, Any]) -> ToolResult:
        channel = parameters.get("channel", "SMS")
        return ToolResult(
            tool_name="fallback_channel_notify",
            action_id=action_id,
            payment_id=payment_id,
            status="SIMULATED_SUCCESS",
            payload={
                "message": f"Fallback notification dispatched via {channel}.",
                "channel": channel,
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
