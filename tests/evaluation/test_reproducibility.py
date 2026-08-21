"""
Reproducibility Tests for Benchmark Hashing
"""

from ml.evaluation.runner import BenchmarkRunner


def test_reproducibility_same_seed_identical_hash():
    runner_1 = BenchmarkRunner(seed=42)
    report_1 = runner_1.run_benchmark()

    runner_2 = BenchmarkRunner(seed=42)
    report_2 = runner_2.run_benchmark()

    assert report_1.benchmark_hash == report_2.benchmark_hash


def test_reproducibility_different_seed_different_hash():
    runner_1 = BenchmarkRunner(seed=42)
    report_1 = runner_1.run_benchmark()

    runner_2 = BenchmarkRunner(seed=123)
    report_2 = runner_2.run_benchmark()

    assert report_1.benchmark_hash != report_2.benchmark_hash
