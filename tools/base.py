"""
RAVEN Tool Infrastructure Base Module

Defines BaseTool abstraction and ToolResult schema for side-effect operations.
"""

from datetime import datetime, timezone
import uuid
from typing import Any
from pydantic import BaseModel, Field
from domain.enums import RecoveryActionType


class ToolResult(BaseModel):
    """
    Structured outcome of a side-effect tool execution.
    """

    execution_id: str = Field(default_factory=lambda: f"exec_{uuid.uuid4().hex[:12]}", description="Unique Execution ID")
    tool_name: str = Field(..., description="Executed tool identifier")
    action_id: str = Field(..., description="Associated Recovery Action ID")
    payment_id: str = Field(..., description="Associated Payment ID")
    status: str = Field(..., description="Outcome status: SIMULATED_SUCCESS, SIMULATED_FAILURE, REJECTED, DUPLICATE")
    payload: dict[str, Any] = Field(default_factory=dict, description="Execution payload snapshot")
    executed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Execution timestamp in UTC",
    )


class BaseTool(BaseModel):
    """
    Base class for RAVEN side-effect execution tools.
    """

    name: str = Field(..., description="Human-readable tool name")
    action_type: RecoveryActionType = Field(..., description="Target RecoveryActionType")

    def validate_parameters(self, parameters: dict[str, Any]) -> bool:
        """Validates action parameters before execution."""
        return True

    def execute(self, action_id: str, payment_id: str, parameters: dict[str, Any]) -> ToolResult:
        """Executes tool operation."""
        raise NotImplementedError("Subclasses must implement execute()")
