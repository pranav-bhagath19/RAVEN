"""
Unit Tests for Benchmark CLI and Report Generation
"""

import json
import os
from ml.evaluation.benchmark import run_benchmark


def test_run_benchmark_generates_json_file(tmp_path):
    output_file = str(tmp_path / "test_benchmark_results.json")
    report = run_benchmark(seed=42, output_path=output_file, print_report=False)

    assert os.path.exists(output_file)
    assert report.benchmark_hash != ""

    with open(output_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["benchmark_version"] == "v1.0"
    assert data["seed"] == 42
    assert "metrics" in data
    assert "RAVEN" in data["metrics"]
