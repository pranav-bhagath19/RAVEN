"""
RAVEN Benchmark Reporting Module

Renders console comparison tables and writes human-readable JSON benchmark reports.
"""

import json
import os
from typing import Any
from ml.evaluation.models import BenchmarkReport


def save_json_benchmark_report(report: BenchmarkReport, output_path: str = "data/evaluation/benchmark_results_v1.json") -> str:
    """
    Writes BenchmarkReport model to formatted JSON file.
    Creates parent directories if necessary. Returns absolute output filepath.
    """
    abs_path = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)

    json_content = json.dumps(report.model_dump(), indent=2, sort_keys=True)
    with open(abs_path, "w", encoding="utf-8") as f:
        f.write(json_content)

    return abs_path


def print_console_benchmark_report(report: BenchmarkReport) -> None:
    """
    Prints clean, markdown-style console comparison tables for RAVEN vs baselines.
    """
    print("\n" + "=" * 85)
    print(" RAVEN BENCHMARK REPORT — EVALUATION SUMMARY")
    print("=" * 85)
    print(f"Benchmark Version : {report.benchmark_version}")
    print(f"Dataset Version   : {report.dataset_version}")
    print(f"Random Seed       : {report.seed}")
    print(f"Benchmark SHA-256 : {report.benchmark_hash}")
    print("=" * 85 + "\n")

    # Header
    print(f"{'Metric':<38} | {'RAVEN':<12} | {'Always Retry':<12} | {'Rule-Based':<12}")
    print("-" * 85)

    def format_val(val: Any, is_pct: bool = False, is_int: bool = False) -> str:
        if is_int:
            return f"{int(val):,}"
        if is_pct:
            return f"{float(val):.1f}%"
        if isinstance(val, float):
            return f"{val:.4f}"
        return str(val)

    m = report.metrics
    r_m = m.get("RAVEN")
    ar_m = m.get("Always Retry")
    rb_m = m.get("Rule-Based")

    if r_m and ar_m and rb_m:
        metrics_rows = [
            ("State Reconstruction Accuracy", r_m.state_reconstruction_accuracy, ar_m.state_reconstruction_accuracy, rb_m.state_reconstruction_accuracy, False, False),
            ("Root Cause Accuracy", r_m.root_cause_accuracy, ar_m.root_cause_accuracy, rb_m.root_cause_accuracy, False, False),
            ("Action Selection Accuracy", r_m.action_selection_accuracy, ar_m.action_selection_accuracy, rb_m.action_selection_accuracy, False, False),
            ("Gross Recovery Rate", r_m.recovery_rate, ar_m.recovery_rate, rb_m.recovery_rate, False, False),
            ("Net Recovery Rate (%)", r_m.recovery_net_rate, ar_m.recovery_net_rate, rb_m.recovery_net_rate, True, False),
            ("Total Risk (minor units)", r_m.total_revenue_at_risk_minor, ar_m.total_revenue_at_risk_minor, rb_m.total_revenue_at_risk_minor, False, True),
            ("Total Recovered (minor units)", r_m.total_revenue_recovered_minor, ar_m.total_revenue_recovered_minor, rb_m.total_revenue_recovered_minor, False, True),
            ("Total Action Cost (minor units)", r_m.total_action_cost_minor, ar_m.total_action_cost_minor, rb_m.total_action_cost_minor, False, True),
            ("Policy Violation Rate", r_m.policy_violation_rate, ar_m.policy_violation_rate, rb_m.policy_violation_rate, False, False),
            ("Attribution Precision", r_m.attribution_precision, ar_m.attribution_precision, rb_m.attribution_precision, False, False),
            ("Attribution Recall", r_m.attribution_recall, ar_m.attribution_recall, rb_m.attribution_recall, False, False),
            ("Organic Misattribution Rate", r_m.organic_recovery_misattribution_rate, ar_m.organic_recovery_misattribution_rate, rb_m.organic_recovery_misattribution_rate, False, False),
            ("Avg Decision Latency (ms)", r_m.average_decision_latency_ms, ar_m.average_decision_latency_ms, rb_m.average_decision_latency_ms, False, False),
        ]

        for title, r_v, ar_v, rb_v, is_pct, is_int in metrics_rows:
            r_str = format_val(r_v, is_pct, is_int)
            ar_str = format_val(ar_v, is_pct, is_int)
            rb_str = format_val(rb_v, is_pct, is_int)
            print(f"{title:<38} | {r_str:<12} | {ar_str:<12} | {rb_str:<12}")

    print("-" * 85 + "\n")
