"""
RAVEN Model Calibration Analyzer Module

Evaluates predicted probability calibration against empirical recovery outcomes.
Calculates Brier Score, Expected Calibration Error (ECE), and binned reliability metrics.
"""

from typing import Any
from pydantic import BaseModel, Field


class CalibrationReport(BaseModel):
    """Calibrated reliability metrics summary."""

    total_samples: int = Field(..., ge=0)
    brier_score: float = Field(..., ge=0.0, le=1.0)
    expected_calibration_error: float = Field(..., ge=0.0, le=1.0)
    reliability_bins: list[dict[str, Any]] = Field(default_factory=list)
    calibration_status: str = Field("WELL_CALIBRATED", description="WELL_CALIBRATED, MODERATELY_CALIBRATED, MISCALIBRATED")


class CalibrationAnalyzer:
    """
    Computes deterministic probability calibration metrics.
    """

    def analyze_calibration(
        self,
        y_true: list[int],
        y_prob: list[float],
        n_bins: int = 5,
    ) -> CalibrationReport:
        """Computes Brier score, Expected Calibration Error (ECE), and reliability bins."""
        if not y_true or len(y_true) != len(y_prob):
            return CalibrationReport(
                total_samples=0,
                brier_score=0.0,
                expected_calibration_error=0.0,
                reliability_bins=[],
                calibration_status="NO_DATA",
            )

        n = len(y_true)

        # 1. Brier Score
        brier = sum((p - y) ** 2 for p, y in zip(y_prob, y_true)) / n

        # 2. Equal-width binning for ECE
        bin_boundaries = [i / n_bins for i in range(n_bins + 1)]
        bins: list[dict[str, Any]] = []
        total_ece = 0.0

        for i in range(n_bins):
            low = bin_boundaries[i]
            high = bin_boundaries[i + 1]

            # Collect items in bin [low, high)
            bin_indices = [
                idx
                for idx, p in enumerate(y_prob)
                if (low <= p < high) or (i == n_bins - 1 and low <= p <= high)
            ]
            bin_size = len(bin_indices)

            if bin_size > 0:
                bin_prob_avg = sum(y_prob[idx] for idx in bin_indices) / bin_size
                bin_acc_avg = sum(y_true[idx] for idx in bin_indices) / bin_size
                abs_diff = abs(bin_prob_avg - bin_acc_avg)
                total_ece += (bin_size / n) * abs_diff

                bins.append(
                    {
                        "bin_index": i + 1,
                        "range": f"[{low:.2f}, {high:.2f}]",
                        "sample_count": bin_size,
                        "mean_predicted_prob": round(bin_prob_avg, 4),
                        "empirical_accuracy": round(bin_acc_avg, 4),
                        "calibration_gap": round(abs_diff, 4),
                    }
                )

        status = (
            "WELL_CALIBRATED"
            if total_ece < 0.10
            else ("MODERATELY_CALIBRATED" if total_ece < 0.20 else "MISCALIBRATED")
        )

        return CalibrationReport(
            total_samples=n,
            brier_score=round(brier, 4),
            expected_calibration_error=round(total_ece, 4),
            reliability_bins=bins,
            calibration_status=status,
        )
