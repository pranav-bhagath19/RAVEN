"""
RAVEN ML Propensity Model Module

Defines BasePropensityModel abstraction and LogisticRegressionPropensityModel implementation.
Output probability is strictly validated to be in range [0.0, 1.0].
Rejects NaN, Infinity, or values out of bounds.
"""

from abc import ABC, abstractmethod
import math
from typing import Any
import numpy as np
from sklearn.linear_model import LogisticRegression  # type: ignore[import-untyped]


class BasePropensityModel(ABC):
    """Abstract Base Class for RAVEN Propensity Scoring Models."""

    @abstractmethod
    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        """Fits model parameters using feature matrix X and binary target vector y."""
        pass

    @abstractmethod
    def predict_probability(self, feature_vector: np.ndarray) -> float:
        """Predicts recovery success probability P(success | state, action) in [0.0, 1.0]."""
        pass

    @abstractmethod
    def model_metadata(self) -> dict[str, Any]:
        """Returns metadata describing model version, type, and parameters."""
        pass


class LogisticRegressionPropensityModel(BasePropensityModel):
    """
    Supervised Logistic Regression Propensity Model predicting recovery success probability.
    Uses scikit-learn LogisticRegression with deterministic random_state.
    """

    def __init__(
        self,
        model_version: str = "v1.0",
        C: float = 1.0,
        random_state: int = 42,
        max_iter: int = 1000,
    ) -> None:
        self.model_version = model_version
        self.model_type = "LogisticRegression"
        self.C = C
        self.random_state = random_state
        self.max_iter = max_iter
        self.model = LogisticRegression(C=C, random_state=random_state, max_iter=max_iter)
        self.is_fitted = False

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        """Fits logistic regression classifier on training feature matrix and target vector."""
        if X.shape[0] == 0 or len(y) == 0:
            raise ValueError("Cannot fit model on empty feature matrix or empty target vector")
        self.model.fit(X, y)
        self.is_fitted = True

    def predict_probability(self, feature_vector: np.ndarray) -> float:
        """
        Predicts binary recovery success probability for a single 1D or 2D feature vector.
        Strictly validates output to ensure 0.0 <= prob <= 1.0.
        """
        if not self.is_fitted:
            # Unfitted model returns fallback baseline probability
            return 0.5

        vec_2d = feature_vector.reshape(1, -1) if feature_vector.ndim == 1 else feature_vector
        proba_matrix = self.model.predict_proba(vec_2d)

        # Get positive class probability (index 1 if binary, else last index)
        if proba_matrix.shape[1] > 1:
            raw_prob = float(proba_matrix[0, 1])
        else:
            raw_prob = float(proba_matrix[0, 0])

        if math.isnan(raw_prob) or math.isinf(raw_prob):
            raise ValueError(f"Model output invalid probability (NaN or Inf): {raw_prob}")

        if not (0.0 <= raw_prob <= 1.0):
            raise ValueError(f"Model output probability out of bounds [0, 1]: {raw_prob}")

        return raw_prob

    def model_metadata(self) -> dict[str, Any]:
        """Returns model configuration and version metadata."""
        return {
            "model_version": self.model_version,
            "model_type": self.model_type,
            "hyperparameters": {"C": self.C, "random_state": self.random_state, "max_iter": self.max_iter},
            "is_fitted": self.is_fitted,
        }

    def save_dict(self) -> dict[str, Any]:
        """Serializes model parameters and metadata into a JSON-compatible dictionary."""
        coef_list = self.model.coef_.tolist() if hasattr(self.model, "coef_") else []
        intercept_list = self.model.intercept_.tolist() if hasattr(self.model, "intercept_") else []
        classes_list = self.model.classes_.tolist() if hasattr(self.model, "classes_") else []

        return {
            "metadata": self.model_metadata(),
            "weights": {
                "coef": coef_list,
                "intercept": intercept_list,
                "classes": classes_list,
            },
        }

    def load_dict(self, data: dict[str, Any]) -> None:
        """Loads model parameters and metadata from a dictionary."""
        meta = data.get("metadata", {})
        self.model_version = str(meta.get("model_version", "v1.0"))
        self.model_type = str(meta.get("model_type", "LogisticRegression"))

        weights = data.get("weights", {})
        if "coef" in weights and "intercept" in weights and "classes" in weights:
            self.model.coef_ = np.array(weights["coef"], dtype=np.float64)
            self.model.intercept_ = np.array(weights["intercept"], dtype=np.float64)
            self.model.classes_ = np.array(weights["classes"], dtype=np.int64)
            self.is_fitted = True
