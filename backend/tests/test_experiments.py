"""These aggregation tests run without SimPy; integration coverage uses real SimPy."""
import csv
import json

import pytest

from cloudwise.config.schemas import ScenarioConfig
from cloudwise.experiments import METRICS, run_experiments, save_experiment_report, summarize_comparisons


def fake_comparison(config):
    results = {}
    for i, policy in enumerate(("FCFS", "RR", "AWLB")):
        summary = {key: float(config.seed + i) for key in METRICS}
        results[policy] = {"summary": summary}
    return {"scenario": config.model_dump(), "results": results}


def test_cross_product_and_statistics():
    report = run_experiments([ScenarioConfig(name="tiny", tasks=0)], [2, 4], fake_comparison)
    assert len(report["runs"]) == 6
    fcfs = next(r for r in report["aggregate"] if r["algorithm"] == "FCFS")
    assert fcfs["throughputMean"] == 3
    assert fcfs["throughputStdDev"] == pytest.approx(2 ** 0.5)
    assert fcfs["runs"] == 2


def test_rejects_duplicate_seeds_and_scenario_names():
    sc = ScenarioConfig(name="duplicate")
    with pytest.raises(ValueError, match="unique"):
        run_experiments([sc], [7, 7], fake_comparison)
    with pytest.raises(ValueError, match="unique"):
        run_experiments([sc, sc], [7], fake_comparison)
    with pytest.raises(ValueError, match="At least one"):
        summarize_comparisons([])


def test_writes_four_valid_artifacts(tmp_path):
    report = run_experiments([ScenarioConfig(name="tiny")], [42], fake_comparison)
    paths = save_experiment_report(report, tmp_path)
    assert len(paths) == 4
    assert json.loads(paths[0].read_text())["seeds"] == [42]
    with paths[1].open(newline="") as handle:
        assert len(list(csv.DictReader(handle))) == 3
    assert "AWLB" in paths[3].read_text()
