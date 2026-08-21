"""
RAVEN Synthetic Data Simulator Package

Provides deterministic generation, multi-scenario simulation, ground-truth tagging,
and serialization of financial event streams.
"""

from simulator.exporter import export_dataset
from simulator.generator import SyntheticDataGenerator
from simulator.scenarios import GroundTruthMetadata, ScenarioResult

__all__ = [
    "SyntheticDataGenerator",
    "ScenarioResult",
    "GroundTruthMetadata",
    "export_dataset",
]
