"""
Phase 15 Automated Certification Tests
"""

import scripts.phase15_certification as cert_module
import scripts.phase15_benchmark as bench_module


def test_phase15_certification_harness():
    """Runs the 15-scenario certification harness as a pytest test case."""
    cert_module.run_certification()


def test_phase15_benchmark_harness():
    """Runs the performance benchmark harness as a pytest test case."""
    bench_module.run_benchmark()
