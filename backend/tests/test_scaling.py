"""Scaling integration tests, designed to execute against actual SimPy."""

import pytest
from pydantic import ValidationError

from cloudwise.config.schemas import ScenarioConfig
from cloudwise.simulation.runner import run_simulation


def scenario(**kw):
    config = dict(name="scaling-test", hosts=1, vms=1, tasks=12, algorithm="FCFS",
                  host_cores=8, vm_pes=1, vm_mips_per_core=1000,
                  arrival_window=0, task_length_mi_min=10000,
                  task_length_mi_max=10000, task_ram_mb_min=512,
                  task_ram_mb_max=512, scaling_enabled=True,
                  scaling_min_vms=1, scaling_max_vms=3,
                  scaling_sample_interval=1, scaling_up_window=1,
                  scaling_down_window=2, scaling_cooldown=0)
    config.update(kw)
    return ScenarioConfig(**config)


def test_scale_out_respects_max_and_placement():
    result = run_simulation(scenario())
    outs = [event for event in result["scalingEvents"] if event["action"] == "SCALE_OUT"]
    assert outs
    assert max(event["newCapacityVms"] for event in outs) <= 3
    assert result["summary"]["completedTasks"] == 12
    assert any(row["assignedVmId"] != "vm-001" for row in result["taskResults"]) is False  # FCFS prefers first eligible
    assert all(row["finishTime"] >= row["startTime"] for row in result["taskResults"])


def test_scale_out_blocked_if_host_full():
    result = run_simulation(scenario(host_cores=1, scaling_max_vms=4))
    assert result["scalingEvents"] == []
    assert result["summary"]["finalActiveVms"] == 1


def test_scaling_disabled_preserves_legacy_contract():
    cfg = scenario(scaling_enabled=False)
    result = run_simulation(cfg)
    assert result["scalingEvents"] == []
    assert "scaleOutEvents" not in result["summary"]


def test_no_tasks_does_not_advance_time():
    result = run_simulation(scenario(tasks=0))
    assert result["summary"]["observationTime"] == 0
    assert result["scalingEvents"] == []


def test_scaling_validation():
    with pytest.raises(ValidationError):
        scenario(scaling_min_vms=2)
    with pytest.raises(ValidationError):
        scenario(scaling_down_threshold=0.9, scaling_up_threshold=0.8)


def test_repeatable_events_and_metrics():
    cfg = scenario(algorithm="AWLB")
    a, b = run_simulation(cfg), run_simulation(cfg)
    assert a == b
    assert len(a["scalingEvents"]) > 0
    assert all(0 <= r["cpuUtilization"] <= 1 + 1e-9 for r in a["vmMetrics"])


def test_scale_in_while_long_task_runs_elsewhere():
    # One long task allocated to VM 1; VM 2 stays idle and may be retired.
    result = run_simulation(scenario(vms=2, tasks=1,
                                    scaling_min_vms=1, scaling_max_vms=2,
                                    scaling_down_window=2, scaling_down_threshold=0.6,
                                    task_length_mi_min=10000, task_length_mi_max=10000))
    assert any(e["action"] == "SCALE_IN" for e in result["scalingEvents"])
    assert result["summary"]["completedTasks"] == 1
    assert result["summary"]["averageCpuUtilization"] <= 1


def test_fixed_capacity_comparison_refuses_scaling():
    from cloudwise.simulation.runner import run_comparison
    with pytest.raises(ValueError, match="separately"):
        run_comparison(scenario())
