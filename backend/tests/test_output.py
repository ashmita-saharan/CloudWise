"""Result files remain machine-readable even for an empty workload."""

import csv
import json

from cloudwise.output.result_writer import save_comparison, save_run
from cloudwise.simulation.runner import run_comparison, run_simulation


def test_empty_run_exports_csv_headers(tmp_path):
    result = run_simulation({"name": "empty", "hosts": 1, "vms": 1, "tasks": 0})
    output_paths = save_run(result, tmp_path)
    assert len(output_paths) == 3
    assert json.loads(output_paths[0].read_text())["summary"]["completedTasks"] == 0
    with output_paths[1].open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        assert "taskId" in reader.fieldnames
        assert list(reader) == []


def test_comparison_export_name_includes_seed(tmp_path):
    comparison = run_comparison({"name": "sample", "hosts": 1, "vms": 1, "tasks": 0, "seed": 9})
    path = save_comparison(comparison, tmp_path)
    assert path.name == "sample-comparison-seed-9.json"
    assert set(json.loads(path.read_text())["results"]) == {"FCFS", "RR", "AWLB"}
