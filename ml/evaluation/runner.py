"""
RAVEN Benchmark Runner Module

Executes evaluation strategies against synthetic datasets, calculates metrics,
and produces deterministic BenchmarkReport objects.
"""

from agents.common.provider import MockLLMProvider
from domain.entities.financial_event import FinancialEvent
from ml.evaluation.baselines import AlwaysRetryStrategy, RuleBasedStrategy
from ml.evaluation.metrics import calculate_metrics_for_results
from ml.evaluation.models import (
    BenchmarkMetrics,
    BenchmarkReport,
    EvaluationCase,
    EvaluationResult,
)
from ml.evaluation.reproducibility import compute_canonical_benchmark_hash
from ml.evaluation.strategies import (
    EvaluationStrategy,
    RavenAdaptiveIntelligenceStrategy,
    RavenMLPropensityStrategy,
    RavenStrategy,
)
from simulator.generator import SyntheticDataGenerator


class BenchmarkRunner:
    """
    Evaluation Harness executing strategies across multi-scenario financial streams.
    """

    def __init__(
        self,
        seed: int = 42,
        strategies: list[EvaluationStrategy] | None = None,
        provider: MockLLMProvider | None = None,
    ) -> None:
        self.seed = seed
        self.provider = provider or MockLLMProvider()
        self.strategies = strategies or [
            AlwaysRetryStrategy(),
            RuleBasedStrategy(),
            RavenStrategy(provider=self.provider),
            RavenMLPropensityStrategy(provider=self.provider, seed=seed),
            RavenAdaptiveIntelligenceStrategy(provider=self.provider, seed=seed),
        ]

    def build_evaluation_cases(self) -> tuple[list[EvaluationCase], dict[str, EvaluationCase]]:
        """
        Generates synthetic scenario suite deterministically using configured seed.
        Converts scenario results into isolated EvaluationCase objects.
        """
        generator = SyntheticDataGenerator(seed=self.seed)
        scenario_results = generator.generate_all_scenarios()

        cases: list[EvaluationCase] = []
        cases_by_id: dict[str, EvaluationCase] = {}

        for idx, s_res in enumerate(scenario_results):
            gt = s_res.ground_truth
            case_id = f"case_{idx + 1:03d}_{s_res.scenario_id}"

            parsed_events: list[FinancialEvent] = []
            for raw_evt in s_res.events:
                if isinstance(raw_evt, FinancialEvent):
                    parsed_events.append(raw_evt)
                elif isinstance(raw_evt, dict):
                    parsed_events.append(FinancialEvent.model_validate(raw_evt))

            first_evt = parsed_events[0] if parsed_events else None
            amount_minor = first_evt.amount.amount_minor if first_evt and first_evt.amount else 100000
            currency = first_evt.currency if first_evt else "INR"

            case = EvaluationCase(
                case_id=case_id,
                scenario_id=s_res.scenario_id,
                payment_id=gt.payment_id,
                amount_minor=amount_minor,
                currency=currency,
                ground_truth_root_cause=gt.true_root_cause,
                ground_truth_recoverable=gt.is_recoverable,
                ground_truth_organic_recovery=gt.organic_recovery_will_occur,
                ground_truth_optimal_action=gt.optimal_action,
                ground_truth_optimal_delay_seconds=gt.expected_optimal_delay_seconds,
                events=parsed_events,
            )
            cases.append(case)
            cases_by_id[case_id] = case

        return cases, cases_by_id

    def run_benchmark(self) -> BenchmarkReport:
        """
        Executes benchmark suite across all strategies and evaluation cases.
        Calculates aggregate and per-scenario metrics, then seals report with SHA-256 hash.
        """
        cases, cases_by_id = self.build_evaluation_cases()

        raw_results: list[EvaluationResult] = []
        results_by_strategy: dict[str, list[EvaluationResult]] = {s.name: [] for s in self.strategies}
        results_by_scenario_strategy: dict[str, dict[str, list[EvaluationResult]]] = {}

        for case in cases:
            if case.scenario_id not in results_by_scenario_strategy:
                results_by_scenario_strategy[case.scenario_id] = {s.name: [] for s in self.strategies}

            for strategy in self.strategies:
                decision = strategy.evaluate(case)

                # Ground Truth Comparison
                rc_pred = decision.root_cause_prediction
                rc_correct = (rc_pred == case.ground_truth_root_cause) if rc_pred is not None else None
                act_correct = (decision.action_type == case.ground_truth_optimal_action)

                is_recovered = False
                recovered_amount = 0
                if decision.recovery_attributed and case.ground_truth_recoverable:
                    is_recovered = True
                    recovered_amount = case.amount_minor

                net_rec = recovered_amount - decision.execution_cost_minor

                res = EvaluationResult(
                    case_id=case.case_id,
                    scenario_id=case.scenario_id,
                    strategy_name=strategy.name,
                    decision=decision.decision,
                    root_cause_prediction=rc_pred,
                    root_cause_correct=rc_correct,
                    selected_action=decision.action_type,
                    optimal_action=case.ground_truth_optimal_action,
                    action_correct=act_correct,
                    recovered=is_recovered,
                    recovery_attributed=decision.recovery_attributed,
                    recovered_amount_minor=recovered_amount,
                    action_cost_minor=decision.execution_cost_minor,
                    net_recovered_minor=net_rec,
                    policy_violation=decision.policy_violation,
                    decision_latency_ms=decision.latency_ms,
                )

                raw_results.append(res)
                results_by_strategy[strategy.name].append(res)
                results_by_scenario_strategy[case.scenario_id][strategy.name].append(res)

        # Calculate Aggregate Metrics per Strategy
        aggregate_metrics: dict[str, BenchmarkMetrics] = {}
        for strategy in self.strategies:
            strat_results = results_by_strategy[strategy.name]
            aggregate_metrics[strategy.name] = calculate_metrics_for_results(strat_results, cases_by_id)

        # Calculate Per-Scenario Metrics
        per_scenario_metrics: dict[str, dict[str, BenchmarkMetrics]] = {}
        for scen_id, strat_map in results_by_scenario_strategy.items():
            per_scenario_metrics[scen_id] = {}
            for strat_name, scen_strat_results in strat_map.items():
                per_scenario_metrics[scen_id][strat_name] = calculate_metrics_for_results(scen_strat_results, cases_by_id)

        # Assemble Unsealed Report
        unsealed_report = BenchmarkReport(
            benchmark_version="v1.0",
            dataset_version="v1.0",
            seed=self.seed,
            benchmark_hash="",
            strategies=[s.name for s in self.strategies],
            metrics=aggregate_metrics,
            per_scenario_metrics=per_scenario_metrics,
            raw_results=raw_results,
        )

        # Compute deterministic benchmark hash
        benchmark_hash = compute_canonical_benchmark_hash(unsealed_report)

        # Seal report with hash
        sealed_report = unsealed_report.model_copy(update={"benchmark_hash": benchmark_hash})
        return sealed_report
