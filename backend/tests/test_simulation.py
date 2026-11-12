"""Behavioural checks for task queues, metrics, policies and reproducibility."""

import pytest
from pydantic import ValidationError

from cloudwise.config.schemas import ScenarioConfig
from cloudwise.simulation.runner import run_comparison, run_simulation


def scenario(**overrides) -> ScenarioConfig:
    values = {
        "name": "test", "hosts": 1, "vms": 1, "tasks": 2,
        "arrival_window": 0, "task_length_mi_min": 1000,
        "task_length_mi_max": 1000, "task_ram_mb_min": 1024,
        "task_ram_mb_max": 1024, "vm_pes": 1,
        "vm_mips_per_core": 1000, "vm_ram_mb": 4096,
    }
    values.update(overrides)
    return ScenarioConfig(**values)


def test_no_tasks_returns_zero_metrics():
    result = run_simulation(scenario(tasks=0))
    assert result["summary"]["completedTasks"] == 0
    assert result["summary"]["throughput"] == 0
    assert result["summary"]["observationTime"] == 0
    assert result["taskResults"] == []


def test_one_vm_executes_sequentially_with_hand_checked_metrics():
    result = run_simulation(scenario(algorithm="FCFS"))
    a, b = result["taskResults"]
    assert [a["startTime"], a["finishTime"]] == [0.0, 1.0]
    assert [b["startTime"], b["finishTime"]] == [1.0, 2.0]
    summary = result["summary"]
    assert summary["completedTasks"] == 2
    assert summary["averageWaitingTime"] == pytest.approx(0.5)
    assert summary["averageExecutionTime"] == pytest.approx(1)
    assert summary["averageTurnaroundTime"] == pytest.approx(1.5)
    assert summary["throughput"] == pytest.approx(1)
    assert summary["averageCpuUtilization"] == pytest.approx(1)
    assert summary["averageRamUtilization"] == pytest.approx(0.25)


def test_fcfs_first_eligible_vm_baseline():
    result = run_simulation(scenario(vms=3, tasks=6, algorithm="FCFS"))
    assert {row["assignedVmId"] for row in result["taskResults"]} == {"vm-001"}


def test_round_robin_cyclic_assignment():
    result = run_simulation(scenario(vms=3, tasks=6, algorithm="RR"))
    assert [row["assignedVmId"] for row in result["taskResults"]] == [
        "vm-001", "vm-002", "vm-003", "vm-001", "vm-002", "vm-003"
    ]


def test_awlb_accounts_pending_work_at_same_timestamp():
    result = run_simulation(scenario(vms=2, tasks=2, algorithm="AWLB", queue_reference_mi=1000))
    assert [row["assignedVmId"] for row in result["taskResults"]] == ["vm-001", "vm-002"]
    assert result["allocationLog"][1]["candidateScores"]["vm-001"] > 0


def test_unplaceable_task_is_failed_not_silently_assigned():
    result = run_simulation(scenario(task_ram_mb_min=8192, task_ram_mb_max=8192))
    assert result["summary"]["completedTasks"] == 0
    assert result["summary"]["failedTasks"] == 2
    assert all(row["status"] == "FAILED" and row["failureReason"]
               for row in result["taskResults"])


def test_fair_comparison_uses_same_tasks_and_reproducible_allocations():
    config = scenario(vms=3, tasks=25, arrival_window=10, task_length_mi_max=2000)
    first = run_comparison(config)
    second = run_comparison(config)
    assert first == second
    common_keys = ("taskId", "arrivalTime", "lengthMi", "requiredRamMb", "requiredPes")
    workloads = [[tuple(row[key] for key in common_keys) for row in run["taskResults"]]
                 for run in first["results"].values()]
    assert workloads[0] == workloads[1] == workloads[2]


def test_rejects_oversubscribed_infrastructure():
    with pytest.raises(ValueError, match="Cannot place"):
        run_simulation(scenario(host_cores=2, vms=3))


def test_invalid_config_rejected():
    with pytest.raises(ValidationError):
        scenario(vm_ram_mb=0)
    with pytest.raises(ValidationError):
        scenario(awlb_cpu_weight=0.8)


def test_failed_task_when_cpu_core_requirement_not_met():
    result = run_simulation(scenario(task_required_pes_max=2, vm_pes=1, tasks=50))
    assert result["summary"]["failedTasks"] > 0


def test_round_robin_skips_ineligible_vm():
    import simpy
    from cloudwise.config.schemas import VMSpec
    from cloudwise.infrastructure.builder import build_datacenter
    from cloudwise.models.task import CloudTask
    from cloudwise.scheduling.round_robin import RoundRobinPolicy

    config = scenario(vms=2, vm_specs=[
        VMSpec(pes=1, mips_per_core=1000, ram_mb=4096),
        VMSpec(pes=3, mips_per_core=1000, ram_mb=4096),
    ])
    vms = sorted(build_datacenter(simpy.Environment(), config).vms, key=lambda vm: vm.vm_id)
    chosen, _ = RoundRobinPolicy().select_vm(
        CloudTask("needs-three-cores", 0, 1000, 1024, required_pes=3), vms
    )
    assert chosen.vm_id == "vm-002"
