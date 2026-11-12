"""Stable JSON and CSV exports; no output written unless explicitly requested."""

import csv
import json
import re
from pathlib import Path

TASK_COLUMNS = (
    "taskId", "arrivalTime", "lengthMi", "requiredRamMb", "requiredPes",
    "status", "assignedVmId", "startTime", "finishTime", "waitingTime",
    "executionTime", "turnaroundTime", "failureReason",
)
ALLOCATION_COLUMNS = ("time", "taskId", "policy", "chosenVmId", "candidateScores", "reason")


def save_run(result: dict, output_dir: str | Path) -> list[Path]:
    folder = Path(output_dir)
    folder.mkdir(parents=True, exist_ok=True)
    prefix = result["runId"]
    json_path = folder / f"{prefix}.json"
    json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    paths = [json_path]
    for field, suffix, columns in (
        ("taskResults", "tasks", TASK_COLUMNS),
        ("allocationLog", "allocations", ALLOCATION_COLUMNS),
    ):
        rows = result[field]
        csv_path = folder / f"{prefix}-{suffix}.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns)
            writer.writeheader()
            for row in rows:
                writer.writerow({key: json.dumps(value) if isinstance(value, dict) else value
                                 for key, value in row.items()})
        paths.append(csv_path)
    if result.get("scalingEvents"):
        scaling_path = folder / f"{prefix}-scaling-events.csv"
        with scaling_path.open("w", newline="", encoding="utf-8") as handle:
            events = result["scalingEvents"]
            writer = csv.DictWriter(handle, fieldnames=list(events[0]))
            writer.writeheader()
            writer.writerows(events)
        paths.append(scaling_path)
    return paths


def save_comparison(comparison: dict, output_dir: str | Path) -> Path:
    folder = Path(output_dir)
    folder.mkdir(parents=True, exist_ok=True)
    scenario = comparison["scenario"]
    slug = re.sub(r"[^a-z0-9]+", "-", scenario["name"].lower()).strip("-") or "scenario"
    path = folder / f"{slug}-comparison-seed-{scenario['seed']}.json"
    path.write_text(json.dumps(comparison, indent=2, ensure_ascii=False), encoding="utf-8")
    return path
