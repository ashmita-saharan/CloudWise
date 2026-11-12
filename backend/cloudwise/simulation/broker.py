"""Task-to-VM admission, scheduling and queue reservation."""

import simpy

from cloudwise.models.task import CloudTask
from cloudwise.models.vm import VM
from cloudwise.monitoring.allocation_logger import AllocationLogger
from cloudwise.monitoring.metrics import MetricsCollector
from cloudwise.scheduling.base import SchedulingPolicy
from .vm_execution import execute_task


class Broker:
    def __init__(self, env: simpy.Environment, vms: list[VM], policy: SchedulingPolicy,
                 metrics: MetricsCollector, log: AllocationLogger, on_terminal=None) -> None:
        self.env = env
        self.vms = vms
        self.policy = policy
        self.metrics = metrics
        self.log = log
        self.on_terminal = on_terminal

    def dispatch(self, task: CloudTask) -> None:
        vm, scores = self.policy.select_vm(task, self.vms)
        if vm is None:
            task.status = "FAILED"
            task.failure_reason = "No VM satisfies the task's RAM and CPU core requirements"
            self.log.record(self.env.now, self.policy.name, task, None, scores)
            if self.on_terminal is not None:
                self.on_terminal()
            return
        task.status = "QUEUED"
        task.assigned_vm_id = vm.vm_id
        vm.assigned_tasks += 1
        # Reservation occurs immediately so same-time arrivals observe pending work.
        vm.queued_work_mi += task.length_mi
        vm.queued_ram_mb += task.required_ram_mb
        self.log.record(self.env.now, self.policy.name, task, vm, scores)
        self.env.process(execute_task(self.env, vm, task, self.metrics, self.on_terminal))


def task_arrival(env: simpy.Environment, broker: Broker, task: CloudTask):
    yield env.timeout(task.arrival_time)
    broker.dispatch(task)
