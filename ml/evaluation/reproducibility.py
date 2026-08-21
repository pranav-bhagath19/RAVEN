"""
RAVEN Benchmark Reproducibility and Hash Verification Module

Provides canonical JSON serialization and SHA-256 hashing for benchmark reports.
Ensures identical seeds produce identical cryptographic benchmark hashes.
"""

import hashlib
import json
from typing import Any
from ml.evaluation.models import BenchmarkReport


def canonicalize_report_data(data: dict[str, Any]) -> dict[str, Any]:
    """
    Recursively strips non-deterministic execution fields (timestamps, latencies) for reproducible hashing.
    """
    if isinstance(data, dict):
        cleaned: dict[str, Any] = {}
        for k, v in sorted(data.items()):
            # Omit non-deterministic runtime attributes from cryptographic hash
            if k in ("generated_at", "latency_ms", "decision_latency_ms", "average_decision_latency_ms", "p95_decision_latency_ms", "benchmark_hash"):
                continue
            cleaned[k] = canonicalize_report_data(v)
        return cleaned
    elif isinstance(data, list):
        return [canonicalize_report_data(item) for item in data]
    return data


def compute_canonical_benchmark_hash(report: BenchmarkReport) -> str:
    """
    Computes a deterministic SHA-256 hex digest over the canonical report payload.
    Independent of execution timestamps or system latency variations.
    """
    report_dict = report.model_dump()
    cleaned_dict = canonicalize_report_data(report_dict)
    canonical_json = json.dumps(cleaned_dict, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
