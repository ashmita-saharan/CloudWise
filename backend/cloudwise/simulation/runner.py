"""API-independent entry points for one run or a fair policy comparison."""

import re
from dataclasses import replace
from typing import Any, Mapping, Sequence

import simpy

from cloudwise.config.schemas import ScenarioConfig
from cloudwise.infrastructure.builder import build_datacenter
from cloudwise.models.task import CloudTask
from cloudwise.monitoring.allocation_logger import AllocationLogger
from cloudwise.monitoring.metrics import MetricsCollector, build_metrics
from cloudwise.scheduling.awlb import AWLBPolicy
from cloudwise.scheduling.fcfs import FCFSPolicy
from cloudwise.scheduling.round_robin import RoundRobinPolicy
from cloudwise.simulation.broker import Broker, task_arrival
from cloudwise.workload.generator import generate_workload


POLICIES = ("FCFS", "RR", "AWLB")


def _parse_config(config: ScenarioConfig | Mapping[str, Any]) -> ScenarioConfig:
    return config if isinstance(config, ScenarioConfig) else ScenarioConfig.model_validate(config)


def _build_policy(config: ScenarioConfig):
    if config.algorithm == "FCFS":
        return FCFSPolicy()
    if config.algorithm == "RR":
        return RoundRobinPolicy()
    return AWLBPolicy(config)


def _task_row(task: CloudTask) -> dict:
    complete = task.status == "COMPLETED"
    return {
        "taskId": task.task_id,
        "arrivalTime": task.arrival_time,
        "lengthMi": task.length_mi,
        "requiredRamMb": task.required_ram_mb,
        "requiredPes": task.required_pes,
        "status": task.status,
        "assignedVmId": task.assigned_vm_id,
        "startTime": task.start_time,
        "finishTime": task.finish_time,
        "waitingTime": task.start_time - task.arrival_time if complete else None,
        "executionTime": task.finish_time - task.start_time if complete else None,
        "turnaroundTime": task.finish_time - task.arrival_time if complete else None,
        "failureReason": task.failure_reason,
    }


def run_simulation(config: ScenarioConfig | Mapping[str, Any],
                   workload: Sequence[CloudTask] | None = None) -> dict:
    config = _parse_config(config)
    if workload is not None and len(workload) != config.tasks:
        raise ValueError("Provided workload size must match config.tasks")
    # Do not mutate a workload shared with other policy runs.
    tasks = [replace(task, status="PENDING", assigned_vm_id=None,
                     start_time=None, finish_time=None, failure_reason=None)
             for task in (workload if workload is not None else generate_workload(config))]
    tasks.sort(key=lambda task: (task.arrival_time, task.task_id))
    env = simpy.Environment()
    datacenter = build_datacenter(env, config)
    vms = sorted(datacenter.vms, key=lambda vm: vm.vm_id)
    metrics = MetricsCollector()
    logger = AllocationLogger()
    broker = Broker(env, vms, _build_policy(config), metrics, logger)
    for task in tasks:
        env.process(task_arrival(env, broker, task))
    env.run()
    summary, vm_metrics = build_metrics(tasks, vms, env.now)
    slug = re.sub(r"[^a-z0-9]+", "-", config.name.lower()).strip("-") or "scenario"
    return {
        "schemaVersion": "1.0",
        "runId": f"{slug}-{config.algorithm.lower()}-seed-{config.seed}",
        "algorithm": config.algorithm,
        "scenario": config.model_dump(mode="json"),
        "summary": summary,
        "vmMetrics": vm_metrics,
        "taskResults": [_task_row(task) for task in tasks],
        "allocationLog": logger.records,
    }


def run_comparison(config: ScenarioConfig | Mapping[str, Any]) -> dict:
    config = _parse_config(config)
    base_workload = generate_workload(config)
    return {
        "schemaVersion": "1.0",
        "scenario": config.model_dump(mode="json"),
        "results": {
            policy: run_simulation(config.model_copy(update={"algorithm": policy}), workload=base_workload)
            for policy in POLICIES
        },
    }
