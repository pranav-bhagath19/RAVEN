"""
RAVEN Benchmark Executable CLI Module

Runs evaluation runner across strategies, displays comparison report,
and writes benchmark_results_v1.json.
"""

import argparse
from ml.evaluation.models import BenchmarkReport
from ml.evaluation.reporting import print_console_benchmark_report, save_json_benchmark_report
from ml.evaluation.runner import BenchmarkRunner


def run_benchmark(
    seed: int = 42,
    output_path: str = "data/evaluation/benchmark_results_v1.json",
    print_report: bool = True,
) -> BenchmarkReport:
    """
    Executes benchmark runner for given seed, prints summary table, and writes JSON report.
    """
    runner = BenchmarkRunner(seed=seed)
    report = runner.run_benchmark()

    if print_report:
        print_console_benchmark_report(report)

    saved_path = save_json_benchmark_report(report, output_path=output_path)
    if print_report:
        print(f"Benchmark results successfully written to: {saved_path}")

    return report


def main() -> None:
    """CLI entry point for python -m ml.evaluation.benchmark"""
    parser = argparse.ArgumentParser(description="RAVEN Benchmark Suite Runner")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for synthetic dataset generation (default: 42)")
    parser.add_argument("--output", type=str, default="data/evaluation/benchmark_results_v1.json", help="Output JSON path")
    parser.add_argument("--quiet", action="store_true", help="Suppress console table printing")

    args = parser.parse_args()

    run_benchmark(
        seed=args.seed,
        output_path=args.output,
        print_report=not args.quiet,
    )


if __name__ == "__main__":
    main()
