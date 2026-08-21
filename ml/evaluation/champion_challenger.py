"""
RAVEN Champion vs. Challenger Evaluation Module

Executes deterministic side-by-side comparative evaluation of Champion and Challenger models.
Generates canonical SHA-256 evaluation report hash for audit verification.
"""

import hashlib
import json
from typing import Any
from pydantic import BaseModel, Field


class ChampionChallengerReport(BaseModel):
    """Side-by-side comparative evaluation report."""

    champion_version: str
    challenger_version: str
    champion_metrics: dict[str, Any]
    challenger_metrics: dict[str, Any]
    metrics_delta: dict[str, float]
    recommendation: str = Field("RETAIN_CHAMPION", description="RETAIN_CHAMPION or PROMOTE_CHALLENGER_RECOMMENDED")
    report_hash: str = Field(..., description="Canonical SHA-256 hex digest of evaluation report")


class ChampionChallengerEvaluator:
    """
    Evaluates Champion vs Challenger models deterministically.
    """

    def evaluate(
        self,
        champion_version: str,
        champion_metrics: dict[str, Any],
        challenger_version: str,
        challenger_metrics: dict[str, Any],
    ) -> ChampionChallengerReport:
        """Computes metric deltas and generates deterministic report hash."""
        champ_auc = float(champion_metrics.get("roc_auc", 0.90))
        chall_auc = float(challenger_metrics.get("roc_auc", 0.92))
        auc_delta = round(chall_auc - champ_auc, 4)

        champ_brier = float(champion_metrics.get("brier_score", 0.09))
        chall_brier = float(challenger_metrics.get("brier_score", 0.08))
        brier_delta = round(chall_brier - champ_brier, 4)

        metrics_delta = {
            "roc_auc_delta": auc_delta,
            "brier_score_delta": brier_delta,
        }

        recommendation = (
            "PROMOTE_CHALLENGER_RECOMMENDED"
            if (auc_delta > 0.01 and brier_delta <= 0.0)
            else "RETAIN_CHAMPION"
        )

        payload = {
            "champion_version": champion_version,
            "challenger_version": challenger_version,
            "champion_metrics": champion_metrics,
            "challenger_metrics": challenger_metrics,
            "metrics_delta": metrics_delta,
            "recommendation": recommendation,
        }

        serialized = json.dumps(payload, sort_keys=True)
        report_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()

        return ChampionChallengerReport(
            champion_version=champion_version,
            challenger_version=challenger_version,
            champion_metrics=champion_metrics,
            challenger_metrics=challenger_metrics,
            metrics_delta=metrics_delta,
            recommendation=recommendation,
            report_hash=report_hash,
        )
