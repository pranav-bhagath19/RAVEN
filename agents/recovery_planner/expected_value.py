"""
RAVEN Deterministic Expected Value Calculator

Provides pure, deterministic arithmetic for monetary Expected Value calculations.
Enforces integer minor unit preservation and strict probability bounds [0.0, 1.0].
LLMs are strictly prohibited from calculating monetary values.
"""

from pydantic import BaseModel, Field
from domain.exceptions import InvalidMoneyError


class ExpectedValue(BaseModel):
    """
    Deterministic Expected Value calculation result in integer minor units.
    """

    probability: float = Field(..., ge=0.0, le=1.0, description="Success probability (0.0 to 1.0)")
    amount_minor: int = Field(..., ge=0, description="Revenue at risk in integer minor units")
    cost_minor: int = Field(0, ge=0, description="Execution cost in integer minor units")
    expected_recovery_minor: int = Field(..., description="Expected gross recovery in minor units")
    expected_value_minor: int = Field(..., description="Net expected recovery value (gross - cost) in minor units")


def calculate_expected_value(
    probability: float,
    amount_minor: int,
    cost_minor: int = 0,
) -> ExpectedValue:
    """
    Calculates Expected Value deterministically in integer minor units:
    Expected Gross Recovery = round(probability * amount_minor)
    Expected Net Value = Expected Gross Recovery - cost_minor
    """
    if not isinstance(probability, (int, float)) or isinstance(probability, bool):
        raise InvalidMoneyError(f"Probability must be a float or int, got {type(probability).__name__}")

    if not (0.0 <= probability <= 1.0):
        raise InvalidMoneyError(f"Probability must be between 0.0 and 1.0 inclusive, got {probability}")

    if not isinstance(amount_minor, int) or isinstance(amount_minor, bool) or amount_minor < 0:
        raise InvalidMoneyError(f"Monetary amount_minor must be a non-negative integer, got {type(amount_minor).__name__}")

    if not isinstance(cost_minor, int) or isinstance(cost_minor, bool) or cost_minor < 0:
        raise InvalidMoneyError(f"Monetary cost_minor must be a non-negative integer, got {type(cost_minor).__name__}")

    # Deterministic calculation rounding to nearest integer minor unit (e.g. paise)
    expected_gross = round(float(probability) * float(amount_minor))
    expected_net = expected_gross - cost_minor

    return ExpectedValue(
        probability=float(probability),
        amount_minor=amount_minor,
        cost_minor=cost_minor,
        expected_recovery_minor=expected_gross,
        expected_value_minor=expected_net,
    )
