"""
RAVEN Simulator Scenarios & Ground Truth Definitions

Defines structured scenario models and ground truth metadata contracts.
"""

from typing import Any
from pydantic import BaseModel, Field
from domain.enums import PaymentStatus


class GroundTruthMetadata(BaseModel):
    """
    Ground truth annotation representing facts known to the simulator.
    Separated strictly from future AI agent inference.
    """

    payment_id: str = Field(..., description="Target payment ID")
    true_root_cause: str = Field(..., description="Ground truth failure cause (e.g. GATEWAY_TIMED_OUT)")
    is_recoverable: bool = Field(..., description="Whether revenue is recoverable")
    organic_recovery_will_occur: bool = Field(..., description="Whether customer will organically retry and succeed")
    optimal_action: str = Field(..., description="Optimal recovery action identifier")
    expected_optimal_delay_seconds: int = Field(0, ge=0, description="Recommended delay before action execution")


class ScenarioResult(BaseModel):
    """
    Complete scenario result packaging synthetic financial events, ground truth metadata,
    and expected reconstructed financial state.
    """

    scenario_id: str = Field(..., description="Unique scenario identifier (e.g. scenario_1_transient_gateway_timeout)")
    scenario_name: str = Field(..., description="Human-readable scenario title")
    description: str = Field(..., description="Detailed narrative description of financial failure mode")
    expected_final_state: PaymentStatus = Field(..., description="Expected final reconstructed PaymentStatus")
    events: list[dict[str, Any]] = Field(default_factory=list, description="Raw financial event payload dictionaries")
    ground_truth: GroundTruthMetadata = Field(..., description="Ground truth evaluation metadata")
