"""
RAVEN LinUCB Contextual Bandit Model Module

Implements a production LinUCB (Linear Upper Confidence Bound) Contextual Bandit algorithm.
Calculates UCB scores: score(a|x) = theta_a^T x + alpha * sqrt(x^T A_a^-1 x).
Guarantees deterministic behavior, finite numerical values (no NaN/inf), and SHA-256 artifact hashing.
Advisory ranking output only — zero tool execution or token minting authority.
"""

import hashlib
import json
import math
from pydantic import BaseModel, Field
from ml.bandits.action_space import BanditActionIdentifier, BanditActionSpace
from ml.bandits.context import BanditContextVector


class BanditScoreResult(BaseModel):
    """Contextual Bandit scoring result for a single candidate action."""

    action_id: str = Field(..., description="Action identifier")
    predicted_reward: float = Field(..., description="Expected reward estimate theta^T x")
    uncertainty_bound: float = Field(..., ge=0.0, description="Exploration bonus alpha * sqrt(x^T A^-1 x)")
    ucb_score: float = Field(..., description="Total Upper Confidence Bound score")
    rank: int = Field(..., ge=1, description="Advisory ranking (1 = top candidate)")


class BanditModelMetadata(BaseModel):
    """Bandit Model Metadata schema."""

    model_version: str = Field(default="v13.0-bandit", description="Model version string")
    algorithm: str = Field(default="LinUCB", description="Algorithm type tag")
    alpha: float = Field(default=0.50, description="Exploration parameter alpha")
    dimension: int = Field(default=12, description="Context vector dimension")
    actions: list[str] = Field(default_factory=BanditActionSpace.get_action_identifiers)
    model_hash: str = Field(..., description="SHA-256 hash of model parameters")


class LinUCBBanditModel:
    """
    LinUCB Contextual Bandit Implementation with ridge-regression covariance matrices A_a.
    """

    def __init__(self, dimension: int = 12, alpha: float = 0.50, seed: int = 42) -> None:
        self.dimension = dimension
        self.alpha = max(0.01, min(2.0, float(alpha)))
        self.seed = seed
        self.actions = BanditActionSpace.get_action_identifiers()

        # Initialize A_a = I_d, b_a = 0_d for each action
        self.A: dict[str, list[list[float]]] = {}
        self.b: dict[str, list[float]] = {}
        self.reset_parameters()

    def reset_parameters(self) -> None:
        """Resets model parameters to identity covariance and zero reward vectors."""
        for act in self.actions:
            # Identity matrix I_d
            self.A[act] = [[1.0 if i == j else 0.0 for j in range(self.dimension)] for i in range(self.dimension)]
            # Zero vector
            self.b[act] = [0.0] * self.dimension

    def _matrix_vector_mult(self, mat: list[list[float]], vec: list[float]) -> list[float]:
        """Helper for matrix-vector multiplication."""
        res = [0.0] * len(vec)
        for i in range(len(mat)):
            s = 0.0
            for j in range(len(vec)):
                s += mat[i][j] * vec[j]
            res[i] = s
        return res

    def _dot_product(self, v1: list[float], v2: list[float]) -> float:
        """Helper for dot product."""
        return sum(x * y for x, y in zip(v1, v2))

    def _simple_invert_diagonal_approx(self, mat: list[list[float]]) -> list[list[float]]:
        """
        Computes diagonal matrix inverse approximation for numerical stability.
        A^-1 ~ diag(1/A_ii).
        """
        dim = len(mat)
        inv = [[0.0] * dim for _ in range(dim)]
        for i in range(dim):
            val = mat[i][i]
            inv[i][i] = 1.0 / val if abs(val) > 1e-9 else 1.0
        return inv

    def score_context(self, context: BanditContextVector, candidate_actions: list[str]) -> list[BanditScoreResult]:
        """
        Calculates UCB scores for all provided candidate actions given the context vector.
        Returns advisory ranked list of BanditScoreResult items.
        """
        x = context.feature_vector
        if len(x) != self.dimension:
            raise ValueError(f"Context vector dimension mismatch: expected {self.dimension}, got {len(x)}")

        scores: list[tuple[str, float, float, float]] = []

        for act in candidate_actions:
            bandit_act = BanditActionSpace.map_recovery_action_to_bandit_action(act).value
            A_mat = self.A.get(bandit_act, self.A[BanditActionIdentifier.NO_ACTION.value])
            b_vec = self.b.get(bandit_act, self.b[BanditActionIdentifier.NO_ACTION.value])

            A_inv = self._simple_invert_diagonal_approx(A_mat)
            theta = self._matrix_vector_mult(A_inv, b_vec)

            pred_reward = self._dot_product(theta, x)
            if math.isnan(pred_reward) or math.isinf(pred_reward):
                pred_reward = 0.0

            # x^T A^-1 x
            A_inv_x = self._matrix_vector_mult(A_inv, x)
            var_term = self._dot_product(x, A_inv_x)
            var_term = max(0.0, var_term)

            uncertainty = self.alpha * math.sqrt(var_term)
            if math.isnan(uncertainty) or math.isinf(uncertainty):
                uncertainty = 0.0

            ucb = pred_reward + uncertainty
            scores.append((act, pred_reward, uncertainty, ucb))

        # Sort descending by UCB score
        scores.sort(key=lambda item: item[3], reverse=True)

        results: list[BanditScoreResult] = []
        for rank_idx, (act, pred, uncert, ucb_val) in enumerate(scores, start=1):
            results.append(
                BanditScoreResult(
                    action_id=act,
                    predicted_reward=round(pred, 4),
                    uncertainty_bound=round(uncert, 4),
                    ucb_score=round(ucb_val, 4),
                    rank=rank_idx,
                )
            )

        return results

    def update(self, action_id: str, context: BanditContextVector, reward: float) -> None:
        """
        Updates parameters A_a += x x^T, b_a += reward * x for selected action.
        """
        bandit_act = BanditActionSpace.map_recovery_action_to_bandit_action(action_id).value
        x = context.feature_vector

        if bandit_act not in self.A:
            return

        # Update A_a += x x^T
        for i in range(self.dimension):
            for j in range(self.dimension):
                self.A[bandit_act][i][j] += x[i] * x[j]

        # Update b_a += reward * x
        for i in range(self.dimension):
            self.b[bandit_act][i] += reward * x[i]

    def compute_integrity_hash(self) -> str:
        """Computes SHA-256 hash of model parameters."""
        data = {"A": self.A, "b": self.b, "alpha": self.alpha, "dimension": self.dimension}
        raw_bytes = json.dumps(data, sort_keys=True).encode("utf-8")
        return hashlib.sha256(raw_bytes).hexdigest()

    def get_metadata(self) -> BanditModelMetadata:
        """Returns model metadata and integrity hash."""
        return BanditModelMetadata(
            model_version="v13.0-bandit",
            algorithm="LinUCB",
            alpha=self.alpha,
            dimension=self.dimension,
            actions=self.actions,
            model_hash=self.compute_integrity_hash(),
        )
