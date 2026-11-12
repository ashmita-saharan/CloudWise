"""One task per VM at a time; pending demand is tracked separately from RAM in use."""

import simpy

from cloudwise.models.task import CloudTask
from cloudwise.models.vm import VM
from cloudwise.monitoring.metrics import MetricsCollector


def execute_task(env: simpy.Environment, vm: VM, task: CloudTask, metrics: MetricsCollector, on_terminal=None):
    with vm.cpu_slot.request() as request:
        yield request
        vm.account_until(env.now)
        vm.queued_work_mi -= task.length_mi
        vm.queued_ram_mb -= task.required_ram_mb
        vm.active_task_id = task.task_id
        vm.ram_in_use_mb += task.required_ram_mb
        task.start_time = env.now
        task.status = "RUNNING"
        try:
            yield env.timeout(task.length_mi / vm.total_mips)
        finally:
            vm.account_until(env.now)
            vm.ram_in_use_mb -= task.required_ram_mb
            vm.active_task_id = None
        task.finish_time = env.now
        task.status = "COMPLETED"
        metrics.record_completion(task, vm)
        if on_terminal is not None:
            on_terminal()
