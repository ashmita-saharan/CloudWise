"""Repeatable, multi-seed policy experiments and transparent descriptive statistics.

Every policy receives the same generated workload for each (scenario, seed) pair.
Standard deviations describe variation over seeds, not confidence intervals.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from statistics import mean, stdev
from typing import Any, Callable, Mapping, Sequence

from cloudwise.config.schemas import ScenarioConfig

METRICS = (
    "completedTasks", "failedTasks", "averageWaitingTime", "averageExecutionTime",
    "averageTurnaroundTime", "throughput", "averageCpuUtilization",
    "averageRamUtilization", "vmCpuUtilizationStdDev",
)
POLICIES = ("FCFS", "RR", "AWLB")


def summarize_comparisons(comparisons: Sequence[Mapping[str, Any]]) -> dict:
    """Aggregate comparison results, retaining per-seed values for auditability."""
    if not comparisons:
        raise ValueError("At least one comparison is required")
    rows = []
    for comparison in comparisons:
        scenario = comparison["scenario"]
        for policy in POLICIES:
            summary = comparison["results"][policy]["summary"]
            rows.append({"scenario": scenario["name"], "seed": scenario["seed"],
                         "algorithm": policy, **{metric: summary[metric] for metric in METRICS}})
    groups: dict[tuple[str, str], list[dict]] = {}
    for row in rows:
        groups.setdefault((row["scenario"], row["algorithm"]), []).append(row)
    aggregate = []
    for (name, policy), group in sorted(groups.items()):
        entry = {"scenario": name, "algorithm": policy, "runs": len(group)}
        for metric in METRICS:
            values = [r[metric] for r in group]
            entry[metric + "Mean"] = mean(values)
            entry[metric + "StdDev"] = stdev(values) if len(values) > 1 else 0.0
        aggregate.append(entry)
    return {"schemaVersion": "1.0", "seeds": sorted({r["seed"] for r in rows}),
            "metrics": list(METRICS), "runs": rows, "aggregate": aggregate,
            "notes": {
                "variance": "Sample standard deviation across fixed seeds; not a confidence interval.",
                "fairness": "Policies share an identical generated workload within each scenario/seed pair.",
                "throughput": "Completed tasks / elapsed simulated time from t=0 to final event.",
                "utilization": "CPU and RAM utilization are modelled, time-averaged quantities.",
            }}


def run_experiments(scenarios: Sequence[ScenarioConfig], seeds: Sequence[int],
                    comparison_fn: Callable[[ScenarioConfig], dict] | None = None) -> dict:
    """Run the cross-product of scenarios and unique seeds (one comparison per pair)."""
    if not scenarios:
        raise ValueError("At least one scenario is required")
    if not seeds:
        raise ValueError("At least one random seed is required")
    if len(set(seeds)) != len(seeds):
        raise ValueError("Seeds must be unique")
    if len({scenario.name for scenario in scenarios}) != len(scenarios):
        raise ValueError("Scenario names must be unique")
    if comparison_fn is None:
        from cloudwise.simulation.runner import run_comparison
        comparison_fn = run_comparison
    comparisons = [comparison_fn(scenario.model_copy(update={"seed": seed}))
                   for scenario in scenarios for seed in seeds]
    return summarize_comparisons(comparisons)


def _format(value: float) -> str:
    return f"{value:.4f}"


def report_markdown(report: Mapping[str, Any]) -> str:
    """Human-readable report; all values come from actual simulation outputs."""
    lines = ["# CloudWise — Multi-seed Experimental Report", "",
             f"Seeds: {', '.join(str(seed) for seed in report['seeds'])}", "",
             "All times are simulated seconds. Values are mean ± sample standard deviation.", "",
             "| Scenario | Policy | Runs | Completed | Waiting (s) | Turnaround (s) | Throughput (tasks/s) | CPU utilisation | RAM utilisation |",
             "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for r in report["aggregate"]:
        def cell(key: str) -> str:
            return f"{_format(r[key + 'Mean'])} ± {_format(r[key + 'StdDev'])}"
        lines.append("| " + " | ".join([
            r["scenario"].replace("|", "\\|"), r["algorithm"], str(r["runs"]),
            cell("completedTasks"), cell("averageWaitingTime"),
            cell("averageTurnaroundTime"), cell("throughput"),
            cell("averageCpuUtilization"), cell("averageRamUtilization")
        ]) + " |")
    lines += ["", "## Interpretation guidance", "",
              "- All three policies reuse the same workload for each scenario and seed.",
              "- Comparisons are descriptive; no significance test or optimality claim is implied.",
              "- FCFS is defined here as first eligible VM, rather than a global shortest-queue policy.",
              "- AWLB uses a weighted heuristic, not machine learning.",
              "- Utilisation is estimated by the model, not measured from live cloud resources.",
              "- Throughput uses the interval from simulated time 0 to the final event.", ""]
    return "\n".join(lines)


def save_experiment_report(report: Mapping[str, Any], directory: str | Path) -> list[Path]:
    """Write JSON plus machine-readable raw/aggregate CSV and Markdown summary."""
    folder = Path(directory)
    folder.mkdir(parents=True, exist_ok=True)
    paths = [folder / "experiment-report.json", folder / "experiment-runs.csv",
             folder / "experiment-aggregate.csv", folder / "experiment-report.md"]
    paths[0].write_text(json.dumps(report, indent=2), encoding="utf-8")
    for path, field in ((paths[1], "runs"), (paths[2], "aggregate")):
        data = report[field]
        with path.open("w", newline="", encoding="utf-8") as handle:
            if data:
                writer = csv.DictWriter(handle, fieldnames=list(data[0]))
                writer.writeheader()
                writer.writerows(data)
    paths[3].write_text(report_markdown(report), encoding="utf-8")
    return paths
