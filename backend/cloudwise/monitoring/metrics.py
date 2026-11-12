"""Task and VM metrics; CPU and RAM utilisation are event-time integrals."""

from dataclasses import dataclass
from statistics import pstdev

from cloudwise.models.task import CloudTask
from cloudwise.models.vm import VM


@dataclass
class MetricsCollector:
    completion_count: int = 0

    def record_completion(self, task: CloudTask, vm: VM) -> None:
        self.completion_count += 1
        vm.completed_tasks += 1


def _average(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def build_metrics(tasks: list[CloudTask], vms: list[VM], end_time: float) -> tuple[dict, list[dict]]:
    for vm in vms:
        vm.account_until(end_time)
    completed = [task for task in tasks if task.status == "COMPLETED"]
    failed = [task for task in tasks if task.status == "FAILED"]
    waits = [(task.start_time - task.arrival_time) for task in completed]
    runtimes = [(task.finish_time - task.start_time) for task in completed]
    turns = [(task.finish_time - task.arrival_time) for task in completed]
    cpu_capacity = sum(vm.total_mips for vm in vms)
    ram_capacity = sum(vm.ram_mb for vm in vms)
    cpu_used = sum(vm.busy_time * vm.total_mips for vm in vms)
    ram_used = sum(vm.ram_mb_seconds for vm in vms)

    vm_metrics = [
        {
            "vmId": vm.vm_id,
            "hostId": vm.host_id,
            "pes": vm.pes,
            "totalMips": vm.total_mips,
            "ramCapacityMb": vm.ram_mb,
            "assignedTasks": vm.assigned_tasks,
            "completedTasks": vm.completed_tasks,
            "cpuUtilization": vm.busy_time / end_time if end_time else 0.0,
            "ramUtilization": vm.ram_mb_seconds / (vm.ram_mb * end_time) if end_time else 0.0,
            "busyTime": vm.busy_time,
        }
        for vm in vms
    ]
    summary = {
        "completedTasks": len(completed),
        "failedTasks": len(failed),
        "averageWaitingTime": _average(waits),
        "averageExecutionTime": _average(runtimes),
        "averageTurnaroundTime": _average(turns),
        "averageResponseTime": _average(waits),
        "throughput": len(completed) / end_time if end_time else 0.0,
        "averageCpuUtilization": cpu_used / (cpu_capacity * end_time) if end_time else 0.0,
        "averageRamUtilization": ram_used / (ram_capacity * end_time) if end_time else 0.0,
        "vmCpuUtilizationStdDev": pstdev([row["cpuUtilization"] for row in vm_metrics]) if vm_metrics else 0.0,
        "observationTime": end_time,
    }
    return summary, vm_metrics
